# -*- coding: utf-8 -*-
################################################################
#    License, author and contributors information in:          #
#    __openerp__.py file at the root folder of this module.    #
################################################################

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.addons.sale.sale import sale_order as so


class SaleOrder(osv.osv):
    _inherit = 'sale.order'

    def _get_order(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('sale.order.line')
        return list(set(line['order_id'] for line in line_obj.read(
            cr, uid, ids, ['order_id'], load='_classic_write',
            context=context)))

    _columns = {
        'public_sector': fields.boolean(
            string='Public Sector Works', readonly=True,
            states={'draft': [('readonly', False)]}),
        'ot_percentage': fields.integer(
            string='Order Tax Percentage', readonly=True,
            states={'draft': [('readonly', False)]}),
        'ge_percentage': fields.integer(
            string='General Expenses Percentage', readonly=True,
            states={'draft': [('readonly', False)]}),
        'ip_percentage': fields.integer(
            string='Industrial Profit Percentage', readonly=True,
            states={'draft': [('readonly', False)]}),
        'amount_material_exe': fields.function(
            so._amount_all_wrapper,
            digits_compute=dp.get_precision('Account'),
            string='Amount Material Execution',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [
                    'order_line', 'public_sector', 'ot_percentage',
                    'ge_percentage', 'ip_percentage'], 10),
                'sale.order.line': (_get_order, [
                    'price_unit', 'tax_id', 'discount',
                    'product_uom_qty'], 10),
            },
            multi='sums',
            help='Amount untaxed without general expenses neither industrial '
                 'profit included.'),
        'general_expenses': fields.function(
            so._amount_all_wrapper, digits_compute=dp.get_precision('Account'),
            string='General Expenses',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [
                    'order_line', 'public_sector', 'ot_percentage',
                    'ge_percentage', 'ip_percentage'], 10),
                'sale.order.line': (_get_order, [
                    'price_unit', 'tax_id', 'discount',
                    'product_uom_qty'], 10),
            },
            multi='sums', help='General expenses.'),
        'industrial_profit': fields.function(
            so._amount_all_wrapper,
            digits_compute=dp.get_precision('Account'),
            string='Industrial Profit',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [
                    'order_line', 'public_sector', 'ot_percentage',
                    'ge_percentage', 'ip_percentage'], 10),
                'sale.order.line': (_get_order, [
                    'price_unit', 'tax_id', 'discount',
                    'product_uom_qty'], 10),
            },
            multi='sums', help='Industrial profit.'),
        'ge_ip_total': fields.function(
            so._amount_all_wrapper,
            digits_compute=dp.get_precision('Account'),
            string='GE and IP Sum',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [
                    'order_line', 'public_sector', 'ot_percentage',
                    'ge_percentage', 'ip_percentage'], 10),
                'sale.order.line': (_get_order, [
                    'price_unit', 'tax_id', 'discount',
                    'product_uom_qty'], 10),
            },
            multi='sums',
            help='Sum of general expenses plus industrial profit.'),

        'amount_untaxed': fields.function(
            so._amount_all_wrapper,
            digits_compute=dp.get_precision('Account'),
            string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [
                    'order_line', 'public_sector', 'ot_percentage',
                    'ge_percentage', 'ip_percentage'], 10),
                'sale.order.line': (_get_order, [
                    'price_unit', 'tax_id', 'discount',
                    'product_uom_qty'], 10),
            },
            multi='sums',
            help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(
            so._amount_all_wrapper,
            digits_compute=dp.get_precision('Account'),
            string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [
                    'order_line', 'public_sector', 'ot_percentage',
                    'ge_percentage', 'ip_percentage'], 10),
                'sale.order.line': (_get_order, [
                    'price_unit', 'tax_id', 'discount',
                    'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(
            so._amount_all_wrapper,
            digits_compute=dp.get_precision('Account'),
            string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, [
                    'order_line', 'public_sector', 'ot_percentage',
                    'ge_percentage', 'ip_percentage'], 10),
                'sale.order.line': (_get_order, [
                    'price_unit', 'tax_id', 'discount',
                    'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
    }

    _defaults = {
        'ot_percentage': 21,
        'ge_percentage': 13,
        'ip_percentage': 6,
    }

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_material_exe': 0.0,
                'general_expenses': 0.0,
                'industrial_profit': 0.0,
                'ge_ip_total': 0.0,
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                if not order.public_sector:
                    val += self._amount_line_tax(cr, uid, line,
                                                 context=context)
            if order.public_sector:
                amount_material_exe = cur_obj.round(cr, uid, cur, val1)
                res[order.id]['amount_material_exe'] = amount_material_exe
                general_expenses = cur_obj.round(cr, uid, cur, (
                    amount_material_exe * order.ge_percentage / 100))
                res[order.id]['general_expenses'] = general_expenses
                industrial_profit = cur_obj.round(cr, uid, cur, (
                    amount_material_exe * order.ip_percentage / 100))
                res[order.id]['industrial_profit'] = industrial_profit
                ge_ip_total = cur_obj.round(cr, uid, cur, (
                    general_expenses + industrial_profit))
                res[order.id]['ge_ip_total'] = ge_ip_total
                amount_untaxed = cur_obj.round(cr, uid, cur, (
                    amount_material_exe + ge_ip_total))
                res[order.id]['amount_untaxed'] = \
                    amount_untaxed
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, (
                    amount_untaxed * order.ot_percentage / 100))
            else:
                amount_untaxed = cur_obj.round(cr, uid, cur, val1)
                res[order.id]['amount_untaxed'] = amount_untaxed
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + \
                res[order.id]['amount_tax']
        return res

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        # Preserve public sector works fields from sale order to account
        # invoice (case: complete sale order)
        values = super(SaleOrder, self)._prepare_invoice(
            cr, uid, order, lines, context)
        values.update({
            'public_sector': order.public_sector or False,
            'ot_percentage': order.ot_percentage or False,
            'ge_percentage': order.ge_percentage or False,
            'ip_percentage': order.ip_percentage or False,
            'amount_material_exe': order.amount_material_exe or False,
            'general_expenses': order.general_expenses or False,
            'industrial_profit': order.industrial_profit or False,
            'ge_ip_total': order.ge_ip_total or False,
        })
        return values
