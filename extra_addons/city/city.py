#!/usr/bin/env python
# -*- coding: utf-8 -*-

from osv import osv, fields
import wizard
import pooler

class city(osv.osv):

	def name_get(self, cr, uid, ids, context=None):
		if not len(ids):
			return []
		res = []
		for line in self.browse(cr, uid, ids):
			state = line.state_id.name	
			country = line.state_id.country_id.name	
			location = "%s %s %s %s" %(line.zipcode, line.name, state, country)
			res.append((line['id'], location))
		return res

	def search(self, cr, uid, args=None, offset=0, limit=80, unknow=0, context=None):
		res = super(city, self).search(cr, uid, args, offset, limit, unknow, context)
		if not res and args:
			args = [('zipcode', 'ilike', args[0][2])]
			res = super(city, self).search(cr, uid, args, offset, limit, unknow, context)
		return res	
		
	_name = 'city.city'
	_description = 'City'
	_columns = {
		'state_id': fields.many2one('res.country.state', 'State', required=True, select=1),
		'name': fields.char('City', size=64, required=True, select=1),
		'zipcode': fields.char('ZIP', size=64, required=True, select=1),
	}
city()


class CountryState(osv.osv):
	_inherit = 'res.country.state'
	_columns = {
		'city_ids': fields.one2many('city.city', 'state_id', 'Cities'),
	}
CountryState()


class res_partner_address(osv.osv):	
	def _get_zip(self, cr, uid, ids, field_name, arg, context):
		res={}
		for obj in self.browse(cr,uid,ids):
			if obj.location:
				res[obj.id] = obj.location.zipcode
			else:
				res[obj.id] = ""
		#print "   _get_zip", str(res)
		return res
		
	def _get_city(self, cr, uid, ids, field_name, arg, context):
		res={}
		for obj in self.browse(cr,uid,ids):
			if obj.location:
				res[obj.id] = obj.location.name
			else:
				res[obj.id] = ""
		#print "   _get_city", str(res)
		return res
		
	def _get_state(self, cr, uid, ids, field_name, arg, context):
		res={}
		for obj in self.browse(cr,uid,ids):
			if obj.location:
				res[obj.id] = [obj.location.state_id.id, obj.location.state_id.name]
			else:
				res[obj.id] = False
		return res

	def _get_country(self, cr, uid, ids, field_name, arg, context):
		res={}
		for obj in self.browse(cr,uid,ids):
			if obj.location:
				res[obj.id] = [obj.location.state_id.country_id.id, obj.location.state_id.country_id.name]
			else:
				res[obj.id] = False
		print res
		return res

	def _search_state(self, cr, uid, obj, name, args):
		res={}
		for i in ids:
			res[i] = [66, 74]
		return res	
		
	def _search_country(self, cr, uid, obj, name, args):
		res={}
		for i in ids:
			res[i] = [66, 74]
		return res	

	_inherit = "res.partner.address"
	_columns = {
			'location': fields.many2one('city.city', 'Location'),
			'zip': fields.function(_get_zip, method=True, type="char", string='Zip', size=24),
			'city': fields.function(_get_city, method=True, type="char", string='City', size=128),
			#  , fnct_search=_search_state 
			#  , fnct_search=_search_country
			'state_id': fields.function(_get_state, obj="res.country.state", method=True, type="many2one", string='State'), 
			'country_id': fields.function(_get_country, obj="res.country" ,method=True, type="many2one", string='Country'), 
			#'zip': fields.char('Zip', change_default=True, size=24),
			#'city': fields.char('City', size=128),
			#'state_id': fields.many2one("res.country.state", 'State', domain="[('country_id','=',country_id)]"),
			#'country_id': fields.many2one('res.country', 'Country'),
				}
"""
	def onchange_location(self, cr, uid, ids, location, zip, city, state_id, country_id): # state_id, country_id
		address_obj = self.browse(cr, uid, ids)[0]
		if location:
			city_obj = self.pool.get('city.city').browse(cr, uid, [location])[0]
			if city_obj.zipcode <> zip:
				zip = city_obj.zipcode
			if city_obj.name <> city:
				city = city_obj.name
			if city_obj.state_id.id <> state_id:
				state_id = city_obj.state_id.id
			if city_obj.state_id.country_id.id <> country_id:
				country_id = city_obj.state_id.country_id.id
			return {'value':{'location':location,'zip': zip, 'city':city,'state_id': state_id, 'country_id':country_id,}}
		else:
			return {'value':{'zip': '', 'city':'','state_id': '', 'country_id':'',}}
"""
res_partner_address()

# Basado en el wizard de l10n_ES_toponyms
cpostal_end_form = '''<?xml version="1.0"?>
<form string="Códigos postales">
	<separator string="Resultado:" colspan="4"/>
	<label string="Se han creado los municipios y provincias del Estado español asociados a códigos postales." colspan="4" align="0.0"/>
	<label string="Permite rellenar automáticamente los campos ciudad y provincia del formulario de empresa y contacto a partir del código postal." colspan="4" align="0.0"/>
</form>'''

class city_crear_cpostal(wizard.interface):
	def _crear_cpostal(self, cr, uid, data, context):
		from cities import municipios
		pool = pooler.get_pool(cr.dbname)
		print pool
		state_obj = pool.get('res.country.state')
		#zip_obj = pool.get('city.zipcode')
		city_obj = pool.get('city.city')
		for municipio in municipios:
			codigo = municipio[0][:2]
			if codigo == '00': codigo = '01'
			args = [('code', '=', codigo),]
			state_id = state_obj.search(cr, uid, args)
			city_data = {'name':municipio[1], 'state_id':state_id[0], 'zipcode':municipio[0]}
			city_id = [city_obj.create(cr, uid, city_data)]
		return {}

	states = {
		'init': {
			'actions': [_crear_cpostal],
			'result': {
				'type':'form',
				'arch':cpostal_end_form,
				'fields': {},
				'state':[('end', 'Aceptar', 'gtk-ok'),]
			}
		}
		
	}

city_crear_cpostal('city.crear_cpostal')


