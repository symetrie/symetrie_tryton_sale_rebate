====================
Sale Rebate Scenario
====================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import Model, Wizard, Report
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Install sale::

    >>> config = activate_modules('sale_rebate')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> revenue = accounts['revenue']

Create tax::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> template = ProductTemplate()
    >>> template.name = "Product"
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.salable = True
    >>> template.list_price = Decimal('15')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_revenue = revenue
    >>> template.customer_taxes.append(tax)
    >>> template.save()
    >>> product, = template.products
    >>> product.cost_price = Decimal('5')
    >>> product.save()

Sale products::

    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 1
    >>> sale_line.rebate
    Decimal('0.00')
    >>> sale.save()
    >>> sale_line, = sale.lines
    >>> sale_line.rebate
    Decimal('0.00')
    >>> sale_line.amount
    Decimal('15.00')
    >>> sale_line.unit_price = Decimal('13')
    >>> sale_line.rebate
    Decimal('13.33')
    >>> sale_line.amount
    Decimal('13.00')
    >>> sale.save()
    >>> sale_line, = sale.lines
    >>> sale_line.rebate
    Decimal('13.33')
    >>> sale_line.rebate = Decimal('0')
    >>> sale_line.unit_price
    Decimal('15.0000')
    >>> sale_line.amount
    Decimal('15.00')
    >>> sale_line.rebate = Decimal('50')
    >>> sale_line.unit_price
    Decimal('7.5000')
    >>> sale_line.amount
    Decimal('7.50')
