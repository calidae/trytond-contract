# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
import contract
import configuration
import invoice
import party

def register():
    Pool.register(
        party.Party,
        contract.ContractService,
        contract.Contract,
        contract.ContractLine,
        contract.ContractConsumption,
        contract.CreateConsumptionsStart,
        invoice.CreateInvoicesStart,
        configuration.Configuration,
        invoice.InvoiceLine,
        invoice.CreditInvoiceStart,
        module='contract', type_='model')
    Pool.register(
        contract.CreateConsumptions,
        invoice.CreateInvoices,
        invoice.CreditInvoice,
        module='contract', type_='wizard')
