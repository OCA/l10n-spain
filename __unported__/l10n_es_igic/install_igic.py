# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Omar Castiñeira Saavedra$
#
#   This program is free software: you can redistribute it and/or modify
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv


class wizard_update_charts_accounts(osv.osv_memory):

    _name = "wizard.update.charts.accounts.todo"
    _inherit = ["res.config.installer", "wizard.update.charts.accounts"]

    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.action_find_records(cr, uid, ids, context=context)
        self.action_update_records(cr, uid, ids, context=context)

wizard_update_charts_accounts()


class install_igic(osv.osv_memory):

    _name = "install.igic"
    _inherit = 'res.config.installer'

    def _get_chart(self, cr, uid, context=None):
        """
        Returns the default chart template.
        """
        if context is None:
            context = {}
        ids = self.pool.get('account.chart.template').search(
            cr, uid, [], context=context)
        if ids:
            return ids[0]
        return False

    def _get_purchase_tax(self, cr, uid, context=None):
        ids = self.pool.get('account.chart.template').search(
            cr, uid, [], context=context)
        if ids:
            purchase_tax_ids = self.pool.get('account.tax').search(cr, uid, [(
                'parent_id', '=', False), ('type_tax_use', 'in', ('purchase', 'all'))], order="sequence")
            return purchase_tax_ids and purchase_tax_ids[0] or False
        return False

    def _get_sale_tax(self, cr, uid, context=None):
        ids = self.pool.get('account.chart.template').search(
            cr, uid, [], context=context)
        if ids:
            sale_tax_ids = self.pool.get('account.tax').search(cr, uid, [(
                'parent_id', '=', False), ('type_tax_use', 'in', ('sale', 'all'))], order="sequence")
            return sale_tax_ids and sale_tax_ids[0] or False
        return False

    _columns = {
        'purchase_tax': fields.many2one("account.tax", "Default Supplier Tax"),
        'sale_tax': fields.many2one("account.tax", "Default Sale Tax"),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'chart_template_id': fields.many2one('account.chart.template', 'Chart Template', required=True),
        'code_digits': fields.integer('# of Digits', required=True, help="No. of Digits to use for account code. Make sure it is the same number as existing accounts."),
        'rename_fiscal_position': fields.boolean('Rename fiscal position', help="Rename National Fiscal Position to Canary Fiscal Position, if you doesn't mark this checkbox it will create new fiscal position for Canary.")
    }

    _defaults = {
        'rename_fiscal_position': True,
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, [uid], context)[0].company_id.id,
        'chart_template_id': _get_chart,
        'sale_tax': _get_sale_tax,
        'purchase_tax': _get_purchase_tax,
    }

    def _get_code_digits(self, cr, uid, context=None, company_id=None):
        """
        Returns the default code size for the accounts.

        To figure out the number of digits of the accounts it look at the
        code size of the default receivable account of the company
        (or user's company if any company is given).
        """
        if context is None:
            context = {}
        property_obj = self.pool.get('ir.property')
        account_obj = self.pool.get('account.account')
        if not company_id:
            user = self.pool.get('res.users').browse(cr, uid, uid, context)
            company_id = user.company_id.id
        property_ids = property_obj.search(cr, uid, [('name', '=', 'property_account_receivable'), (
            'company_id', '=', company_id), ('res_id', '=', False), ('value_reference', '!=', False)])
        if not property_ids:
            # Try to get a generic (no-company) property
            property_ids = property_obj.search(cr, uid, [(
                'name', '=', 'property_account_receivable'), ('res_id', '=', False), ('value_reference', '!=', False)])
        number_digits = 6
        if property_ids:
            prop = property_obj.browse(
                cr, uid, property_ids[0], context=context)
            try:
                # OpenERP 5.0 and 5.2/6.0 revno <= 2236
                account_id = int(prop.value_reference.split(',')[1])
            except AttributeError:
                # OpenERP 6.0 revno >= 2236
                account_id = prop.value_reference.id

            if account_id:
                code = account_obj.read(
                    cr, uid, account_id, ['code'], context)['code']
                number_digits = len(code)
        return number_digits

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        """
        Update the code size when the company changes
        """
        res = {
            'value': {
                'code_digits': self._get_code_digits(cr, uid, context=context, company_id=company_id),
            }
        }
        return res

    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        super(install_igic, self).execute(cr, uid, ids, context=context)
        obj = self.browse(cr, uid, ids)[0]
        ir_values = self.pool.get('ir.values')
        if obj.sale_tax:
            value_ids = ir_values.search(cr, uid, [(
                'key', '=', 'default'), ('name', '=', "taxes_id"), ('company_id', '=', obj.company_id.id)])
            ir_values.unlink(cr, uid, value_ids)
            ir_values.set(cr, uid, key='default', key2=False, name="taxes_id", company=obj.company_id.id,
                          models=[('product.product', False)], value=[obj.sale_tax.id])
        if obj.purchase_tax:
            value_ids = ir_values.search(cr, uid, [(
                'key', '=', 'default'), ('name', '=', "supplier_taxes_id"), ('company_id', '=', obj.company_id.id)])
            ir_values.unlink(cr, uid, value_ids)
            ir_values.set(cr, uid, key='default', key2=False, name="supplier_taxes_id", company=obj.company_id.id,
                          models=[('product.product', False)], value=[obj.purchase_tax.id])

        if obj.rename_fiscal_position:
            fp_ids = self.pool.get('account.fiscal.position').search(
                cr, uid, [('name', '=', u'Régimen Nacional'), ('company_id', '=', obj.company_id.id)])
            if fp_ids:
                self.pool.get('account.fiscal.position').write(
                    cr, uid, fp_ids, {'name': u'Régimen Canario'})


install_igic()
