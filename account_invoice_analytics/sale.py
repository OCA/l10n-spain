# -*- encoding: utf-8 -*-
##############################################################################
#
#    Avanzosc - Avanced Open Source Consulting
#    Copyright (C) 2011 - 2012 Avanzosc <http://www.avanzosc.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import time
from mx import DateTime

from osv import osv
from osv import fields

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    def _check_installments(self, cr, uid, ids): 
        for line in self.browse(cr, uid, ids):
            if line.installments < 2:
                return False
        return True
 
    _columns = {
        'invoice_mode':fields.related('product_id', 'invoicing_mode', type="selection", selection=[('once','Invoice Once'),
                ('installments','Payment by Installments'),
                ('recur','Invoice Recursively'),
                ('no','Do not Invoice'),
                ], string="Invoice Mode",store=True, readonly=True),
        'installments':fields.integer('Installments'),
        'installment_unit': fields.selection([
            ('days','Days'),
            ('weeks','Weeks'),
            ('months','Months'),
            ('years','Years'),
            ], 'Unit'),
        'analytic_created':fields.boolean("Analytic line created"),
        'invoice_date': fields.date('First invoice date', required=False),
        'expire_date': fields.date('Expire date'),
        'partner_signed_date': fields.date('Signed on'),
        'interval': fields.integer('Interval', help="Time before current validity expires to prolong the agreement for the next term."),
        'interval_unit': fields.selection([
            ('days','Days'),
            ('weeks','Weeks'),
            ('months','Months'),
            ('years','Years'),
            ], 'Unit'),
        'period': fields.integer('Period', help="Period time to prolong the next agreement"),
        'period_unit': fields.selection([
            ('days','Days'),
            ('weeks','Weeks'),
            ('months','Months'),
            ('years','Years'),
            ], 'Unit'),
        'payment': fields.selection([('start','In advance'),('end','After')], 'Payment'),
    }
    
    _defaults = {
        'invoice_date': lambda*a: time.strftime('%Y/%m/%d'),
        'installments': lambda *a: 2,
        'installment_unit': lambda *a: 'months',
        'period': lambda *a: 1,
        'period_unit': lambda *a: 'months',
        'interval': lambda *a: 1,
        'interval_unit': lambda *a: 'weeks',
        'payment': lambda *a: 'start',
    }
    
    _constraints = [(_check_installments, 'Error: Invalid Installment Quantity', ['Installments']), ]
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
            uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging, fiscal_position, flag, context=context)
        if product:
            product_obj = self.pool.get('product.product').browse(cr, uid, product)
            if product_obj.invoicing_mode:
                res['value'].update({'invoice_mode': product_obj.invoicing_mode})
        return res
    
sale_order_line()

class sale_order(osv.osv):
    _inherit = 'sale.order'
 
    _columns = {
        'agreement': fields.many2one('inv.agreement', 'Agreement'),
        'agreement_date': fields.date('Agreement Date'),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice On Order After Delivery'),
            ('picking', 'Invoice From The Picking'),
            ('analytic', 'Invoice From Analytics'),
        ], 'Shipping Policy', required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }
    
#    def onchange_date_order(self, cr, uid, ids, date_order, context=None):
#        res = {}
#        if date_order:
#            res = {
#                'agreement_date': date_order,
#            }
#        return {'value': res}
    
    def change_date_agree(self, cr, uid, ids, context=None):
        res = {}
        lines = []
        sale_line_obj = self.pool.get('sale.order.line')
        for sale in self.browse(cr, uid, ids):
            if sale.agreement_date:
                for line in sale.order_line:
                    sale_line_obj.write(cr, uid, [line.id], {'invoice_date': sale.agreement_date})
            else:
                for line in sale.order_line:
                    sale_line_obj.write(cr, uid, [line.id], {'invoice_date': sale.date_order})
        return True
    
    def action_create_analytic_lines(self, cr, uid, ids, context=None):
        res = False
        values = {}
        obj_sale_order_line = self.pool.get('sale.order.line')
        obj_account_analytic_line = self.pool.get('account.analytic.line')
        obj_factor = self.pool.get('hr_timesheet_invoice.factor')
        obj_agreement = self.pool.get('inv.agreement')
        if context is None:
            context = {}
        for order in self.browse(cr, uid, ids, context=context):
            analytic_account = order.project_id.id
            factor = obj_factor.search(cr, uid, [('factor', '=', 0)])[0]
            for line in order.order_line:
                if not line.analytic_created:
                    if line.product_id.property_account_income:
                        general_account = line.product_id.property_account_income.id
                    else:
                        general_account = line.product_id.categ_id.property_account_income_categ.id
                    if not line.invoice_date:
                        raise osv.except_osv(_('User error'), _('Invoice Date not found for: %s') %(line.product_id.name))
                    values = {
                        'date': line.invoice_date,
                        'account_id': analytic_account,
                        'unit_amount': line.product_uom_qty,
                        'name': line.name,
                        'sale_amount':line.price_subtotal,
                        'general_account_id': general_account,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_id.uom_id.id,
                        'ref': order.name,
                        'to_invoice': factor,
                        'journal_id': 1,
                        'sale_id': order.id,
                    }
                    if line.invoice_mode == 'once':   
                        values.update({
                            'sale_amount': line.price_subtotal,
                        })
                        obj_account_analytic_line.create(cr,uid,values)
                        obj_sale_order_line.write(cr, uid, [line.id], {'analytic_created': True})
                    elif line.invoice_mode == 'installments':
                        amount = line.price_subtotal / line.installments
                        values.update({
                            'sale_amount': amount,
                        })
                        if line.installment_unit == 'days':
                            increment_size = DateTime.RelativeDateTime(days=1)
                        elif line.installment_unit == 'weeks':
                            increment_size = DateTime.RelativeDateTime(days=7)
                        elif line.installment_unit == 'months':
                            increment_size = DateTime.RelativeDateTime(months=1)
                        elif line.installment_unit == 'years':
                            increment_size = DateTime.RelativeDateTime(months=12)
                        cont = line.installments
                        while cont > 0:
                            obj_account_analytic_line.create(cr,uid,values)
                            next_date = DateTime.strptime(values['date'], '%Y-%m-%d') + increment_size
                            values.update({
                                'date': next_date.strftime('%Y-%m-%d'),
                            })
                            cont-=1
                        obj_sale_order_line.write(cr, uid, [line.id], {'analytic_created': True})    
                    elif line.invoice_mode == 'recur' and not order.agreement:
                        values = {
                            'partner_id': order.partner_id.id,
                            'service': line.product_id.recur_service.id,
                            'signed_date': line.invoice_date,
                            'cur_effect_date': line.expire_date,
                            'partner_signed_date': line.partner_signed_date or line.invoice_date,
                            'analytic_account': analytic_account,
                            'payment': line.payment,
                            'recurr_unit_number': line.interval,
                            'recurr_unit': line.interval_unit,
                            'period_unit_number': line.period,
                            'period_unit': line.period_unit,
                        }
                        id = obj_agreement.create(cr, uid, values)
                        self.write(cr, uid, [order.id], {'agreement': id})
                        obj_agreement.get_number(cr, uid, [id])
                        obj_agreement.set_process(cr, uid, [id])
        return res
sale_order()
