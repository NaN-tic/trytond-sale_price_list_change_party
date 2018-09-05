=====================================
Sale Price List Change Party Scenario
=====================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Install module::

    >>> config = activate_modules('sale_price_list_change_party')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']
    >>> cash = accounts['cash']

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()
    >>> discount_customer = Party(name='Discount Customer')
    >>> discount_customer.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> product, = template.products
    >>> product.cost_price = Decimal('5')
    >>> template.save()
    >>> product, = template.products

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create two price list one and assign on to each customer::

    >>> PriceList = Model.get('product.price_list')
    >>> default_price_list = PriceList(name='Default')
    >>> price_list_line = default_price_list.lines.new()
    >>> price_list_line.formula = 'unit_price'
    >>> default_price_list.save()
    >>> discount_price_list = PriceList(name='50% Discount')
    >>> price_list_line = discount_price_list.lines.new()
    >>> price_list_line.formula = 'unit_price * 0.5'
    >>> discount_price_list.save()
    >>> customer.sale_price_list = default_price_list
    >>> customer.save()
    >>> discount_customer.sale_price_list = discount_price_list
    >>> discount_customer.save()

Sale products to customer::

    >>> Sale = Model.get('sale.sale')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.price_list == default_price_list
    True
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0
    >>> sale_line.unit_price
    Decimal('10.0000')
    >>> sale.save()
    >>> sale.state
    u'draft'

Change party of the sale::

    >>> change_party = Wizard('sale.change.party', [sale])
    >>> party_address, = discount_customer.addresses
    >>> change_party.form.party = discount_customer
    >>> change_party.form.shipment_address == party_address
    True
    >>> change_party.form.invoice_address == party_address
    True
    >>> change_party.form.price_list == discount_price_list
    True
    >>> change_party.execute('change_party')

Sale price list and prices should be updated::

    >>> sale.reload()
    >>> sale.party == discount_customer
    True
    >>> sale.price_list == discount_price_list
    True
    >>> sale_line, = sale.lines
    >>> sale_line.unit_price
    Decimal('5.0000')
