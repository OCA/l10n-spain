# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Factor Libre All Rights Reserved.
#    #    $Id$
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

from osv import osv

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def write(self, cr, uid, ids, vals, context=None):
        """Modificación de método de escritura de res.partner para que se 
        produzca el cambio de las posiciones fiscales del partner automáticamente
        al realizar el guardado de los datos del mismo y en función de la dirección de
        facturación o de si tiene el CIF validado con VIES o no"""
       
        if context is None:
            context = {}
        if type(ids) != list:
            ids = [ids]
        domain = []
        #Buscamos la pos fiscal solamente si se cambia el valor al cif intracomunitario válido
        if 'valid_vies_vat' in vals:
            domain = [('vies_valid_vat','=',vals['valid_vies_vat'])]
        if 'vat' in vals and not vals['vat']:
            domain = [('vies_valid_vat','=',False)]
            
        config_fpos_obj = self.pool.get('config.fiscal.position')            
        partner_address_obj = self.pool.get('res.partner.address')
        for partner in self.browse(cr, uid, ids):
            fpos_ids = None               
            if not domain:
                domain = [('vies_valid_vat','=',partner.valid_vies_vat)]
            addr_ids = partner_address_obj.search(cr, uid, [('type','=','invoice'),
                                                            ('partner_id','=',partner.id)])            
            if addr_ids:
                address = partner_address_obj.browse(cr, uid, addr_ids[0])
                if address.country_id:
                    country_domain = list(domain)
                    country_domain.append(('country_ids','in',[address.country_id.id]))
                    fpos_ids = config_fpos_obj.search(cr, uid, country_domain)
                    if fpos_ids:
                        config_fpos = config_fpos_obj.browse(cr, uid, fpos_ids[0])                        
                        vals['vat_subjected'] = config_fpos.vat_subjected
                        vals['property_account_position'] = config_fpos.fpos.id
                    
                if address.state_id:
                    state_domain = list(domain)
                    state_domain.append(('state_ids','in',[address.state_id.id]))
                    fpos_ids = config_fpos_obj.search(cr, uid, state_domain)
                    if fpos_ids:
                        config_fpos = config_fpos_obj.browse(cr, uid, fpos_ids[0])                        
                        vals['vat_subjected'] = config_fpos.vat_subjected
                        vals['property_account_position'] = config_fpos.fpos.id

        return super(res_partner, self).write(cr, uid, ids, vals, context=context)
                    

res_partner()

class res_partner_address(osv.osv):
    _inherit = 'res.partner.address'
    
    def create(self, cr, uid, vals, context=None):
        """Modificación de método de creación de res.partner.address para que se 
        produzca el cambio de las posiciones fiscales del partner automáticamente
        al realizar la creación de una dirección de tipo factura"""
        config_fpos_obj = self.pool.get('config.fiscal.position')
        partner_obj = self.pool.get('res.partner')
        
        if 'partner_id' in vals:
            partner = partner_obj.browse(cr, uid, vals['partner_id'])
            domain = [('vies_valid_vat', '=', partner.valid_vies_vat)]            
            fpos_id = False
            config_fpos = None
            values = {}
            if 'type' in vals and vals['type'] == 'invoice':
                if 'country_id' in vals and vals['country_id']:
                    country_domain = list(domain)
                    country_domain.append(('country_ids','in',[vals['country_id']]))
                    fpos_ids = config_fpos_obj.search(cr, uid, country_domain)
                    if fpos_ids:
                        config_fpos = config_fpos_obj.browse(cr, uid, fpos_ids[0])
                        fpos_id = config_fpos.fpos.id
                
                if 'state_id' in vals and vals['state_id']:
                    state_domain = list(domain)
                    state_domain.append(('state_ids','in',[vals['state_id']]))
                    fpos_ids = config_fpos_obj.search(cr, uid, state_domain)
                    if fpos_ids:
                        config_fpos = config_fpos_obj.browse(cr, uid, fpos_ids[0])
                        fpos_id = config_fpos.fpos.id
                        
                if config_fpos:
                    values['vat_subjected'] = config_fpos.vat_subjected
            values['property_account_position'] = fpos_id
                    
            partner_obj.write(cr, uid, vals['partner_id'], values, context=context)
              
            return super(res_partner_address, self).create(cr, uid, vals, context=context)
            
    def write(self, cr, uid, ids, vals, context=None, update=True):
        """Modificación de método de escritura de res.partner.address para que se 
        produzca el cambio de las posiciones fiscales del partner automáticamente
        al realizar la modificación de datos de una dirección de tipo factura"""

        result = super(res_partner_address, self).write(cr, uid, ids, vals, context=context)        
        config_fpos_obj = self.pool.get('config.fiscal.position')
        partner_obj = self.pool.get('res.partner')
        if type(ids) == int:
            ids = [ids]              
        for addr in self.browse(cr, uid, ids, context=context):
            fpos_id = None
            config_fpos = None
            values = {}
            if addr.partner_id and addr.type == 'invoice':
                fpos_id = addr.partner_id.property_account_position.id
                domain = []
                #Vies en domain
                domain.append(('vies_valid_vat', '=', addr.partner_id.valid_vies_vat))
                if vals.get('country_id', False) and update:
                    country_domain = list(domain)
                    country_domain.append(('country_ids','in',[vals['country_id']]))                    
                    fpos_ids = config_fpos_obj.search(cr, uid, country_domain)
                    if fpos_ids:
                        config_fpos = config_fpos_obj.browse(cr, uid, fpos_ids[0])
                        fpos_id = config_fpos.fpos.id
                        
                if vals.get('state_id', False) and update:
                    state_domain = list(domain)
                    state_domain.append(('state_ids','in',[vals['state_id']]))
                    fpos_ids = config_fpos_obj.search(cr, uid, state_domain)
                    if fpos_ids:
                        config_fpos = config_fpos_obj.browse(cr, uid, fpos_ids[0])
                        fpos_id = config_fpos.fpos.id
                        
                if config_fpos:
                    values['vat_subjected'] = config_fpos.vat_subjected
                values['property_account_position'] = fpos_id
                
                partner_obj.write(cr, uid, addr.partner_id.id, values, context=context)

        return result
        
res_partner_address()
