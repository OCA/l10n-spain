# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv


class l10n_cat_account_wizard(osv.osv_memory):

    """Translate the account templates from Spanish to Catalan"""
    _name = "l10n_cat_account.wizard"

    _columns = {
        'name': fields.char('Name', size=64),
    }

    def action_translate(self, cr, uid, ids, context=None):
        """Translates the names of account templates"""
        if context == None:
            context = {}
        from .chart_of_accounts import chart_of_accounts
        account_template_obj = self.pool.get('account.account.template')
        for a in chart_of_accounts:
            # In v6.0 the account.account.templates don't have a template name, so we can't filter them
            # ids = account_template_obj.search(cr, uid, [('code', '=', a[0]),('template_name','like','PGCE %')])
            ids = account_template_obj.search(cr, uid, [('code', '=', a[0])])
            if ids:
                account_template_obj.write(cr, uid, ids, {'name': a[1], })
        return {}

    def action_skip(self, cr, uid, ids, context=None):
        """Skips the account template translation wizard"""
        if context == None:
            context = {}
        todo_obj = self.pool.get('ir.actions.todo')
        ids = todo_obj.search(
            cr, uid, [('name', '=', 'Account templates from Spanish to Catalan')])
        if ids:
            todo_obj.write(cr, uid, ids, {'state': 'skip', })
        return {}

l10n_cat_account_wizard()
