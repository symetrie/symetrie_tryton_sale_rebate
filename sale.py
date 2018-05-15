# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import PoolMeta, Pool
from trytond.model import fields
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Line']


class Line:
    __metaclass__ = PoolMeta
    __name__ = 'sale.line'

    list_price = fields.Numeric('List Price', digits=(16, 4),
        states={
            'invisible': ((Eval('type') != 'line') | ~Eval('product')),
            'readonly': True,  # to get it saved by the client
            },
        depends=['type', 'product'])
    rebate = fields.Function(fields.Numeric('Rebate', digits=(16, 2),
            help='Rebate in percentage',
            states={
                'invisible': ((Eval('type') != 'line') | ~Eval('product')),
                },
            depends=['type', 'product']),
        'on_change_with_rebate', setter='set_rebate')

    @fields.depends('list_price', 'unit_price')
    def on_change_with_rebate(self, name=None):
        if not self.list_price:
            rebate = Decimal(0)
        else:
            rebate = (1 - (self.unit_price or 0) / self.list_price) * 100
        return rebate.quantize(
            Decimal(str(10 ** -self.__class__.rebate.digits[1])))

    @fields.depends('list_price', 'rebate',
        # XXX: From on_change_with_amoun
        # https://bugs.tryton.org/issue5191
        'type', 'quantity', 'unit', 'sale', '_parent_sale.currency')
    def on_change_rebate(self):
        if self.list_price is None or self.rebate is None:
            return
        unit_price = (1 - (self.rebate / 100)) * self.list_price
        self.unit_price = unit_price.quantize(
            Decimal(str(10 ** -self.__class__.unit_price.digits[1])))
        self.amount = self.on_change_with_amount()

    @classmethod
    def set_rebate(cls, lines, name, value):
        pass

    @fields.depends('product', '_parent_sale.currency', '_parent_sale.company')
    def on_change_product(self):
        pool = Pool()
        Currency = pool.get('currency.currency')
        Date = pool.get('ir.date')

        super(Line, self).on_change_product()
        list_price = Decimal('0')
        if self.product:
            list_price = self.product.list_price
            date = self.sale.sale_date or Date.today()
            if self.sale.currency and self.sale.company:
                with Transaction().set_context(date=date):
                    list_price = Currency.compute(
                        self.sale.company.currency, list_price,
                        self.sale.currency, round=False)
        self.list_price = list_price.quantize(
            Decimal(1) / 10 ** self.__class__.list_price.digits[1])
        self.rebate = self.on_change_with_rebate()

    @fields.depends('list_price', 'unit_price')
    def on_change_quantity(self):
        super(Line, self).on_change_quantity()
        self.rebate = self.on_change_with_rebate()

    def get_invoice_line(self):
        InvoiceLine = Pool().get('account.invoice.line')
        lines = super(Line, self).get_invoice_line()
        if hasattr(InvoiceLine, 'list_price'):
            for line in lines:
                if line.unit_price == self.unit_price:
                    line.list_price = self.list_price
        return lines
