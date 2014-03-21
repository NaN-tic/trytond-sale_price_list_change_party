# This file is part of the sale_price_list_change_party module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import *


def register():
    Pool.register(
        SaleChangePartyStart,
        module='sale_price_list_change_party', type_='model')
    Pool.register(
        SaleChangeParty,
        module='sale_price_list_change_party', type_='wizard')
