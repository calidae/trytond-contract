from behave import given, when, then
from hamcrest import assert_that, equal_to

import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from proteus import Model, Wizard
from trytond.modules.company.tests.tools import create_company, \
        get_company
from trytond.modules.account.tests.tools import create_fiscalyear, \
        create_chart, get_accounts, create_tax, set_tax_code
from trytond.modules.account_invoice.tests.tools import \
    set_fiscalyear_invoice_sequences, create_payment_term

import re

#TODO: To be used on all modules,
def convert_to_type(full_field_name, value):
    """ Converts the value from a behave table into its correct type based on the name
        of the column (header).  If it is wrapped in a convert method, then use it to
        determine the value type the column should contain.

        Returns: a tuple with the newly converted value and the name of the field (without the
                 convertion method specified).  E.g. int(size) will return size as the new field
                 name and the value will be converted to an int and returned.
    """
    field_name = full_field_name.strip()
    matchers = [(re.compile('int\((.*)\)'), lambda val: int(val)),
                (re.compile('float\((.*)\)'), lambda val: float(val)),
                (re.compile('decimal\((.*)\)'), lambda val: Decimal(val)),
                (re.compile('date\((.*)\)'), lambda val: datetime.datetime.strptime(val, '%Y-%m-%d').date())]
    for (matcher, func) in matchers:
        matched = matcher.match(field_name)
        if matched:
            if value:
                return (func(value), matched.group(1))
            else:
                return (None, matched.group(1))
    return (value, full_field_name)


@given(u'a invoice configuration database')
def step_impl(context):

    # create company
    create_company()
    company = get_company()

    today = datetime.date(2015, 01, 01)

    User = Model.get('res.user')
    context._proteus_config._context = User.get_preferences(True,
        context._proteus_config.context)
    context._proteus_config._context['company'] = company.id

    fiscalyear = set_fiscalyear_invoice_sequences(
        create_fiscalyear(company, today))

    fiscalyear.click('create_period')
    # Create Chart of Accounts
    create_chart(company)
    context.accounts = get_accounts(company)
    # receivable = accounts['receivable']
    # revenue = accounts['revenue']
    # expense = accounts['expense']
    # account_tax = accounts['tax']

    # Create tax::
    tax = set_tax_code(create_tax(Decimal('.10')))
    tax.save()
    context.tax = tax
    # invoice_base_code = tax.invoice_base_code
    # invoice_tax_code = tax.invoice_tax_code
    # credit_note_base_code = tax.credit_note_base_code
    # credit_note_tax_code = tax.credit_note_tax_code

    # Create party::
    Party = Model.get('party.party')
    party = Party(name='Party')
    party.save()
    context.party = party
    # Create payment term::
    payment_term = create_payment_term()
    payment_term.save()
    party.customer_payment_term = payment_term
    party.save()


@given(u'Basic Contract configuration')
def step_impl(context):

    Sequence = Model.get('ir.sequence')
    sequence_contract, = Sequence.find([('code', '=', 'contract')])
    Journal = Model.get('account.journal')
    journal, = Journal.find([('type', '=', 'revenue')])

    ContractConfig = Model.get('contract.configuration')
    contract_config = ContractConfig(1)
    contract_config.contract_sequence = sequence_contract
    contract_config.journal = journal
    contract_config.save()

@given(u'set of services')
def step_impl(context):

    ProductUom = Model.get('product.uom')
    unit, = ProductUom.find([('name', '=', 'Unit')])
    unit.rounding =  0.01
    unit.digits = 2
    unit.save()

    ProductTemplate = Model.get('product.template')
    Product = Model.get('product.product')
    product = Product()
    template = ProductTemplate()
    template.name = 'product'
    template.default_uom = unit
    template.type = 'service'
    template.list_price = Decimal('40')
    template.cost_price = Decimal('25')
    template.account_expense = context.accounts['expense']
    template.account_revenue = context.accounts['revenue']
    template.customer_taxes.append(context.tax)
    template.save()
    product.template = template
    product.save()

    Service = Model.get('contract.service')

    for row in context.table:
        service = Service()
        service.name = row['name']
        service.product = product
        service.save()

@given(u'a contract {name} that starts on {start_date:ti}, first invoice on {first_invoice_date:ti}, {freq} and interval of {interval:n}')
def step_impl(context, name, start_date, first_invoice_date, freq, interval):
    Contract = Model.get('contract')
    contract = Contract()
    contract.party = context.party
    contract.reference = name
    contract.freq = freq
    contract.interval = interval
    contract.start_period_date = start_date
    contract.first_invoice_date = first_invoice_date
    contract.save()

@given(u'A set of lines for contracts')
def step_impl(context):
    Contract = Model.get('contract')
    ContractLine = Model.get('contract.line')
    ContractService = Model.get('contract.service')
    contract, = Contract.find([])
    for row in context.table:
        l = ContractLine()
        l.contract = contract
        for key, val in row.as_dict().iteritems():
            if key == 'service':
                service, = ContractService.find([('name', '=', val)])
                val = service
            val, key = convert_to_type(key, val)
            setattr(l, key, val)
        l.save()

@when(u'confirm contract')
def step_impl(context):
    Contract = Model.get('contract')
    contract, = Contract.find([])
    contract.click('confirm')

@then(u'contract state is {state}')
def step_impl(context, state):
    Contract = Model.get('contract')
    contract, = Contract.find([])
    assert_that(state, equal_to(contract.state))

@when(u'I Create Consumptions for Date {date:ti}')
def step_impl(context, date):
    create_consumptions = Wizard('contract.create_consumptions')
    create_consumptions.form.date = date
    create_consumptions.execute('create_consumptions')

# @then(u'I get {nlines:n} consumptions Lines for date 2015-01-31')
# def step_impl(context, nlines):
#     Consumption = Model.get('contract.consumption')
#     consumptions = Consumption.find([])
#     assert_that(nlines, equal_to(len(consumptions)))

@then(u'I get a set of consumptions not invoiced')
def step_impl(context):
    Consumption = Model.get('contract.consumption')
    consumptions = Consumption.find([])

    cons = {}
    for con in consumptions:
        cons[(con.contract_line.service.name, con.init_period_date)] = con

    for row in context.table:
        d, _ = convert_to_type('date(init_period_date)',
            row['date(init_period_date)'])
        consumption = cons[(row['service'], d)]
        for key, val in row.as_dict().iteritems():
            if key == 'service':
                continue
            val, key = convert_to_type(key, val)
            consumption_key_val = getattr(consumption, key)
            assert_that(consumption_key_val, equal_to(val))

@when(u'I Create Consumptions for Date {date:ti}')
def step_impl(context, date):
    create_consumptions = Wizard('contract.create_consumptions')
    create_consumptions.form.date = date
    create_consumptions.execute('create_consumptions')


@then(u'I get {nlines:n} consumptions lines')
def step_impl(context, nlines):
    Consumption = Model.get('contract.consumption')
    consumptions = Consumption.find([])
    assert_that(equal_to(len(consumptions)), nlines)

@when(u'I Invoice on Date {date:ti}')
def step_impl(context, date):
    create_invoices = Wizard('contract.create_invoices')
    create_invoices.form.date = date
    create_invoices.execute('create_invoices')

@then(u'I get {nlines:n} invoices')
def step_impl(context, nlines):
    Invoice = Model.get('account.invoice')
    invoices = Invoice.find([])
    assert_that(equal_to(len(invoices)), nlines)

@then(u'Invoice line Amounts for consumptions')
def step_impl(context):
    Consumption = Model.get('contract.consumption')
    consumptions = Consumption.find([])

    cons = {}
    for con in consumptions:
        cons[(con.contract_line.service.name, con.invoice_date)] = con

    for row in context.table:
        d, _ = convert_to_type('date(invoice_date)',
            row['date(invoice_date)'])
        consumption = cons[(row['service'], d)]
        for key, val in row.as_dict().iteritems():
            if key in ('service', 'date(invoice_date)'):
                continue
            val, key = convert_to_type(key, val)
            invoice_line_amount = consumption.invoice_lines[0].amount
            assert_that(invoice_line_amount, equal_to(val))
