# -*- encoding: utf-8 -*-

import wizard
#import netsvc
#import ir
import pooler

retrieve_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Recuperar CP">
    <label string="¿Desea recuperar los datos de ubicación existentes antes de instalar el módulo city?." colspan="4" align="0.0"/>
</form>'''

retrieve_done = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Datos recuperados">
    <separator string="Resultado:" colspan="4"/>
    <label string="La recuperación de datos de ubicación a concluido." colspan="4" align="0.0"/>
</form>'''

class city_recuperar_cpostal(wizard.interface):
    def _recuperar_cpostal(self, cr, uid, data, context):
        cr.execute("select id, zip from res_partner_address where location IS NULL")
        zipcodes = cr.dictfetchall()
        for zipcode in zipcodes:
            if zipcode['zip']:
                cr.execute("select id from city_city where zipcode = %s" %zipcode['zip'])
                city_id = cr.fetchall()
                if len(city_id) > 0:
                    cr.execute("update res_partner_address SET location = %i WHERE id = %i" %(city_id[0][0], zipcode['id']))
        return {}

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : retrieve_form,
                    'fields' : {},
                    'state' : [('end', 'Cancel'),('retrieve', 'Aceptar', 'gtk-ok') ]}
        },
        'retrieve': {
            'actions': [_recuperar_cpostal],
            'result': {
                'type':'form',
                'arch':retrieve_done,
                'fields': {},
                'state':[('end', 'Aceptar', 'gtk-ok'),]
            }
        }
        
    }
city_recuperar_cpostal('city.recuperar_cpostal')


