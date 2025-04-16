import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear, create_tax,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install module
        activate_modules('sale_price_list_change_party')

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()
        discount_customer = Party(name='Discount Customer')
        discount_customer.save()

        # Create account categories
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()
        account_category_tax, = account_category.duplicate()
        account_category_tax.customer_taxes.append(tax)
        account_category_tax.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.salable = True
        template.list_price = Decimal('10')
        template.account_category = account_category_tax
        product, = template.products
        product.cost_price = Decimal('5')
        template.save()
        product, = template.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create two price list one and assign on to each customer
        PriceList = Model.get('product.price_list')
        default_price_list = PriceList(name='Default', price='list_price')
        price_list_line = default_price_list.lines.new()
        price_list_line.formula = 'unit_price'
        default_price_list.save()
        discount_price_list = PriceList(name='50% Discount', price='list_price')
        price_list_line = discount_price_list.lines.new()
        price_list_line.formula = 'unit_price * 0.5'
        discount_price_list.save()
        customer.sale_price_list = default_price_list
        customer.save()
        discount_customer.sale_price_list = discount_price_list
        discount_customer.save()

        # Sale products to customer
        Sale = Model.get('sale.sale')
        sale = Sale()
        sale.party = customer
        sale.payment_term = payment_term
        self.assertEqual(sale.price_list, default_price_list)

        sale_line = sale.lines.new()
        sale_line.product = product
        sale_line.quantity = 2.0
        self.assertEqual(sale_line.unit_price, Decimal('10.0000'))

        sale.save()
        self.assertEqual(sale.state, 'draft')

        # Change party of the sale
        change_party = Wizard('sale.change.party', [sale])
        party_address, = discount_customer.addresses
        change_party.form.party = discount_customer
        self.assertEqual(change_party.form.shipment_address, party_address)
        self.assertEqual(change_party.form.invoice_address, party_address)
        self.assertEqual(change_party.form.price_list, discount_price_list)

        change_party.execute('change_party')

        # Sale price list and prices should be updated
        sale.reload()
        self.assertEqual(sale.party, discount_customer)
        self.assertEqual(sale.shipment_party, None)
        self.assertEqual(sale.invoice_party, None)
        self.assertEqual(sale.invoice_address, party_address)
        self.assertEqual(sale.shipment_address, party_address)
        self.assertEqual(sale.price_list, discount_price_list)

        sale_line, = sale.lines
        self.assertEqual(sale_line.unit_price, Decimal('5.0000'))
