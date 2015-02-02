# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from datetime import datetime
from dateutil.rrule import rrule, SECONDLY, MINUTELY, HOURLY, DAILY, WEEKLY, \
    MONTHLY, YEARLY
from itertools import groupby, chain
from sql.aggregate import Max

from trytond.config import config
from trytond.model import Workflow, ModelSQL, ModelView, Model, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.tools import reduce_ids
from trytond.wizard import Wizard, StateView, StateAction, Button
DIGITS = config.getint('digits', 'unit_price_digits', 4)

__all__ = ['ContractService', 'Contract', 'ContractLine',
    'ContractConsumption', 'CreateConsumptionsStart', 'CreateConsumptions']


class RRuleMixin(Model):
    _rec_name = 'freq'
    freq = fields.Selection([
        ('secondly', 'Secondly'),
        ('minutely', 'Minutely'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ], 'Frequency', required=True)
    until_date = fields.Boolean('Is Date',
        help='Ignore time of field "Until Date", but handle as date only.')
    until = fields.DateTime('Until Date')
    count = fields.Integer('Count')
    interval = fields.Integer('Interval')
    bysecond = fields.Char('By Second')
    byminute = fields.Char('By Minute')
    byhour = fields.Char('By Hour')
    byday = fields.Char('By Day')
    bymonthday = fields.Char('By Month Day')
    byyearday = fields.Char('By Year Day')
    byweekno = fields.Char('By Week Number')
    bymonth = fields.Char('By Month')
    bysetpos = fields.Char('By Position')
    wkst = fields.Selection([
        (None, ''),
        ('su', 'Sunday'),
        ('mo', 'Monday'),
        ('tu', 'Tuesday'),
        ('we', 'Wednesday'),
        ('th', 'Thursday'),
        ('fr', 'Friday'),
        ('sa', 'Saturday'),
        ], 'Week Day', sort=False)

    @classmethod
    def __setup__(cls):
        super(RRuleMixin, cls).__setup__()
        cls._sql_constraints += [
            ('until_count_only_one',
                'CHECK(until IS NULL OR count IS NULL OR count = 0)',
                'Only one of "until" and "count" can be set.'),
            ]
        cls._error_messages.update({
                'invalid_bysecond': ('Invalid "By Second" in recurrence rule '
                    '"%s"'),
                'invalid_byminute': ('Invalid "By Minute" in recurrence rule '
                    '"%s"'),
                'invalid_byhour': 'Invalid "By Hour" in recurrence rule "%s"',
                'invalid_byday': 'Invalid "By Day" in recurrence rule "%s"',
                'invalid_bymonthday': ('Invalid "By Month Day" in recurrence '
                    'rule "%s"'),
                'invalid_byyearday': ('Invalid "By Year Day" in recurrence '
                    'rule "%s"'),
                'invalid_byweekno': ('Invalid "By Week Number" in recurrence '
                    'rule "%s"'),
                'invalid_bymonth': (
                    'Invalid "By Month" in recurrence rule "%s"'),
                'invalid_bysetpos': (
                    'Invalid "By Position" in recurrence rule "%s"'),
                })

    @classmethod
    def validate(cls, rules):
        super(RRuleMixin, cls).validate(rules)
        for rule in rules:
            rule.check_bysecond()
            rule.check_byminute()
            rule.check_byhour()
            rule.check_byday()
            rule.check_bymonthday()
            rule.check_byyearday()
            rule.check_byweekno()
            rule.check_bymonth()
            rule.check_bysetpos()

    def check_bysecond(self):
        if self.bysecond:
            for second in self.bysecond.split(','):
                try:
                    second = int(second)
                except Exception:
                    second = -1
                if not (second >= 0 and second <= 59):
                    self.raise_user_error('invalid_bysecond', (self.rec_name,))

    def check_byminute(self):
        if self.byminute:
            for minute in self.byminute.split(','):
                try:
                    minute = int(minute)
                except Exception:
                    minute = -1
                if not (minute >= 0 and minute <= 59):
                    self.raise_user_error('invalid_byminute', (self.rec_name,))

    def check_byhour(self):
        if self.byhour:
            for hour in self.byhour.split(','):
                try:
                    hour = int(hour)
                except Exception:
                    hour = -1
                if not (hour >= 0 and hour <= 23):
                    self.raise_user_error('invalid_byhour', (self.rec_name,))

    def check_byday(self):
        if self.byday:
            for weekdaynum in self.byday.split(','):
                weekday = weekdaynum[-2:]
                if weekday not in ('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'):
                    self.raise_user_error('invalid_byday', (self.rec_name,))
                ordwk = weekday[:-2]
                if not ordwk:
                    continue
                try:
                    ordwk = int(ordwk)
                except Exception:
                    ordwk = -1
                if not (abs(ordwk) >= 1 and abs(ordwk) <= 53):
                    self.raise_user_error('invalid_byday', (self.rec_name,))

    def check_bymonthday(self):
        if self.bymonthday:
            for monthdaynum in self.bymonthday.split(','):
                try:
                    monthdaynum = int(monthdaynum)
                except Exception:
                    monthdaynum = -100
                if not (abs(monthdaynum) >= 1 and abs(monthdaynum) <= 31):
                    self.raise_user_error('invalid_bymonthday', (
                            self.rec_name,))

    def check_byyearday(self):
        if self.byyearday:
            for yeardaynum in self.byyearday.split(','):
                try:
                    yeardaynum = int(yeardaynum)
                except Exception:
                    yeardaynum = -1000
                if not (abs(yeardaynum) >= 1 and abs(yeardaynum) <= 366):
                    self.raise_user_error('invalid_byyearday',
                        (self.rec_name,))

    def check_byweekno(self):
        if self.byweekno:
            for weeknum in self.byweekno.split(','):
                try:
                    weeknum = int(weeknum)
                except Exception:
                    weeknum = -100
                if not (abs(weeknum) >= 1 and abs(weeknum) <= 53):
                    self.raise_user_error('invalid_byweekno', (self.rec_name,))

    def check_bymonth(self):
        if self.bymonth:
            for monthnum in self.bymonth.split(','):
                try:
                    monthnum = int(monthnum)
                except Exception:
                    monthnum = -1
                if not (monthnum >= 1 and monthnum <= 12):
                    self.raise_user_error('invalid_bymonth', (self.rec_name,))

    def check_bysetpos(self):
        if self.bysetpos:
            for setposday in self.bysetpos.split(','):
                try:
                    setposday = int(setposday)
                except Exception:
                    setposday = -1000
                if not (abs(setposday) >= 1 and abs(setposday) <= 366):
                    self.raise_user_error('invalid_bysetpos', (self.rec_name,))

    def _rule2update(self):
        res = {}
        for field in ('freq', 'until_date', 'until', 'count', 'interval',
                'bysecond', 'byminute', 'byhour', 'byday', 'bymonthday',
                'byyearday', 'byweekno', 'bymonth', 'bysetpos', 'wkst'):
            res[field] = getattr(self, field)
        return res

    def rrule_values(self):
        values = {}
        mappings = {
            'freq': {
                'secondly': SECONDLY,
                'minutely': MINUTELY,
                'hourly': HOURLY,
                'daily': DAILY,
                'weekly': WEEKLY,
                'monthly': MONTHLY,
                'yearly': YEARLY,
                },
            'byday': 'bymonthday',
            }
        for field in ('freq', 'until_date', 'until', 'count', 'interval',
                'bysecond', 'byminute', 'byhour', 'byday', 'bymonthday',
                'byyearday', 'byweekno', 'bymonth', 'bysetpos', 'wkst'):
            value = getattr(self, field)
            if not value:
                continue
            if field in mappings:
                if isinstance(mappings[field], str):
                    values[mappings[fields]] = value
                else:
                    value = mappings[field][value]
            values[field] = value
        return values

    @property
    def rrule(self):
        'Returns rrule instance from current values'
        return rrule(**self.rrule_values())


class ContractService(RRuleMixin, ModelSQL, ModelView):
    'Contract Service'
    __name__ = 'contract.service'

    product = fields.Many2One('product.product', 'Product', required=True,
        domain=[
            ('type', '=', 'service'),
            ])

    def get_rec_name(self, name):
        name = super(ContractService, self).get_rec_name(name)
        return '%s (%s)' % (self.product.rec_name, name)

_STATES = {
    'readonly': Eval('state') != 'draft',
    }
_DEPENDS = ['state']


class Contract(RRuleMixin, Workflow, ModelSQL, ModelView):
    'Contract'
    __name__ = 'contract'

    company = fields.Many2One('company.company', 'Company', required=True,
        states=_STATES, depends=_DEPENDS)
    currency = fields.Many2One('currency.currency', 'Currency', required=True,
        states=_STATES, depends=_DEPENDS)
    party = fields.Many2One('party.party', 'Party', required=True,
        states=_STATES, depends=_DEPENDS)
    reference = fields.Char('Reference', readonly=True, select=True)
    start_date = fields.DateTime('Start Date', required=True,
        states=_STATES, depends=_DEPENDS)
    end_date = fields.DateTime('End Date')
    first_invoice_date = fields.Date('First Invoice Date', states=_STATES,
        depends=_DEPENDS)
    lines = fields.One2Many('contract.line', 'contract', 'Lines',
        context={
            'start_date': Eval('start_date'),
            'end_date': Eval('end_date'),
            },
        depends=['start_date', 'end_date'])
    state = fields.Selection([
            ('draft', 'Draft'),
            ('validated', 'Validated'),
            ('cancel', 'Cancel'),
            ], 'State', required=True, readonly=True)

    @classmethod
    def __setup__(cls):
        super(Contract, cls).__setup__()
        for field_name in ('freq', 'until_date', 'until', 'count', 'interval',
                'bysecond', 'byminute', 'byhour', 'byday', 'bymonthday',
                'byyearday', 'byweekno', 'bymonth', 'bysetpos', 'wkst'):
            field = getattr(cls, field_name)
            field.states = _STATES
            field.depends = _DEPENDS
        cls._transitions |= set((
                ('draft', 'validated'),
                ('validated', 'cancel'),
                ('draft', 'cancel'),
                ('cancel', 'draft'),
                ))
        cls._buttons.update({
                'draft': {
                    'invisible': Eval('state') != 'cancel',
                    'icon': 'tryton-clear',
                    },
                'validate_contract': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-go-next',
                    },
                'cancel': {
                    'invisible': Eval('state') == 'cancel',
                    'icon': 'tryton-cancel',
                    },
                })

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_currency():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.id

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def set_reference(cls, contracts):
        'Fill the reference field with the contract sequence'
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('contract.configuration')

        config = Config(1)
        to_write = []
        for contract in contracts:
            if contract.reference:
                continue
            reference = Sequence.get_id(config.contract_sequence.id)
            to_write.extend(([contract], {
                        'reference': reference,
                        }))
        if to_write:
            cls.write(*to_write)

    @classmethod
    def copy(cls, contracts, default=None):
        if default is None:
            default = {}
        default.setdefault('reference', None)
        default.setdefault('end_date', None)
        return super(Contract, cls).copy(contracts, default=default)

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, contracts):
        pool = Pool()
        ContractLine = pool.get('contract.line')
        ContractLine.hold([l for c in contracts for l in c.lines])

    @classmethod
    @ModelView.button
    @Workflow.transition('validated')
    def validate_contract(cls, contracts):
        pool = Pool()
        ContractLine = pool.get('contract.line')
        cls.set_reference(contracts)
        ContractLine.active([l for c in contracts for l in c.lines])

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, contracts):
        pass

    def rrule_values(self):
        values = super(Contract, self).rrule_values()
        values['dtstart'] = self.start_date
        return values

    def get_consumptions(self, end_date=None):
        pool = Pool()
        Date = pool.get('ir.date')

        if end_date is None:
            end_date = datetime.combine(Date.today(), datetime.max.time())

        consumptions = []
        for line in self.lines:
            if line.state != 'active':
                continue
            start_date = (line.last_consumption_date or line.start_date or
                line.contract.start_date)
            for date in self.rrule.between(start_date, end_date):
                consumptions.append(line.get_consumption(start_date, date))
                start_date = date
        return consumptions

    @classmethod
    def consume(cls, contracts, date=None):
        'Consume the contracts until date'
        pool = Pool()
        ContractConsumption = pool.get('contract.consumption')

        to_create = []
        for contract in contracts:
            to_create += contract.get_consumptions(date)
        return ContractConsumption.create([c._save_values for c in to_create])


class ContractLine(Workflow, ModelSQL, ModelView):
    'Contract Line'
    __name__ = 'contract.line'

    contract = fields.Many2One('contract', 'Contract', required=True,
        ondelete='CASCADE')
    service = fields.Many2One('contract.service', 'Service')
    name = fields.Char('Name')
    description = fields.Text('Description', required=True)
    unit_price = fields.Numeric('Unit Price', digits=(16, DIGITS),
        required=True)
    start_date = fields.DateTime('Start Date', required=True)
    end_date = fields.DateTime('End Date')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('hold', 'Hold'),
            ], 'State', required=True, readonly=True)
    last_consumption_date = fields.Function(fields.Date(
            'Last Consumption Date'), 'get_last_consumption_date')

    @classmethod
    def __setup__(cls):
        super(ContractLine, cls).__setup__()
        for attr in dir(RRuleMixin):
            if not hasattr(cls, attr):
                continue
            if isinstance(getattr(cls, attr), fields.Field):
                field = getattr(cls, attr)
                field.states = _STATES
                field.depends = _DEPENDS

        cls._transitions |= set((
                ('draft', 'active'),
                ('active', 'hold'),
                ('hold', 'active'),
                ))
        cls._buttons.update({
                'active': {
                    'invisible': Eval('state') == 'active',
                    'icon': 'tryton-go-next',
                    },
                'hold': {
                    'invisible': Eval('state') != 'hold',
                    'icon': 'tryton-go-previous',
                    },
                })
        cls._error_messages.update({
                'line_outside_contract': ('Line "%(line)s" is outside its '
                    'contract "%(contract)s" period')
                })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_start_date():
        return Transaction().context.get('start_date')

    @staticmethod
    def default_end_date():
        return Transaction().context.get('end_date')

    @fields.depends('service', 'unit_price', 'description')
    def on_change_service(self):
        changes = {
            'unit_price': None,
            }
        if self.service:
            changes['name'] = self.service.rec_name
            if not self.unit_price:
                changes['unit_price'] = self.service.product.list_price
            if not self.description:
                changes['description'] = self.service.product.rec_name
        return changes

    @property
    def rrule(self):
        if not self.service:
            return
        values = self.service.rrule_values()
        values['dtstart'] = self.start_date
        return rrule(**values)

    @classmethod
    def get_last_consumption_date(cls, lines, name):
        pool = Pool()
        Consumption = pool.get('contract.consumption')
        table = Consumption.__table__()
        cursor = Transaction().cursor

        line_ids = [l.id for l in lines]
        values = dict.fromkeys(line_ids, None)
        cursor.execute(*table.select(table.contract_line, Max(table.end_date),
                where=reduce_ids(table.contract_line, line_ids),
                group_by=table.contract_line))
        values.update(dict(cursor.fetchall()))
        return values

    @classmethod
    def validate(cls, lines):
        super(ContractLine, cls).validate(lines)
        for line in lines:
            line.check_contract_period()

    def check_contract_period(self):
        if self.start_date < self.contract.start_date:
            self.raise_user_error('line_outside_contract', {
                    'line': self.rec_name,
                    'contract': self.contract.rec_name,
                    })
        if (self.contract.end_date and
                self.end_date > self.contract.end_date):
            self.raise_user_error('line_outside_contract', {
                    'line': self.rec_name,
                    'contract': self.contract.rec_name,
                    })

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, lines):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('active')
    def active(cls, lines):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('hold')
    def hold(cls, lines):
        pass

    def get_consumption(self, start_date, end_date):
        'Returns the consumption for date date'
        pool = Pool()
        Consumption = pool.get('contract.consumption')
        consumption = Consumption()
        consumption.contract_line = self
        consumption.start_date = start_date
        consumption.end_date = end_date
        invoice_date = end_date.date()
        if self.contract.first_invoice_date:
            invoice_date += (self.contract.first_invoice_date -
                self.contract.start_date.date())
        consumption.invoice_date = invoice_date
        return consumption


class ContractConsumption(ModelSQL, ModelView):
    'Contract Consumption'
    __name__ = 'contract.consumption'

    contract_line = fields.Many2One('contract.line', 'Contract Line',
        required=True)
    invoice_line = fields.Many2One('account.invoice.line', 'Invoice Line')
    start_date = fields.DateTime('Start Date')
    end_date = fields.DateTime('End Date')
    invoice_date = fields.Date('Invoice Date')

    @classmethod
    def __setup__(cls):
        super(ContractConsumption, cls).__setup__()
        cls._error_messages.update({
                'missing_account_revenue': ('Product "%(product)s" of '
                    'contract line %(contract_line)s misses a revenue '
                    'account.'),
                'missing_account_revenue_property': ('Contract Line '
                    '"%(contract_line)s" misses an "account revenue" default '
                    'property.'),
                })
        cls._buttons.update({
                'invoice': {
                    'invisible': Bool(Eval('invoice_line')),
                    'icon': 'tryton-go-next',
                    },
                })

    def _get_tax_rule_pattern(self):
        '''
        Get tax rule pattern
        '''
        return {}

    def get_invoice_line(self):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')
        Property = pool.get('ir.property')
        Uom = pool.get('product.uom')
        invoice_line = InvoiceLine()
        invoice_line.type = 'line'
        invoice_line.origin = self.contract_line
        invoice_line.company = self.contract_line.contract.company
        invoice_line.currency = self.contract_line.contract.currency
        invoice_line.product = None
        if self.contract_line.service:
            invoice_line.product = self.contract_line.service.product
        invoice_line.description = '%(name)s (%(start)s - %(end)s)' % {
            'name': self.contract_line.description,
            'start': self.start_date,
            'end': self.end_date,
            }
        invoice_line.unit_price = self.contract_line.unit_price
        invoice_line.party = self.contract_line.contract.party
        taxes = []
        if invoice_line.product:
            invoice_line.unit = invoice_line.product.default_uom
            party = invoice_line.party
            pattern = self._get_tax_rule_pattern()
            for tax in invoice_line.product.customer_taxes_used:
                if party.customer_tax_rule:
                    tax_ids = party.customer_tax_rule.apply(tax, pattern)
                    if tax_ids:
                        taxes.extend(tax_ids)
                    continue
                taxes.append(tax.id)
            if party.customer_tax_rule:
                tax_ids = party.customer_tax_rule.apply(None, pattern)
                if tax_ids:
                    taxes.extend(tax_ids)
            invoice_line.account = invoice_line.product.account_revenue_used
            if not invoice_line.account:
                self.raise_user_error('missing_account_revenue', {
                        'contract_line': self.contract_line.rec_name,
                        'product': invoice_line.product.rec_name,
                        })
        else:
            invoice_line.unit = None
            for model in ('product.template', 'product.category'):
                invoice_line.account = Property.get('account_revenue', model)
                if invoice_line.account:
                    break
            if not invoice_line.account:
                self.raise_user_error('missing_account_revenue_property', {
                        'contract_line': self.contract_line.rec_name,
                        })
        invoice_line.taxes = taxes
        invoice_line.invoice_type = 'out_invoice'
        # Compute quantity based on dates
        contract_start = self.contract_line.contract.start_date
        invoice_date = self.contract_line.contract.rrule.after(contract_start)
        quantity = ((self.end_date - self.start_date).total_seconds()
            / (invoice_date - contract_start).total_seconds())
        rounding = invoice_line.unit.rounding if invoice_line.unit else 1
        invoice_line.quantity = Uom.round(quantity, rounding)
        return invoice_line

    @classmethod
    def _group_invoice_key(cls, line):
        '''
        The key to group invoice_lines by Invoice

        line is a tuple of consumption id and invoice line
        '''
        consumption_id, invoice_line = line
        consumption = cls(consumption_id)
        return (
            ('party', invoice_line.party),
            ('company', invoice_line.company),
            ('currency', invoice_line.currency),
            ('type', invoice_line.invoice_type),
            ('invoice_date', consumption.invoice_date),
            )

    @classmethod
    def _get_invoice(cls, keys):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Journal = pool.get('account.journal')
        journals = Journal.search([
                ('type', '=', 'revenue'),
                ], limit=1)
        if journals:
            journal, = journals
        else:
            journal = None
        values = dict(keys)
        values['invoice_address'] = values['party'].address_get('invoice')
        invoice = Invoice(**values)
        invoice.journal = journal
        invoice.payment_term = invoice.party.customer_payment_term
        invoice.account = invoice.party.account_receivable
        return invoice

    @classmethod
    @ModelView.button
    def invoice(cls, consumptions):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        lines = {}
        to_write = []
        for consumption in consumptions:
            line = consumption.get_invoice_line()
            if line:
                line.save()
                lines[consumption.id] = line
                to_write.extend(([consumption], {
                            'invoice_line': line.id,
                            }))
        if not lines:
            return
        lines = lines.items()
        lines = sorted(lines, key=cls._group_invoice_key)

        invoices = []
        for key, grouped_lines in groupby(lines, key=cls._group_invoice_key):
            invoice = cls._get_invoice(key)
            invoice.lines = (list(getattr(invoice, 'lines', []))
                + list(x[1] for x in grouped_lines))
            invoices.append(invoice)

        invoices = Invoice.create([x._save_values for x in invoices])
        Invoice.update_taxes(invoices)
        cls.write(*to_write)


class CreateConsumptionsStart(ModelView):
    'Create Consumptions Start'
    __name__ = 'contract.create_consumptions.start'
    date = fields.DateTime('Date')

    @staticmethod
    def default_date():
        return datetime.now()


class CreateConsumptions(Wizard):
    'Create Consumptions'
    __name__ = 'contract.create_consumptions'
    start = StateView('contract.create_consumptions.start',
        'contract.create_consumptions_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('OK', 'create_consumptions', 'tryton-ok', True),
            ])
    create_consumptions = StateAction('contract.act_contract_consumption')

    def do_create_consumptions(self, action):
        pool = Pool()
        Contract = pool.get('contract')
        contracts = Contract.search([
                ('state', '=', 'validated'),
                ])
        consumptions = Contract.consume(contracts, self.start.date)
        data = {'res_id': [c.id for c in consumptions]}
        if len(consumptions) == 1:
            action['views'].reverse()
        return action, data
