# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import copy
from decimal import Decimal
from trytond.pool import PoolMeta, Pool
from trytond.model import Model, fields
from trytond.pyson import Eval, If, Bool
from trytond.transaction import Transaction

__all__ = ['SaleLine']

class SaleLine:
    __metaclass__ = PoolMeta
    __name__ = 'sale.line'

    list_price = fields.Numeric('List Price', digits=(16, 4),
        states={
            'invisible': ((Eval('type') != 'line') | ~Eval('product')),
            'readonly': True, # to get it saved by the client
            },
        depends=['type', 'product'])
    rebate = fields.Function(fields.Numeric('Rebate', digits=(16, 2),
            help='Rebate in percentage',
#            on_change=['list_price', 'rebate'],
            states={
                'invisible': ((Eval('type') != 'line') | ~Eval('product')),
                },
            depends=['type', 'product']),
        'get_rebate', setter='set_rebate')
    print '======== sale rebate SaleLine class new fields'

    @classmethod
    def __setup__(cls):
        super(SaleLine, cls).__setup__()
        for field in (cls.quantity, cls.unit):
            field.on_change = copy.copy(field.on_change)
            if 'list_price' not in field.on_change:
                field.on_change.add('list_price')
        if cls.unit_price.on_change:
            cls.unit_price.on_change = copy.copy(cls.unit_price.on_change)
        else:
            cls.unit_price.on_change = set()
        for fname in ('unit_price', 'list_price'):
            if fname not in cls.unit_price.on_change:
                cls.unit_price.on_change.add(fname)
        cls.__rpc__.setdefault('on_change_unit_price', False)
#        if 'rebate' not in cls.amount.on_change_with:
#            cls.amount = copy.copy(cls.amount)
#            cls.amount.on_change_with = copy.copy(cls.amount.on_change_with)
#            cls.amount.on_change_with.add('rebate')
        print u'=== sale rebate __setup__: ', cls.amount.on_change_with
# AttributeError: type object 'sale.line' has no attribute '_reset_columns'
#        cls._reset_columns()

    @fields.depends('list_price', 'rebate')
    def on_change_rebate(self):
        print u'=== sale rebate on_change_rebate: %s' % str(self.rebate)
        self.unit_price = self._compute_unit_price(self.list_price, self.rebate)
#        self.rebate = self._compute_unit_price(self.list_price, self.rebate)

#    @fields.depends('list_price', 'rebate')
#    def on_change_with_rebate(self):
#        print u'=== sale rebate on_change_with_rebate: %s' % str(self.rebate)
#        self.unit_price = self._compute_unit_price(self.list_price, self.rebate)
#        return self._compute_rebate(self.list_price, self.unit_price)
    
    @classmethod
    def _compute_unit_price(self, list_price, rebate):
        if not rebate:
            return list_price
        unit_price = (1 - (rebate / 100)) * list_price
        unit_price.quantize(Decimal(str(10 ** -self.unit_price.digits[1])))
        return unit_price        

    @classmethod
    def _compute_rebate(self, list_price, unit_price):
        if not unit_price:
            unit_price = Decimal('0')
        if not list_price:
            value = Decimal('0')
        else:
            value = (1 - unit_price / list_price) * 100
        return value.quantize(Decimal(str(10 ** -self.rebate.digits[1])))

    @classmethod
    def get_rebate(self, ids, name):
        result = {}
        for line in self.browse(ids):
            result[line.id] = self._compute_rebate(line.list_price,
                line.unit_price)
        return result

    @classmethod
    def set_rebate(self, ids, name, value):
        print u'sale rebate set_rebate: %s' % str(value)
#        for line in self.browse(ids):
#            line.unit_price = _compute_unit_price(self, line.list_price, value)

    def _compute_list_price(self, product, currency, date):
        pool = Pool()
        Company = pool.get('company.company')
        Date = pool.get('ir.date')
        Currency = pool.get('currency.currency')

        today = Date.today()
        list_price = product.list_price
        company = Company(Transaction().context['company'])
        if currency and company:
#           Maybe could be 
#           if company.currency != currency:
            if company.currency.id != currency.id:
                date = date or today
                with Transaction().set_context(date=date):
                    list_price = Currency.compute(company.currency.id,
                        list_price, currency.id)
        return list_price

    @fields.depends('product')
    def on_change_product(self):
#        Product = Pool().get('product.product')
        Currency = Pool().get('currency.currency')

        super(SaleLine, self).on_change_product()
        list_price = Decimal('0')
#        if values.get('product'):
        if self.product:
            print u'=== sale rebate change product: %s' % self.product.rec_name
#            product = Product.browse(values['product'])
            currency = None
#            if values.get('_parent_sale.currency'):
            if self.sale.currency:
#                currency = Currency.browse(values['_parent_sale.currency'])
                currency = self.sale.currency
            list_price = self._compute_list_price(self.product, currency,
#                values.get('_parent_sale.sale_date'))
                self.sale.sale_date)
        self.list_price = list_price
        self.rebate = self._compute_rebate(list_price, self.unit_price)

    @fields.depends('quantity', 'list_price', 'unit_price')
    def on_change_quantity(self):
        print u'=== sale rebate on_change_quantity: %s' % self.quantity
        super(SaleLine, self).on_change_quantity()
        self.rebate = self._compute_rebate(self.list_price, self.unit_price)

    @fields.depends('product', 'list_price', 'unit_price')
    def on_change_unit_price(self):
        print u'=== sale rebate on_change_unit_price: %s' % self.unit_price
        try:
            result = super(SaleLine, self).on_change_unit_price()
        except AttributeError:
            pass
        self.rebate = self._compute_rebate(self.list_price, self.unit_price)

    def get_invoice_line(self, line):
        InvoiceLine = Pool().get('account.invoice.line')
        result = super(SaleLine, self).get_invoice_line(line)
        if hasattr(InvoiceLine, 'list_price'):
            for inv_line in result:
                if inv_line['unit_price'] == line.unit_price:
                    inv_line['list_price'] = line.list_price
        return result
