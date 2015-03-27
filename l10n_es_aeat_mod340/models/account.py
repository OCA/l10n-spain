# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountTaxCodeTemplate(orm.Model):
    _inherit = 'account.tax.code.template'

    _columns = {
        'mod340': fields.boolean("Include in mod340"),
    }


class AccountTaxCode(orm.Model):
    _inherit = 'account.tax.code'

    _columns = {
        'mod340': fields.boolean("Include in mod340"),
    }


class WizardUpdateChartsAccounts(orm.TransientModel):
    _inherit = 'wizard.update.charts.accounts'

    def _find_tax_codes(self, cr, uid, wizard, chart_template_ids,
                        context=None):
        """Search for, and load, tax code templates to create/update.

        @param chart_template_ids: IDs of the chart templates to look on,
            calculated once in the calling method.
        """
        if not wizard.chart_template_id:
            return {}
        new_tax_codes = 0
        updated_tax_codes = 0
        tax_code_template_mapping = {}
        tax_code_templ_obj = self.pool['account.tax.code.template']
        tax_code_obj = self.pool['account.tax.code']
        wiz_tax_code_obj = self.pool['wizard.update.charts.accounts.tax.code']
        # Remove previous tax codes
        wiz_tax_code_obj.unlink(cr, uid, wiz_tax_code_obj.search(cr, uid, []))
        # Search for new / updated tax codes
        root_tax_code_id = wizard.chart_template_id.tax_code_root_id.id
        children_tax_code_template = tax_code_templ_obj.search(cr, uid, [(
            'parent_id', 'child_of', [root_tax_code_id])], order='id',
            context=context)
        for tax_code_template in tax_code_templ_obj.browse(
                cr, uid, children_tax_code_template, context=context):
            # Ensure the tax code template is on the map (search for the mapped
            # tax code id).
            tax_code_id = self._map_tax_code_template(
                cr, uid, wizard, tax_code_template_mapping, tax_code_template,
                context=context)
            if not tax_code_id:
                new_tax_codes += 1
                wiz_tax_code_obj.create(cr, uid, {
                    'tax_code_id': tax_code_template.id,
                    'update_chart_wizard_id': wizard.id,
                    'type': 'new',
                    'notes': _('Name or code not found.'),
                }, context)
            elif wizard.update_tax_code:
                # Check the tax code for changes.
                modified = False
                notes = ""
                tax_code = tax_code_obj.browse(
                    cr, uid, tax_code_id, context=context)
                if tax_code.code != tax_code_template.code:
                    notes += _("The code field is different.\n")
                    modified = True
                if tax_code.info != tax_code_template.info:
                    notes += _("The info field is different.\n")
                    modified = True
                if tax_code.sign != tax_code_template.sign:
                    notes += _("The sign field is different.\n")
                    modified = True
                if tax_code.mod340 != tax_code_template.mod340:
                    notes += _("The Mod 340 field is different.\n")
                    modified = True
                # TODO: We could check other account fields for changes...
                if modified:
                    # Tax code to update.
                    updated_tax_codes += 1
                    wiz_tax_code_obj.create(cr, uid, {
                        'tax_code_id': tax_code_template.id,
                        'update_chart_wizard_id': wizard.id,
                        'type': 'updated',
                        'update_tax_code_id': tax_code_id,
                        'notes': notes,
                    }, context)
        return {
            'new': new_tax_codes,
            'updated': updated_tax_codes,
            'mapping': tax_code_template_mapping
        }

    def _update_tax_codes(self, cr, uid, wizard, log, context=None):
        """
        Search for, and load, tax code templates to create/update.
        """
        tax_code_obj = self.pool['account.tax.code']
        root_tax_code_id = wizard.chart_template_id.tax_code_root_id.id
        new_tax_codes = 0
        updated_tax_codes = 0
        tax_code_template_mapping = {}
        for wiz_tax_code in wizard.tax_code_ids:
            tax_code_template = wiz_tax_code.tax_code_id
            tax_code_name = ((root_tax_code_id == tax_code_template.id) and
                             wizard.company_id.name or
                             tax_code_template.name)
            # Ensure the parent tax code template is on the map.
            self._map_tax_code_template(cr, uid, wizard,
                                        tax_code_template_mapping,
                                        tax_code_template.parent_id,
                                        context=context)
            # Values
            vals = {
                'name': tax_code_name,
                'code': tax_code_template.code,
                'info': tax_code_template.info,
                'parent_id': (tax_code_template.parent_id and
                              tax_code_template_mapping.get(
                                  tax_code_template.parent_id.id)),
                'company_id': wizard.company_id.id,
                'sign': tax_code_template.sign,
                'mod340': tax_code_template.mod340
            }
            tax_code_id = None
            modified = False
            if wiz_tax_code.type == 'new':
                # Create the tax code
                tax_code_id = tax_code_obj.create(cr, uid, vals,
                                                  context=context)
                log.add(_("Created tax code %s.\n") % tax_code_name)
                new_tax_codes += 1
                modified = True
            elif wizard.update_tax_code and wiz_tax_code.update_tax_code_id:
                # Update the tax code
                tax_code_id = wiz_tax_code.update_tax_code_id.id
                tax_code_obj.write(cr, uid, [tax_code_id], vals)
                log.add(_("Updated tax code %s.\n") % tax_code_name)
                updated_tax_codes += 1
                modified = True
            else:
                tax_code_id = wiz_tax_code.update_tax_code_id and \
                    wiz_tax_code.update_tax_code_id.id
                modified = False
            # Store the tax codes on the map
            tax_code_template_mapping[tax_code_template.id] = tax_code_id
            if modified:
                # Detect errors
                if tax_code_template.parent_id and not \
                        tax_code_template_mapping.get(
                        tax_code_template.parent_id.id):
                    log.add(
                        _("Tax code %s: The parent tax code %s can not be "
                          "set.\n")
                        % (tax_code_name, tax_code_template.parent_id.name),
                        True)
        return {
            'new': new_tax_codes,
            'updated': updated_tax_codes,
            'mapping': tax_code_template_mapping
        }

