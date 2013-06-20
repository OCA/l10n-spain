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
import time
import datetime
import pooler

class wizard_pagar_anticipo(osv.osv_memory):
    
    _name = 'wizard.pagar.anticipo'
    _description = 'Wizard para pagar anticipos'
    
    _columns={
        #'anticipos_ids': {'string': 'Anticipos', 'type': 'many2many', 'relation': 'hr.anticipo', 'required': True},
        'anticipos_ids': fields.many2many('hr.anticipo','rel_anticipos_p','nomina_id','anticipos_id')
              }
    
    def pagar_anticipos(self, cr, uid, ids, context):
        #########################################################################
        # OBJETOS
        #########################################################################
        nominas_obj = self.pool.get ('hr.employee')
        anticipos_obj = self.pool.get ('hr.anticipo')
        #########################################################################
        pool = pooler.get_pool(cr.dbname)

        anticipo_list = []
        for ant_id in self.browse(cr, uid, ids[0], context).anticipos_ids:
            anticipo_list.append(ant_id.id)
            
        anticipos_obj.pagar_anticipo(cr, uid, anticipo_list)
            
        return {'type': 'ir.actions.act_window_close'}
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'} 
            
wizard_pagar_anticipo()

class wizard_confirmar_anticipo(osv.osv_memory):
    
    _name = 'wizard.confirmar.anticipo'
    _description = 'Wizard confirmar anticipos'
    
    _columns={
        #'anticipos_ids': {'string': 'Anticipos', 'type': 'many2many', 'relation': 'hr.anticipo', 'required': True},
        'anticipos_ids': fields.many2many('hr.anticipo','rel_anticipos_c','nomina_id','anticipos_id'),
              }

    def confirmar_anticipos(self, cr, uid, ids, context):
        #########################################################################
        # OBJETOS
        #########################################################################
        anticipos_obj = self.pool.get('hr.anticipo')
        #########################################################################
        anticipo_list = []
        for ant_id in self.browse(cr, uid, ids[0], context).anticipos_ids:
            anticipo_list.append(ant_id.id)
            
        anticipos_obj.confirmar_anticipo(cr, uid, anticipo_list, context)
            
        return {'type': 'ir.actions.act_window_close'}
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'} 

wizard_confirmar_anticipo()