# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2009 Ting! (<http://www.ting.es>). All Rights Reserved
#    Copyright (c) 2010 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Update to OpenERP 6.0 Ignacio Ibeas <ignacio@acysos.com> 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
#    $Id$
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
from osv import osv, fields
import wizard
import pooler


class wizard_confirmar_nominas(osv.osv_memory):
    
    _name = 'wizard.confirmar.nominas'
    _description = 'Para confirmar nominas'
    
    _columns={
        'nominas_ids': fields.many2many('hr.nomina','rel_nominas','antocipo_id','nomina_id',required = True),
              }

    def confirma_nominas(self, cr, uid, ids, context):
        ###############################################
        # OBJETOS
        ###############################################
        nomina_obj = self.pool.get('hr.nomina')
        ###############################################
        nom_list=[]
        for nom_id in self.browse(cr, uid, ids[0], context).nominas_ids:
            nom_list.append(nom_id.id)
        nomina_obj.confirmar_nomina(cr, uid,  nom_list)
        
        return {'type': 'ir.actions.act_window_close'} 
        
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'} 
            
wizard_confirmar_nominas()


class wizard_pagar_nominas(osv.osv_memory):
    
    _name = 'wizard.pagar.nominas'
    _description = 'Para pagar nominas'
    
    _columns={
         'nominas_ids': fields.many2many('hr.nomina','rel_nominas','antocipo_id','nomina_id',required = True)
              }

    def paga_nominas(self, cr, uid, ids, context):
        ###############################################
        # OBJETOS
        ###############################################
        nomina_obj = self.pool.get('hr.nomina')
        ###############################################
        nom_list=[]
        for nom_id in self.browse(cr, uid, ids[0], context).nominas_ids:
            nom_list.append(nom_id.id)
            
        #nomina_obj.pagar_nomina(self, cr, uid, nom_list)
        nomina_obj.pagar_nomina(cr, uid, nom_list)
        
        return {'type': 'ir.actions.act_window_close'}
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'} 

wizard_pagar_nominas()