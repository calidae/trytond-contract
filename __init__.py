# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import contract
from . import invoice
from . import party


def register():
    Pool.register(
        party.Party,
        party.PartyContractGroupingMethod,
        contract.ContractService,
        contract.Contract,
        contract.ContractLine,
        contract.ContractConsumption,
        contract.CreateConsumptionsStart,
        invoice.CreateInvoicesStart,
        configuration.Configuration,
        configuration.ConfigurationSequence,
        configuration.ConfigurationAccount,
        invoice.InvoiceLine,
        invoice.CreditInvoiceStart,
        module='contract', type_='model')
    Pool.register(
        contract.AnalyticAccountEntry,
        contract.AnalyticContractLine,
        depends=['analytic_invoice'],
        module='contract', type_='model')
    Pool.register(
        contract.CreateConsumptions,
        invoice.CreateInvoices,
        invoice.CreditInvoice,
        party.PartyReplace,
        party.PartyErase,
        module='contract', type_='wizard')
