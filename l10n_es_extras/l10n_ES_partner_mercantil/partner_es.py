# -*- encoding: utf-8 -*-

from osv import osv, fields
import tools
import os

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
	'es_libro': fields.char('Book', size=128), #libro
	'es_registro_mercantil': fields.char('Commercial Registry', size=128), # Registro Mercantil
	'es_hoja': fields.char('Sheet', size=128), #hoja
	'es_folio': fields.char('Page', size=128), #folio
	'es_seccion': fields.char('Section', size=128),# seccion
	'es_tomo': fields.char('Volume', size=128),# tomo
	
    }
res_partner()

