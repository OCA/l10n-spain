# -*- encoding: utf-8 -*-

import wizard
import pooler

_retrieve_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Recuperar ubicaciones">
    <label string="¿Desea recuperar los datos de ubicación a partir del código postal que había en los contactos de empresas antes de instalar el módulo city?." colspan="4" align="0.0"/>
</form>'''

_retrieve_done = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Recuperar ubicaciones">
    <label string="La recuperación de datos de ubicación ha concluido." colspan="4" align="0.0"/>
    <separator string="Ubicaciones recuperadas:" colspan="4"/>
    <field name="retrieved"/>
</form>'''

_retrieve_done_fields = {
    'retrieved': {'string':'Recuperados', 'type':'integer', 'readonly': True},
}

class city_recuperar_cpostal(wizard.interface):
    def _recuperar_cpostal(self, cr, uid, data, context):
        cr.execute("select id, zip from res_partner_address where location IS NULL")
        zipcodes = cr.dictfetchall()
        cont = 0
        for zipcode in zipcodes:
            if zipcode['zip']:
                cr.execute("select id from city_city where zipcode = '%s'" %zipcode['zip'])
                city_id = cr.fetchall()
                if len(city_id) > 0:
                    cr.execute("update res_partner_address SET location = %i WHERE id = %i" %(city_id[0][0], zipcode['id']))
                    cont += 1
        return {'retrieved': cont}

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : _retrieve_form,
                    'fields' : {},
                    'state' : [('end', 'Cancel'),('retrieve', 'Aceptar', 'gtk-ok') ]}
        },
        'retrieve': {
            'actions': [_recuperar_cpostal],
            'result': {
                'type':'form',
                'arch':_retrieve_done,
                'fields': _retrieve_done_fields,
                'state':[('end', 'Aceptar', 'gtk-ok'),]
            }
        }

    }
city_recuperar_cpostal('city.recuperar_cpostal')
