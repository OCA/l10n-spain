# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2010 Zikzakmedia S.L. (http://zikzakmedia.com)
#                            Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010-2010 NaN-Tic (http://www.nan-tic.com)
#                            Albert Cervera
#    Copyright (c) 2013
#        Joan M. Grande <totaler@gmail.com> All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

"""
Extensión de los objetos plantilla contable (cuentas, impuestos y otros),
para añadir un campo con el nombre de la plantilla en si (para poder
diferenciar entre PGCE 2008 y PGCE PYMES).
"""

from openerp.osv import fields, orm


class account_account(orm.Model):
    _inherit = "account.account"

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        """Improves the search of accounts using a dot to fill the zeroes
        (like 43.27 to search account 43000027)"""
        args = args[:]
        pos = 0
        while pos < len(args):
            if (args[pos][0] == 'code' and
                    args[pos][1] in ('like', 'ilike', '=like') and
                    args[pos][2]):
                query = args[pos][2].replace('%', '')
                if '.' in query:
                    query = query.partition('.')
                    cr.execute("""SELECT id FROM account_account
                                WHERE type <> 'view'
                                AND code ~ ('^' || %s || '0+' || %s || '$')""",
                               (query[0], query[2]))
                    ids = [x[0] for x in cr.fetchall()]
                    if ids:
                        args[pos] = ('id', 'in', ids)
            pos += 1
        return super(account_account, self).search(cr, uid, args,
                                                   offset, limit, order,
                                                   context, count)


class account_account_template(orm.Model):

    """Extends the account template to add the chart
    template that the account belongs"""

    def _get_chart_template(self, cr, uid, ids, field_name, arg, context=None):
        """To get the chart template from an account template,
        we have to search recursively across its parent_id field
        until parent_id is null (this is the root account) then
        select the chart template which have 'account_root_id'
        pointing to the root account."""

        chart_obj = self.pool.get('account.chart.template')
        if context is None:
            context = {}
        res = {}
        accounts = self.browse(cr, uid, ids)
        for account in accounts:
            id = account.id
            while account.parent_id:
                account = self.browse(cr, uid, account.parent_id.id)
            search_params = [('account_root_id', '=', account.id)]
            template_ids = chart_obj.search(cr, uid, search_params,
                                            context=context)
            res[id] = template_ids and template_ids[0] or False

        return res

    def _get_account_from_chart(self, cr, uid, ids, context=None):
        """If 'account_root_id' is changed from a chart template, we must
           recompute all accounts that are children"""
        chart_obj = self.pool.get('account.chart.template')
        acc_tmpl_obj = self.pool.get('account.account.template')
        if context is None:
            context = {}
        templates = chart_obj.browse(cr, uid, ids, context=context)
        account_root_ids = [t.account_root_id.id for t in templates]
        search_params = [('parent_id', 'child_of', account_root_ids)]
        res = acc_tmpl_obj.search(cr, uid, search_params, context=context)
        return res

    def _get_account_from_account(self, cr, uid, ids, context=None):
        """If 'parent_id' is changed from an account template, we must
           recompute all accounts that are children"""

        if context is None:
            context = {}

        search_params = [('parent_id', 'child_of', ids)]
        return self.search(cr, uid, search_params, context=context)

    _inherit = "account.account.template"
    _columns = {
        'chart_template_id': fields.function(
            _get_chart_template,
            method=True,
            string='Chart Template',
            type='many2one',
            obj='account.chart.template',
            store={
                'account.chart.template': (_get_account_from_chart,
                                           ['account_root_id'], 10),
                'account.account.template': (_get_account_from_account,
                                             ['parent_id'], 10),
            },
        ),
    }


class account_tax_code_template(orm.Model):

    """Extends the tax code template to add the chart
    template that the tax code belongs"""

    def _get_chart_template(self, cr, uid, ids, field_name, arg, context=None):
        """To get the chart template from a tax code template,
        we have to search recursively across its parent_id field
        until parent_id is null (this is the root tax code) then
        select the chart template which have 'tax_code_root_id'
        pointing to the root tax code."""
        chart_obj = self.pool.get('account.chart.template')
        if context is None:
            context = {}
        res = {}
        taxcodes = self.browse(cr, uid, ids)
        for taxcode in taxcodes:
            id = taxcode.id
            while taxcode.parent_id:
                taxcode = self.browse(cr, uid, taxcode.parent_id.id)
            search_params = [('tax_code_root_id', '=', taxcode.id)]
            template_ids = chart_obj.search(cr, uid, search_params,
                                            context=context)
            res[id] = template_ids and template_ids[0] or False
        return res

    def _get_taxcode_from_chart(self, cr, uid, ids, context=None):
        """If 'tax_code_root_id is changed from a chart template, we must
           recompute all tax codes that are children"""

        chart_obj = self.pool.get('account.chart.template')
        tcode_tmpl_obj = self.pool.get('account.tax.code.template')

        if context is None:
            context = {}
        templates = chart_obj.browse(cr, uid, ids, context=context)
        tax_code_root_ids = [t.tax_code_root_id.id for t in templates]
        search_params = [('parent_id', 'child_of', tax_code_root_ids)]
        res = tcode_tmpl_obj.search(cr, uid, search_params, context=context)
        return res

    def _get_taxcode_from_taxcode(self, cr, uid, ids, context=None):
        """If 'parent_id' is changed from a tax code template, we must
           recompute all tax codes that are children"""
        if context is None:
            context = {}
        search_params = [('parent_id', 'child_of', ids)]
        return self.search(cr, uid, search_params, context=context)

    _inherit = 'account.tax.code.template'
    _columns = {
        'chart_template_id': fields.function(
            _get_chart_template,
            method=True,
            string='Chart Template',
            type='many2one',
            obj='account.chart.template',
            store={
                'account.chart.template': (_get_taxcode_from_chart,
                                           ['tax_code_root_id'], 10),
                'account.tax.code.template': (_get_taxcode_from_taxcode,
                                              ['parent_id'], 10),
            },
        ),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
