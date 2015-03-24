# This file is part of contract_invoice module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.wizard import Wizard, StateView, StateAction, Button

__all__ = ['InvoiceLine', 'CreateInvoicesStart', 'CreateInvoices']
__metaclass__ = PoolMeta


class InvoiceLine:
    __name__ = 'account.invoice.line'

    @classmethod
    def _get_origin(cls):
        models = super(InvoiceLine, cls)._get_origin()
        models.append('contract.consumption')
        return models


class CreateInvoicesStart(ModelView):
    'Create Invoices Start'
    __name__ = 'contract.create_invoices.start'

    date = fields.Date('Date')

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()


class CreateInvoices(Wizard):
    'Create Invoices'
    __name__ = 'contract.create_invoices'
    start = StateView('contract.create_invoices.start',
        'contract.create_invoices_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('OK', 'create_invoices', 'tryton-ok', True),
            ])
    create_invoices = StateAction(
            'account_invoice.act_invoice_out_invoice_form')

    def do_create_invoices(self, action):
        pool = Pool()
        Consumptions = pool.get('contract.consumption')
        consumptions = Consumptions.search(
            [('invoice_date', '<=', self.start.date)])
        invoices = Consumptions.invoice(consumptions)

        data = {'res_id': [c.id for c in invoices]}
        if len(invoices) == 1:
            action['views'].reverse()
        return action, data
