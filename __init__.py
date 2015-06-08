# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .contract import *
from .configuration import *
from .invoice import *
from .party import *


def register():
    Pool.register(
        Party,
        ContractService,
        Contract,
        ContractLine,
        ContractConsumption,
        CreateConsumptionsStart,
        CreateInvoicesStart,
        Configuration,
        InvoiceLine,
        module='contract', type_='model')
    Pool.register(
        CreateConsumptions,
        CreateInvoices,
        module='contract', type_='wizard')
