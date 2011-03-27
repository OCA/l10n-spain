# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
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

"""
C43 format concepts and extension of the bank statement lines.
"""

from osv import osv, fields
import tools
import os
from tools.translate import _
from xml.dom import minidom



class l10n_es_extractos_import_wizard(osv.osv_memory):
    """
    Wizard to import the XML file defining the statement concepts (concepto)
    """

    def _get_available_user_companies(self, cr, uid, context={}):
        """
            Obtiene la compañía del usuario activo
        """
        current_user = self.pool.get('res.users').browse(cr,uid,uid)
        result = [x.id for x in current_user.company_ids]
        return result

    def action_import(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context):
            concept_obj = self.pool.get('l10n.es.extractos.concepto')
            account_obj = self.pool.get('account.account')
            concept_ids_list = []
            root_uid = 1
            company_concepts = concept_obj.browse(cr, root_uid, concept_obj.search(cr, root_uid, [('company_id','=', wiz.company_id.id)]))
            all_concepts = concept_obj.browse(cr, root_uid, concept_obj.search(cr, root_uid, []))
            if company_concepts:
                raise osv.except_osv(_("Info:"), _("Concepts for this company already imported..."))
            elif all_concepts:
                #Duplicamos los de una compañia (controlando que los planes contables no tengan el mismo numero de digitos) y asignamos nueva compañía
                any_concepts = concept_obj.browse(cr, root_uid, concept_obj.search(cr, root_uid,[('company_id','=', all_concepts[0].company_id.id)]))
                for concept in any_concepts:
                    account_code = "%s%%00"%(concept.account_id.code[0:4])
                    company_account_id = account_obj.search(cr, root_uid, [('company_id','=',wiz.company_id.id), ('code','like',account_code)])
                    company_account_id = company_account_id and company_account_id[0] or False
                    vals_concept = {
                        'name': concept.name,
                        'code': concept.code,
                        'account_id': company_account_id,
                        'company_id': wiz.company_id.id
                    }
                    concept_id = concept_obj.create(cr,uid, vals_concept)
                    concept_ids_list.append(concept_id)

                #Devolvemos la vista lista de los conceptos creados...
                concept_view_list_id = self.pool.get('ir.ui.view').search(cr, root_uid, [('name', '=', 'l10n.es.extractos.concepto.tree')])[0]
                return {
                    'name' : _('C43 Created Concepts'),
                    'type' : 'ir.actions.act_window',
                    'res_model' : 'l10n.es.extractos.concepto',
                    'view_type' : 'form',
                    'view_mode' : 'tree,form',
                    'domain' : "[('id', 'in', %s)]" % concept_ids_list,
                    'view_id' : False,
                    'views': [(concept_view_list_id, 'tree'), (False, 'form'), (False, 'calendar'), (False, 'graph')],
                }

            else:
                #Creamos nuevos registros...
                data = [
                    ('01', _('Reintegro/Talón'), '4300%00'),
                    ('02', _('Ingreso/Abonaré'), '4100%00'),
                    ('03', _('Recibo/Letra domiciliado'), '4100%00'),
                    ('04', _('Transf./Giro/Cheque'), '4300%00'),
                    ('05', _('Amortización préstamo'), '6800%00'),
                    ('06', _('Remesa efectos'), '4010%00'),
                    ('07', _('Subscripción/Canje'), '5700%00'),
                    ('08', _('Amortización'), '6800%00'),
                    ('09', _('Compra/Venta valores'), '2510%00'),
                    ('10', _('Cheque gasolina'), '5700%00'),
                    ('11', _('Cajero automático'), '5700%00'),
                    ('12', _('Tarjeta crédito/débito'), '5700%00'),
                    ('13', _('Operaciones extranjero'), '5730%00'),
                    ('14', _('Devolución/Impagado'), '4300%00'),
                    ('15', _('Nómina/Seg. social'), '6400%00'),
                    ('16', _('Timbre/Corretaje/Póliza'), '6690%00'),
                    ('17', _('Intereses/Comisión/Gastos/Custodia'), '6690%00'),
                    ('98', _('Anulación/Corrección'), '5720%00'),
                    ('99', _('Varios'), '5720%00'),
                ]
                concept_ids = []
                for item in data:

                    account_ids = self.pool.get('account.account').search(cr, uid, [
                        ('company_id', '=', wiz.company_id.id),
                        ('code', 'like', item[2]),
                    ], context=context)
                    if not account_ids:
                        raise osv.except_osv(_('Import Error'), _('Could not import concept %(concept)s because no matching account was found for expression %(expression)s.') % {
                            'concept': item[0],
                            'expression': item[2],
                        })

                    concept_id = self.pool.get('l10n.es.extractos.concepto').create(cr, uid, {
                        'code': item[0],
                        'name': item[1],
                        'account_id': account_ids[0],
                        'company_id': wiz.company_id.id,
                    }, context)

                    concept_ids.append( concept_id )
			

                #Devolvemos la vista lista de los usuarios modificados...
                concept_view_list_id = self.pool.get('ir.ui.view').search(cr, root_uid, [('name', '=', 'l10n.es.extractos.concepto.tree')])[0]
                return {
                    'name' : _('C43 Created Concepts'),
                    'type' : 'ir.actions.act_window',
                    'res_model' : 'l10n.es.extractos.concepto',
                    'view_type' : 'form',
                    'view_mode' : 'tree,form',
                    'view_id' : False,
                    'views': [(concept_view_list_id, 'tree'), (False, 'form'), (False, 'calendar'), (False, 'graph')],
                    'domain': [('id', 'in', concept_ids)]
                }

    _name = 'l10n.es.extractos.import.wizard'

    _columns = {
        'company_id': fields.many2one('res.company', _('Company'), required=True, context={'user_preference': True})
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self._get_available_user_companies(cr, uid, context),
    }

l10n_es_extractos_import_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
