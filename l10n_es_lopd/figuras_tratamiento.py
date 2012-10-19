# -*- coding: utf-8 -*-

from osv import fields, osv
import os

########################################################################################################
# Responsables de seguridad
########################################################################################################

class lopd_responsable(osv.osv):
	_name = 'lopd.responsable'
	_description = 'Responsable de seguridad'
	_columns = {
		'persona':fields.selection([('p_fis','Física'),('p_jur','Jurídica'),], '¿El responsable es una persona física o jurídica?', required= True),
		'name':fields.char('Nombre y Apellidos / Organización', size=140, Required = True),
		'domicilio': fields.char('Domicilio Social', size=100),
        'cp': fields.char('Código Postal', change_default=True, size=5),
        'localidad': fields.char('Localidad', size=50),
        'provincia': fields.many2one("res.country.state", 'Provincia', domain="[('country_id','=',pais)]"),
        'pais': fields.many2one('res.country', 'Pais'),    
        'tlf': fields.char('Teléfono', size=10),
        'fax': fields.char('Fax', size=10),
		'nif':fields.char('NIF / CIF', size=9, required = True),
		'cargo':fields.char('Cargo', size=70),
        'email': fields.char('E-Mail', size=70),
		'id_fichero':fields.many2many('lopd.fichero', 'lopd_rel_refi', 'id_re', 'id_fi', 'Ficheros'),
		'dataload':fields.boolean('¿Mantener datos de la empresa o asociación?', required=True)

	}
	def datos_empresa (self, cr, uid, ids, dato):
		datos = self.pool.get('res.partner.address').search(cr, uid, [('partner_id','=',1)])
		datos = self.pool.get('res.partner.address').read(cr, uid, datos[0], ['street','zip','localidad','city','state_id','country_id','phone','fax','email'])
		v = { 'domicilio':datos['street'], 'cp': datos['zip'], 'localidad':datos['city'], 'provincia': datos['state_id'], 'pais': datos['country_id'], 'tlf': datos['phone'], 'fax': datos['fax'], 'email': datos['email'],} 
		return { 'value':v }

lopd_responsable()
