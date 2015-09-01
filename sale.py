# This file is part of the sale_price_list_change_party module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.wizard import Button, StateTransition, StateView, Wizard

__all__ = ['SaleChangePartyStart', 'SaleChangeParty']
__metaclass__ = PoolMeta


class SaleChangePartyStart(ModelView):
    'Sale Change Party'
    __name__ = 'sale.change.party.start'
    company = fields.Many2One('company.company', 'Company', required=True,
        readonly=True, states={'invisible': True},
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ])
    party = fields.Many2One('party.party', 'Party', required=True)
    shipment_address = fields.Many2One('party.address', 'Shipment Address',
        domain=[('party', '=', Eval('party'))],
        depends=['party'], required=True)
    invoice_address = fields.Many2One('party.address', 'Invoice Address',
        domain=[('party', '=', Eval('party'))],
        depends=['party'], required=True)
    price_list = fields.Many2One('product.price_list', 'Price List',
        domain=[('company', '=', Eval('company'))],
        depends=['company'])

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @fields.depends('party')
    def on_change_party(self):
        Sale = Pool().get('sale.sale')

        if self.party:
            sale = Sale()
            sale.party = self.party
            sale.on_change_party()

            self.shipment_address = sale.shipment_address
            self.invoice_address = sale.invoice_address
            self.price_list = sale.price_list if sale.price_list else None


class SaleChangeParty(Wizard):
    'Sale Change Party'
    __name__ = 'sale.change.party'
    start = StateView('sale.change.party.start',
        'sale_price_list_change_party.sale_change_party_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Change Party', 'change_party', 'tryton-ok', default=True),
            ])
    change_party = StateTransition()

    @classmethod
    def __setup__(cls):
        super(SaleChangeParty, cls).__setup__()
        cls._error_messages.update({
                'sale_not_in_draft_state': 'This sale is not in draft state.',
                })

    def transition_change_party(self):
        pool = Pool()
        Sale = pool.get('sale.sale')
        sale_id = Transaction().context.get('active_id')
        sale = Sale(sale_id)
        if sale.state != 'draft':
            self.raise_user_error('sale_not_in_draft_state')
        sale_pricelist = sale.price_list

        sale.party = self.start.party
        sale.price_list = self.start.price_list
        sale.shipment_address = self.start.shipment_address
        sale.invoice_address = self.start.invoice_address
        sale.save()

        if self.start.price_list and (not sale_pricelist or
                (sale_pricelist.id != self.start.price_list.id)):
            for line in sale.lines:
                for key, value in line.on_change_quantity().iteritems():
                    setattr(line, key, value)
                line.save()
        return 'end'
