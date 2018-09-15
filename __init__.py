# This file is part of the sale_price_list_change_party module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import sale


def register():
    Pool.register(
        sale.SaleChangePartyStart,
        module='sale_price_list_change_party', type_='model')
    Pool.register(
        sale.SaleChangeParty,
        module='sale_price_list_change_party', type_='wizard')
