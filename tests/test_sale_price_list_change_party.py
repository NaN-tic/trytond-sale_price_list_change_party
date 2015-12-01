# This file is part of the sale_price_list_change_party module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class SalePriceListChangePartyTestCase(ModuleTestCase):
    'Test Sale Price List Change Party module'
    module = 'sale_price_list_change_party'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        SalePriceListChangePartyTestCase))
    return suite