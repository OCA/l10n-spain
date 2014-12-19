# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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
from collections import defaultdict


class account_tax(orm.Model):

    _inherit = 'account.tax'

    def _allowed_pct_by_ledger(self, cr, uid, context=None):
        tax_obj = self.pool.get('account.tax')
        res = defaultdict(set)
        tax_ids = tax_obj.search(cr, uid, [('ledger_key','!=',False)], context=context)
        for tax in tax_obj.browse(cr, uid, tax_ids, context):
            res[tax.ledger_key].add(abs(tax.amount))
        return res

    def get_operation_keys(self, cr, uid, context=None):
        return [('-', u'Recargo de equivalencia'),
                (' ', u'Operación habitual'),
                ('F', u'F-Adquisiciones realizadas por las agencias de viajes directamente en interés del viajero (Régimen especial de agencias de viajes)'),
                ('H', u'H-Régimen especial de oro de inversión'),
                ('I', u'I-Inversión del Sujeto pasivo (ISP)'),
                ('J', u'J-Tiques / Factura simplificada'),
                ('L', u'L-Adquisiciones a comerciantes minoristas del IGIC'),
                ('N', u'N-Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras en nombre y por cuenta ajena'),
                ('P', u'P-Adquisiciones intracomunitarias de bienes.'),
                ('Q', u'Q-Operaciones a las que se aplique el Régimen especial de bienes usados, objetos de arte, antigüedades y objetos de colección'),
                ('R', u'R-Operación de arrendamiento de local de negocio'),
                ('S', u'S-Subvenciones, auxilios o ayudas satisfechas o recibidas, tanto por parte de Administraciones públicas como de entidades privadas'),
                ('V', u'V-Compras de Agencias viajes'),
                ('W', u'W-Operaciones sujetas al Impuesto sobre la Producción, los Servicios y la Importación en las Ciudades de Ceuta y Melilla'),
                ('X', u'X-Operaciones por las que los empresarios o profesionales que satisfagan compensaciones agrícolas, ganaderas y/o pesqueras hayan expedido el recibo correspondiente'),]

    def _get_operation_keys(self, cr, uid, context=None):
        return self.get_operation_keys(cr, uid, context=context)

    def get_ledger_keys(self, cr, uid, context=None):
        return [('E', u'E-Libro registro de facturas expedidas.'),
                ('F', u'F-Libro registro de facturas expedidas IGIC.'),
                ('R', u'R-Libro registro de facturas recibidas.'),
                ('I', u'I-Libro registro de bienes de inversión.'),
                ('J', u'J-Libro de registro de bienes de inversión IGIC.'),
                ('S', u'S-Libro de registro de facturas recibidas IGIC.'),
                ('U', u'U-Libro registro de determinadas operaciones intracomunitarias.')]

    def _get_ledger_keys(self, cr, uid, context=None):
        return self.get_ledger_keys(cr, uid, context=context)

    def get_ledger_keys_out(self, cr, uid, context=None):
        return [('E', u'E-Libro registro de facturas expedidas.'),
                ('F', u'F-Libro registro de facturas expedidas IGIC.'),
                ('U', u'U-Libro registro de determinadas operaciones intracomunitarias.')]

    def _get_ledger_keys_out(self, cr, uid, context=None):
        return self.get_ledger_keys_out(cr, uid, context=context)

    def get_ledger_keys_in(self, cr, uid, context=None):
        return [('R', u'R-Libro registro de facturas recibidas.'),
                ('I', u'I-Libro registro de bienes de inversión.'),
                ('J', u'J-Libro de registro de bienes de inversión IGIC.'),
                ('S', u'S-Libro de registro de facturas recibidas IGIC.'),
                ('U', u'U-Libro registro de determinadas operaciones intracomunitarias.')]

    def _get_ledger_keys_in(self, cr, uid, context=None):
        return self.get_ledger_keys_in(cr, uid, context=context)

    def _calc_ledger(self, cr, uid, ids, field_names, arg, context=None):
        res = dict.fromkeys(ids, {})
        for tax in self.browse(cr, uid, ids, context):
            res[tax.id]['ledger_key_out'] = False
            res[tax.id]['ledger_key_in'] = False
            if tax.type_tax_use == "purchase":
                res[tax.id]['ledger_key_in'] = tax.ledger_key
            elif tax.type_tax_use == "sale":
                res[tax.id]['ledger_key_out'] = tax.ledger_key
        return res

    def _set_ledger(self, cr, uid, ids, field_names, field_value, arg, context):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        taxes = self.browse(cr, uid, ids, context)
        for field in field_names:
            if field == "ledger_key_in":
                self.write(cr, uid, [tax.id for tax in taxes if tax.type_tax_use in ('purchase', 'all')], {'ledger_key': field_value}, context)
            else:
                self.write(cr, uid, [tax.id for tax in taxes if tax.type_tax_use in ('sale', 'all')], {'ledger_key': field_value}, context)

    def onchange_ledger(self, cr, uid, ids, field, key, context=None):
        value = {
            'ledger_key': key
        }
        return {'value': value}

    def onchange_type_tax_use(self, cr, uid, ids, context=None):
        value = {
            'ledger_key': False,
            'ledger_key_in': False,
            'ledger_key_out': False
        }
        return {'value': value}

    _columns = {
        'operation_key': fields.selection(_get_operation_keys, 'Operation Key'),
        'ledger_key': fields.selection(_get_ledger_keys, 'Ledger Key', help="Determines to which ledger the invoice with this tax will be assigned. Setting a value makes the tax to be accounted in 340 declaration"),
        'ledger_key_in': fields.function(_calc_ledger, type="selection", fnct_inv=_set_ledger, selection=_get_ledger_keys_in, string='Ledger Key', multi="ledger",
                                         help="Determines to which ledger the invoice with this tax will be assigned. Setting a value makes the tax to be accounted in 340 declaration"),
        'ledger_key_out': fields.function(_calc_ledger, type="selection", fnct_inv=_set_ledger, selection=_get_ledger_keys_out, string='Ledger Key', multi="ledger",
                                          help="Determines to which ledger the invoice with this tax will be assigned. Setting a value makes the tax to be accounted in 340 declaration"),
    }


class account_tax_template(orm.Model):
    _inherit = 'account.tax.template'

    def _get_ledger_keys(self, cr, uid, context=None):
        return self.pool.get('account.tax').get_ledger_keys(cr, uid, context=context)

    def _get_operation_keys(self, cr, uid, context=None):
        return self.pool.get('account.tax').get_operation_keys(cr, uid, context=context)

    _columns = {
        'operation_key': fields.selection(_get_operation_keys, 'Operation Key'),
        'ledger_key': fields.selection(_get_ledger_keys, 'Ledger Key'),
    }


class account_tax_code(orm.Model):
    _inherit = 'account.tax.code'

    def _calc_mod340(self, cr, uid, ids, name, args, context=None):
        tax_obj = self.pool.get('account.tax')
        res = {}
        for tax in self.browse(cr, uid, ids, context=context):
            res[tax.id] = len(tax_obj.search(cr, uid, [('base_code_id','=',tax.id),('ledger_key','!=',False)], context=context)) > 0
        return res

    def _get_code_affected_by_tax(self, cr, uid, ids, context=None):
        code_ids = set()
        for tax in self.pool.get('account.tax').browse(cr, uid, ids, context=context):
            code_ids.add(tax.base_code_id.id)
        return list(code_ids)

    _columns = {
        'mod340': fields.function(_calc_mod340, type="boolean", string="Include in mod340",
                                  store={
                                        'account.tax': (_get_code_affected_by_tax, ['base_code_id', 'ledger_key'], 10),
                                  })
    }


class wizard_update_charts_accounts(orm.TransientModel):
    _inherit = 'wizard.update.charts.accounts'

    def _find_taxes(self, cr, uid, wizard, chart_template_ids, context=None):
        """
        En caso de actualizar impuestos, añade a los impuestos modificados los que
        tengan claves de operación o libro distintas de sus plantillas
        """
        tax_obj = self.pool['account.tax']
        tax_templ_obj = self.pool['account.tax.template']
        wiz_taxes_obj = self.pool['wizard.update.charts.accounts.tax']
        res = super(wizard_update_charts_accounts, self)._find_taxes(cr, uid, wizard, chart_template_ids, context)

        if not wizard.update_tax:
            return res
        updated_taxes = res['updated']
        tax_templ_mapping = res['mapping']
        tax_templ_ids = tax_templ_obj.search(cr, uid,
                                            [('chart_template_id',
                                              'in',
                                              chart_template_ids)],
                                            context=context)

        for tax_templ in tax_templ_obj.browse(cr, uid, tax_templ_ids,
                                              context=context):

            tax_id = self._map_tax_template(cr, uid, wizard,
                                            tax_templ_mapping,
                                            tax_templ, context=context)

            if not tax_id:
                continue

            modified = False
            notes = ""
            tax = tax_obj.browse(cr, uid, tax_id, context=context)
            if tax.operation_key != tax_templ.operation_key:
                notes += _("The operation key is different.\n")
                modified = True
            if tax.ledger_key != tax_templ.ledger_key:
                notes += _("The ledger key is different.\n")
                modified = True
            if modified:
                wiz_tax_id = wiz_taxes_obj.search(cr, uid, [('update_chart_wizard_id','=',wizard.id),('update_tax_id','=',tax.id)], context=context)
                if wiz_tax_id:
                    wiz_tax_line = wiz_taxes_obj.browse(cr, uid, wiz_tax_id[0], context)
                    wiz_taxes_obj.write(cr, uid, wiz_tax_line.id, {'notes': wiz_tax_line.notes + notes}, context)
                else:
                    updated_taxes += 1
                    wiz_taxes_obj.create(cr, uid, {
                        'tax_id': tax_templ.id,
                        'update_chart_wizard_id': wizard.id,
                        'type': 'updated',
                        'update_tax_id': tax_id,
                        'notes': notes,
                    }, context)

        res['updated'] = updated_taxes
        return res

    def _update_taxes(self, cr, uid, wizard, log, tax_code_template_mapping, context=None):
        """
        Vuelve a reprocesar las líneas de impuestos para actualizar las claves de operación y libro
        """
        res = super(wizard_update_charts_accounts, self)._update_taxes(cr, uid, wizard, log, tax_code_template_mapping, context)
        taxes = self.pool['account.tax']

        if not wizard.update_tax:
            return res

        for wiz_tax in wizard.tax_ids:
            tax_template = wiz_tax.tax_id

            vals_tax = {
                'operation_key': tax_template.operation_key,
                'ledger_key': tax_template.ledger_key
            }

            if wiz_tax.type == 'updated' and wiz_tax.update_tax_id:
                taxes.write(cr, uid, [wiz_tax.update_tax_id.id], vals_tax)
#                 log.add(_("mod340: Updated tax %s.\n") % tax_template.name)

        # No necesitamos llevar control de taxes_pending_for_accounts ni detectar errores, ya lo hizo super
        return res

