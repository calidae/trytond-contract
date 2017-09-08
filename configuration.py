# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pyson import Eval

__all__ = ['Configuration']


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Contract Configuration'
    __name__ = 'contract.configuration'
    contract_sequence = fields.Property(fields.Many2One('ir.sequence',
            'Contract Reference Sequence', domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'contract'),
                ], required=True))
    journal = fields.Property(fields.Many2One('account.journal', 'Journal',
            required=True, domain=[
                ('type', '=', 'revenue'),
                ]))
    payment_term = fields.Property(fields.Many2One(
            'account.invoice.payment_term', 'Payment Term',
            help='The payment term to be used when there is none set on the '
            'party.'))
