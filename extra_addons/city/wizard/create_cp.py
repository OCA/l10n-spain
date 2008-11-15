# -*- encoding: utf-8 -*-

import wizard
#import netsvc
#import ir
import pooler

# Basado en el wizard de l10n_ES_toponyms
cpostal_end_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Códigos postales">
    <separator string="Resultado:" colspan="4"/>
    <label string="Se han creado los municipios y provincias del Estado español asociados a códigos postales." colspan="4" align="0.0"/>
    <label string="Permite rellenar automáticamente los campos ciudad y provincia del formulario de empresa y contacto a partir del código postal." colspan="4" align="0.0"/>
</form>'''

class city_crear_cpostal(wizard.interface):
    def _crear_cpostal(self, cr, uid, data, context):
        from cities import municipios
        pool = pooler.get_pool(cr.dbname)
        state_obj = pool.get('res.country.state')
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
