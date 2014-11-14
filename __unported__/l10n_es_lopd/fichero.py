# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 LambdaSoftware (<http://www.lambdasoftware.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from osv import fields, osv
from .procesos.funciones import mensaje_consola
#import time

##########################################################################
# Clase para almacenar el declarante
##########################################################################


class lopd_declarante(osv.osv):
    ##########################################################################
    # Sobreescritura del método para mostrar nombre y apellidos
    ##########################################################################

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(
            cr, uid, ids, ['name', 'apellido1', 'apellido2'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['apellido1']:
                name = name + ' ' + record['apellido1']
            if record['apellido2'] and record['apellido2'] != '-':
                name = name + ' ' + record['apellido2']
            res.append((record['id'], name))
        return res

    _name = 'lopd.declarante'
    _description = 'Datos de los declarantes'
    _columns = {
        'name': fields.char('Nombre', size=35, required=True),
        'apellido1': fields.char('Primer Apellido', size=35, required=True),
        'apellido2': fields.char('Segundo Apellido', size=35, required=True, help='Si el declarante carece de segundo apellido por ser extranjero, deberá cumplimentarse con "-" (un guión).'),
        'nif': fields.char('NIF / CIF', required=True, size=9),
        'cargo': fields.char('Cargo', size=70, required=True, help='Cargo o condición'),
        # 'cargo': fields.many2one('hr.job', 'Cargo', required = True, help='Cargo o condición'), #TODO: Modificar fichero_nota.py y reemplazar la asignación del cargo de texto por lectura en db
        'denomina_p': fields.char('Denominación postal', required=True, size=70, help='Denominación conocida a efectos postales'),
        'dir_postal': fields.char('Dirección postal', size=100, required=True),
        'pais': fields.many2one('res.country', 'Pais', required=True),
        'provincia': fields.many2one("res.country.state", 'Provincia', domain="[('country_id','=',pais)]", required=True),
        'localidad': fields.char('Localidad', size=50, required=True),
        'postal': fields.char('Código postal', size=5, required=True),
        'telefono': fields.char('Teléfono', size=10, help='Número de teléfono'),
        'fax': fields.char('Fax', size=10, help='Número de fax'),
        'email': fields.char('E-Mail', size=70, help='Dirección de correo electrónico'),
    }
lopd_declarante()

##########################################################################
# Clase principal de fichero
##########################################################################


class lopd_fichero(osv.osv):
    _name = 'lopd.fichero'
    _description = 'Datos relativos a los ficheros jurídicos'
    _columns = {
        #######################################################################
        # Datos del fichero
        #######################################################################
        'name': fields.char('Nombre', size=64, required=True, help='Nombre del fichero o tratamiento de datos'),
        'descripcion': fields.char('Descripción', size=350, required=True),
        'check': fields.boolean('He recibido la carta, con el código de inscripción del fichero, de la Agencia de protección de datos'),
        'codigo_agencia': fields.char('Código Agencia', size=10),
        'nivel': fields.selection([('1', 'Básico'), ('2', 'Medio'), ('3', 'Alto')], 'Nivel de seguridad del fichero', required=True),
        'estado': fields.selection([('est_leg', 'Legalizado'), ('est_mod', 'Modificado'), ('est_pmo', 'Pendiente'), ('est_pen', 'Pendiente'), ('est_null', 'No enviado'), ('est_baja', 'Baja')], 'Estado', required=True),
        'id_declarante': fields.many2one('lopd.declarante', 'Especifique la persona que va a declarar el fichero', required=True),
    }

    def onchange_check():
        return {'value': {'codigo_agencia': ''}}

    _defaults = {'nivel': '1', 'estado': 'est_null', }

lopd_fichero()


class fichero_estructura(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        #######################################################################
        # Estructura del fichero
        #######################################################################
        # datos especialmente protegidos
        'ideologia': fields.boolean('Ideología'),
        'afiliacion': fields.boolean('Afiliación sindical'),
        'religion': fields.boolean('Religión'),
        'creencias': fields.boolean('Creencias'),
        # otros datos especialmente protegidos
        'raza': fields.boolean('Origen racial o étnico'),
        'salud': fields.boolean('Salud'),
        'sexo': fields.boolean('Vida sexual'),
        # datos de carácter identificativo
        'dci': fields.char('Datos de carácter identificativo', size=30),
        'otrosdatos': fields.char('Otros datos de carácter significativo', size=100),
        # otros tipos de datos
        'otros_tipos_datos': fields.char('Otros tipos de datos', size=17),
        'otrostipos': fields.char('Otros tipos de datos', size=100),
    }
    _defaults = {
        'ideologia': lambda *a: False,
        'afiliacion': lambda *a: False,
        'religion': lambda *a: False,
        'creencias': lambda *a: False,
        'raza': lambda *a: False,
        #'salud': lambda *a: False,
        'sexo': lambda *a: False,
    }

    def onchange_datos_protegidos(self, cr, uid, ids, dato, finalidad='', afiliacion=False, salud=False):
        v = {}
        try:
            lista = finalidad.split(';')
        except:
            lista = ()

        if ('419' in lista and not salud):
            v = {'salud': True, }
            alerta = {'title': 'Atención', 'message':
                      'No puede modificar este campo ya que Historial clínico se encuentra entre las finalidades del fichero.\nSi el fichero no contiene ningún Historial clínico desactive esa finaliad.'}
            return {'value': v, 'warning': alerta}

        if (((('401' in lista) or ('402' in lista)) and (afiliacion or salud)) and dato):
            alerta = {'title': 'Atención', 'message':
                      'El fichero contiene datos especialmente protegidos de afiliación sindical y/o salud, pero se ha seleccionado como finalidad del mismo recursos humanos y/o gestión de nóminas, deberá indicar el nivel de seguridad manualmente. \n\nSeleccione el nivel en el desplegable que se encuentra en la parte superior derecha, junto al nombre del fichero.'}
            return {'value': v, 'warning': alerta}
        if (dato):
            v['nivel'] = '3'
        return {'value': v}

    def onchange_dci(self, cr, uid, ids, codigo, valor, cantidad, datos_iden):
        # Si valor viene a True, se ha marcado una casilla
        v = {}
        if cantidad > 0:
            lista = datos_iden.split(';')
        else:
            lista = []
        if (valor):
            if codigo not in lista:
                lista.append(codigo)
            v['n_dci'] = cantidad + 1
        else:
            if codigo in lista:
                lista.remove(codigo)
            v['n_dci'] = cantidad - 1
        lista.sort()
        v['dci'] = ';'.join(lista)
        return {'value': v}

    def onchange_otrostipos(self, cr, uid, ids, codigo, valor, cantidad, otrosdatos):
        # Si valor viene a True, se ha marcado una casilla
        v = {}
        if (cantidad > 0):
            lista = otrosdatos.split(';')
        else:
            lista = []
        if (valor):
            if codigo not in lista:
                lista.append(codigo)
                v['n_otd'] = cantidad + 1
        else:
            if codigo in lista:
                lista.remove(codigo)
                v['n_otd'] = cantidad - 1
        lista.sort()
        v['otros_tipos_datos'] = ';'.join(lista)

        return {'value': v}

fichero_estructura()


class fichero_responsable(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        #######################################################################
        # Responsables del fichero
        #######################################################################
        'id_responsable': fields.many2one('res.partner', 'Responsable de Fichero', required=True, readonly=True),
        'unidad_empresa': fields.boolean('¿Mantener los datos de la empresa/asociación?', ),
        'id_unidad': fields.many2one('res.partner', 'Unidad de ejercicio de derechos', required=True),
        #'encargado_empresa':fields.boolean('¿Mantener los datos de la empresa?', required=True),
        #'id_encargado':fields.many2one('res.partner','Encargado de tratamiento', required=True),
        'id_encargado': fields.many2many('res.partner', 'lopd_rel_pafi', 'id_fi', 'id_pa', 'Encargados de tratamiento', required=True),
    }

    def onchange_unidad(self, cr, uid, ids, valor):
        v = {'id_unidad': 1}
        return {'value': v}

    def onchange_encargado(self, cr, uid, ids, valor):
        v = {'id_encargado': 1}
        return {'value': v}

    _defaults = {
        'unidad_empresa': lambda *a: True,
        #'encargado_empresa':lambda *a: True,
        'id_responsable': lambda obj, cr, uid, context: uid,
        'id_unidad': lambda obj, cr, uid, context: uid,
        #'id_encargado': lambda obj,cr,uid,context: uid,
        'id_encargado': lambda self, cr, uid, context:
        self.pool.get('res.partner').search(
            cr, uid, [('id', '=', 1)], context=context),
    }

fichero_responsable()


class fichero_finalidad(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        'finalidad': fields.char('finalidad', size=23),
        #######################################################################
        #        'datoseval':fields.selection([('de_s','Sí'),('de_n','No'),], '¿Contiene el Fichero datos de carácter personal suficientes para obtener una evaluación de la personalidad del individuo?', size=2, required= True),
        #        'evalperso':fields.selection([('ep_s','Sí'),('ep_n','No'),], '¿Utiliza los datos de carácter personal para evaluar la personalidad de los individuos?', size=2, required= True),
        #        'solvpatri':fields.selection([('sp_s','Sí'),('sp_n','No'),], '¿Los datos de carácter personal del Fichero son destinados a la prestación de servicios sobre la solvencia patrimonial o crédito?', size=2, required= True),
        #        'servfinan':fields.selection([('sf_s','Sí'),('sf_n','No'),], '¿Los datos de carácter personal son utilizados para ofertar servicios financieros?', size=2, required= True),
        #        'seguactiv':fields.selection([('sa_s','Sí'),('sa_n','No'),], '¿Los datos de carácter personal son utilizados para prestar servicios relacionados con los seguros o actividades auxiliares del seguro?', size=2, required= True),
    }

#    _defaults = {
#        'datoseval': 'de_n',
#        'evalperso': 'ep_n',
#        'solvpatri': 'sp_n',
#        'servfinan': 'sf_n',
#        'seguactiv': 'sa_n',
#    }

    def onchange_finalidad(self, cr, uid, ids, codigo, valor, cantidad, finalidad, afiliacion=False, salud=False):
        # Si valor viene a True, se ha marcado una casilla
        v = {}
        if (cantidad > 0):
            lista = finalidad.split(';')
        else:
            lista = []
        if (valor):
            if codigo not in lista:
                lista.append(codigo)
                v['n_fin'] = cantidad + 1
        else:
            if codigo in lista:
                lista.remove(codigo)
                v['n_fin'] = cantidad - 1
        lista.sort()
        v['finalidad'] = ';'.join(lista)
        if (codigo == '419' and valor):
            v['salud'] = True

        if ((codigo == '401' or codigo == '402') and valor):
            if ((('401' in lista) or ('402' in lista)) and (salud or afiliacion) and valor):
                alerta = {'title': 'Atención', 'message':
                          'El fichero contiene datos especialmente protegidos de afiliación sindical y/o salud, pero se ha seleccionado como finalidad del mismo recursos humanos y/o gestión de nóminas, deberá indicar el nivel de seguridad manualmente. \n\nSeleccione el nivel en el desplegable que se encuentra en la parte superior junto al nombre del fichero.'}
                return {'value': v, 'warning': alerta}

        return {'value': v}

fichero_finalidad()


class fichero_origen(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        #######################################################################
        # Origen y procedencia de los datos
        #######################################################################
        # Origen
        'interesado': fields.boolean('El propio interesado o su representante legal'),
        'reg_publico': fields.boolean('Registros públicos'),
        'ent_privada': fields.boolean('Entidad privada'),
        'fue_publica': fields.boolean('Fuentes accesibles al público', help='Censo promocional\nGuías de servicios de telecomunicaciones\nListas de personal pertenecientes a grupos\nDiarios y boletines oficiales\nMedios de comunicación'),
        'adm_publica': fields.boolean('Administraciones públicas'),
        'otras': fields.boolean('Otras personas físicas distintas del afectado o su representante'),
        # colectivos o categorías de interesados
        'colectivos': fields.char('Colectivos', size=17),
        'otros_colectivos': fields.char('Otros colectivos', size=100),
    }
    _defaults = {
        'interesado': lambda *a: False, 'reg_publico': lambda *a: False, 'ent_privada': lambda *a: False, 'fue_publica': lambda *a: False, 'adm_publica': lambda *a: False, 'otras': lambda *a: False,
    }

    def onchange_colectivo(self, cr, uid, ids, codigo, valor, cantidad, colectivo):
        # Si valor viene a True, se ha marcado una casilla
        v = {}
        v['otros_colectivos'] = ''
        if (cantidad > 0):
            lista = colectivo.split(';')
        else:
            lista = []
        if (valor):
            if codigo not in lista:
                lista.append(codigo)
                v['n_col'] = cantidad + 1
        else:
            if codigo in lista:
                lista.remove(codigo)
                v['n_col'] = cantidad - 1
        lista.sort()
        v['colectivos'] = ';'.join(lista)

        return {'value': v}

fichero_origen()


class fichero_cesion(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        #######################################################################
        # Cesión o Comunicación de Datos
        #######################################################################
        'cesiones': fields.char('Cesiones', size=17),
        'otras_cesiones': fields.char('Otros', size=100),
        'no_cesion': fields.boolean('No se realizan cesiones', required=True)
    }
    _defaults = {'no_cesion': lambda *a: True, }

    def onchange_nocesion(self, cr, uid, ids, nocesion):
        lista = ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                 '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21')
        v = {}
        v = {'cesiones': '', 'n_cesiones': 0, 'otras_cesiones': ''}
        for elemento in lista:
            v['cc' + elemento] = False
        return {'value': v}

    def onchange_cesion(self, cr, uid, ids, codigo, valor, cantidad, cadena):
        # Si valor viene a True, se ha marcado una casilla
        v = {}
        if (cantidad > 0):
            lista = cadena.split(';')
        else:
            lista = []
        if (valor):
            if codigo not in lista:
                lista.append(codigo)
                v['n_ces'] = cantidad + 1
        else:
            if codigo in lista:
                lista.remove(codigo)
                v['n_ces'] = cantidad - 1
        lista.sort()
        v['cesiones'] = ';'.join(lista)

        return {'value': v}

fichero_cesion()


class fichero_rel(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        'id_programa': fields.many2many('lopd.programas', 'lopd_rel_fipro', 'id_fic', 'id_pro', 'Programas'),
        'id_soporte': fields.many2many('lopd.soportes', 'lopd_rel_fisop', 'id_fic', 'id_sop', 'Soportes'),
    }

fichero_rel()


class categoria_destinatarios(osv.osv):
    _name = 'lopd.categoria.destinatarios'
    _description = 'Categorías de destinatarios para las transferencias'
    _columns = {
        'id': fields.integer('ID', required=True, readonly=True),
        'name': fields.char('Nombre', size=80, required=True),
    }
categoria_destinatarios()


class fichero_transferencias(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        #'paises': fields.char('Paises', size=14),
        #'categorias': fields.char('Categorías', size=11),
        'pais1': fields.many2one('res.country', 'Paises'),
        'categoria1': fields.many2one('lopd.categoria.destinatarios', 'c1'),
        'pais2': fields.many2one('res.country', 'Paises'),
        'categoria2': fields.many2one('lopd.categoria.destinatarios', 'c2'),
        'pais3': fields.many2one('res.country', 'Paises'),
        'categoria3': fields.many2one('lopd.categoria.destinatarios', 'c3'),
        'pais4': fields.many2one('res.country', 'Paises'),
        'categoria4': fields.many2one('lopd.categoria.destinatarios', 'c4'),
        'pais5': fields.many2one('res.country', 'País'),
        'categoria5': fields.char('Otras categorías de destinatarios', size=100),
        'no_transfer': fields.boolean('No se realizan transferencias', required=True),
    }
    _defaults = {
        'no_transfer': lambda *a: True,
    }

    def onchange_pais1(self, cr, uid, ids, pais):
        v = {'categoria1': 0, 'categoria2': 0, 'categoria3': 0,
             'categoria4': 0, 'pais2': 0, 'pais3': 0, 'pais4': 0, }
        return {'value': v}

    def onchange_pais2(self, cr, uid, ids, pais):
        v = {'categoria2': 0, 'categoria3': 0,
             'categoria4': 0, 'pais3': 0, 'pais4': 0, }
        return {'value': v}

    def onchange_pais3(self, cr, uid, ids, pais):
        v = {'categoria3': 0, 'categoria4': 0, 'pais4': 0, }
        return {'value': v}

    def onchange_pais4(self, cr, uid, ids, pais):
        v = {'categoria4': 0}
        return {'value': v}

    def onchange_pais5(self, cr, uid, ids, pais):
        v = {'categoria5': 0}
        return {'value': v}

    def onchange_categoria1(self, cr, uid, ids, cat):
        v = {'pais2': 0, 'pais3': 0, 'pais4': 0,
             'categoria2': 0, 'categoria3': 0, 'categoria4': 0}
        return {'value': v}

    def onchange_categoria2(self, cr, uid, ids, cat):
        v = {'pais3': 0, 'pais4': 0, 'categoria3': 0, 'categoria4': 0}
        return {'value': v}

    def onchange_categoria3(self, cr, uid, ids, cat):
        v = {'pais4': 0, 'categoria4': 0}
        return {'value': v}

    def onchange_notransfer(self, cr, uid, ids, transfer):
        v = {'categoria1': 0, 'categoria2': 0, 'categoria3': 0, 'categoria4': 0,
             'categoria5': 0, 'pais1': 0, 'pais2': 0, 'pais3': 0, 'pais4': 0, 'pais5': 0}
        return {'value': v}
fichero_transferencias()

##########################################################################
# Columnas para guardar las modificaciones realizadas al fichero
##########################################################################


class fichero_mod(osv.osv):
    _inherit = 'lopd.fichero'
    _columns = {
        'mod_cif_nif': fields.char('NIF / CIF', size=9),
        'mod_res': fields.boolean('¿Se ha modificado el responsable?'),
        'mod_serv': fields.boolean('¿Se ha modificado el servicio o unidad de acceso?'),
        'mod_iden': fields.boolean('¿Se han modificado datos descriptivos del fichero y sus finalidades?'),
        'mod_enc': fields.boolean('¿Se ha modificado del encargado de tratamiento?'),
        'mod_est': fields.boolean('¿Se han modificado los tipos de datos, estructura o sistema de tratamiento?'),
        'mod_med': fields.boolean('¿Se han modificado las medidas de seguridad y auditorías?'),
        'mod_org': fields.boolean('¿Se ha modificado el origen y procedencia de los datos?'),
        'mod_tra': fields.boolean('¿Se ha modificado la información referida a transferencias internacionales?'),
        'mod_com': fields.boolean('¿Se ha modificado la información referida a comunicación de datos?'),
    }

fichero_mod()


class fichero_botones(osv.osv):
    _inherit = 'lopd.fichero'

    ##########################################################################
    # Funciones de botones
    ##########################################################################
    def envio_nuevo(self, cr, uid, ids, context):
        datos = self.browse(cr, uid, ids, context)
        for linea in datos:
            if linea['estado'] == 'est_null' or linea['estado'] == 'est_pen':
                self.creacion_fichero(cr, uid, ids, context, 1)
            elif linea['estado'] == 'est_mod':
                self.creacion_fichero(cr, uid, ids, context, 2)
            # En caso de estar pendiente de legalización la opción está
            # desactivada desde la vista
        mensaje = {'title': 'Atención', 'message':
                   'No olvide imprimir y enviar a la agencia el archivo asociado a esta petición.\n Para ello pulse el botón \'Abrir\' del campo \'Ultima solicitud\'.'}
        # TODO: El fichero debería mostrarse sólo
        #raise osv.except_osv('Atención','Recuerde que para completar el proceso debe enviar a la agencia el archivo asociado a esta petición.\n\n Para ello pulse el botón \'Abrir\' del campo \'Ultima solicitud\'.')
        return {'warning': mensaje, 'nodestroy': True}
        # return False

    def envio_baja(self, cr, uid, ids, context, motivos, previsiones):
        datos = self.browse(cr, uid, ids, context)
        for linea in datos:
            # Crea una solicitud de baja
            if linea['estado'] == 'est_leg':
                return self.creacion_fichero(cr, uid, ids, context, 3, motivos, previsiones)
            elif linea['estado'] == 'est_null':
                return super(lopd_fichero, self).unlink(cr, uid, ids, context)
            # elif linea['estado']=='est_pen' # El botón está desactivado en la vista cuando el fichero está 'pendiente'
              #mensaje_consola(2,"No se puede solicitar la baja, el fichero se encuentra en estado pendiente")
              #raise osv.except_osv('¡No se puede procesar la baja!','El fichero ha sido enviado a la agencia y está pendiente.')
        mensaje = {'title': 'Atención', 'message':
                   'Recuerde que para completar el proceso debe enviar a la agencia el archivo asociado a esta petición.\n\n Para ello pulse el botón \'Abrir\' del campo \'Ultima solicitud\'.'}
        # TODO: El fichero debería mostrarse sólo
        #raise osv.except_osv('Atención','Recuerde que para completar el proceso debe enviar a la agencia el archivo asociado a esta petición.\n\n Para ello pulse el botón \'Abrir\' del campo \'Ultima solicitud\'.')
        return {'warning': mensaje, 'nodestroy': True}
        # return False

    def confirmar_envio(self, cr, uid, ids, context):
        # Llama al método write
        return self.write(cr, uid, ids, context)

    def confirmar_legalizacion(self, cr, uid, ids, context):
        # Marca un fichero como legalizado
        return super(lopd_fichero, self).write(cr, uid, ids, {'estado': 'est_leg'}, context)

    def cancelar_envio(self, cr, uid, ids, context):
        # Marca un fichero como no enviado
        return super(lopd_fichero, self).write(cr, uid, ids, {'estado': 'est_null'}, context)

    def borrar_fichero(self, cr, uid, ids, context):
        # Borra el fichero
        return super(lopd_fichero, self).unlink(cr, uid, ids, context)

    def legal_papel(self, cr, uid, ids, context):
        # TODO: documento legal en papel
        ok = True
        if (ok):
            self.write(cr, uid, ids, {'estado': 'est_null'})
            return True
        else:
            return False

fichero_botones()


class fichero_metodos_sobrecargados(osv.osv):
    _inherit = 'lopd.fichero'

    ##########################################################################
    # Sobreescritura del método read
    ##########################################################################
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        values = super(lopd_fichero, self).read(cr, uid, ids, fields, context)
        # Lectura de finalidades
        try:
            finalidad = values[0].get('finalidad', False)
        except:
            mensaje_consola(
                2, 'Ha habido problemas con la lectura de las finalidades')
            return values
        try:
            lista_fin = finalidad.split(';')
            values[0]['n_fin'] = len(lista_fin)
            for campo in lista_fin:
                values[0]['f' + campo] = True
        except:
            values[0]['n_fin'] = 0
        # Lectura de colectivos
        colectivo = values[0].get('colectivos', False)
        try:
            lista_col = colectivo.split(';')
            values[0]['n_col'] = len(lista_col)
            for campo in lista_col:
                values[0]['c' + campo] = True
        except:
            values[0]['n_col'] = 0
        # Lectura de cesiones
        cesion = values[0].get('cesiones', False)
        try:
            lista_ces = cesion.split(';')
            values[0]['n_ces'] = len(lista_ces)
            for campo in lista_ces:
                values[0]['cc' + campo] = True
        except:
            values[0]['n_ces'] = 0
        # Lectura de datos de carácter identificativo
        dci = values[0].get('dci', False)
        try:
            lista_dci = dci.split(';')
            values[0]['n_dci'] = len(lista_dci)
            for campo in lista_dci:
                values[0]['dci' + campo] = True
        except:
            values[0]['n_dci'] = 0
        # Lectura otros tipos de datos
        otrosdat = values[0].get('otros_tipos_datos', False)
        try:
            lista_otd = otrosdat.split(';')
            values[0]['n_otd'] = len(lista_otd)
            for campo in lista_otd:
                values[0]['otd' + campo] = True
        except:
            values[0]['n_otd'] = 0

        return values

    ##########################################################################
    # Sobreescritura del método create
    ##########################################################################
    # *Cuando no hay definido encargado de tratamiento el error no es descriptivo, (Corrija los campos en rojo!)

    def create(self, cr, uid, vals, context=None):
        # Se comprueba si esta marcado un elemento de carácter identificativo
        datos_iden = vals['dci'] or vals['otrosdatos']
        if not datos_iden:
            mensaje_consola(
                2, "fichero no creado, no se han especificado datos de carácter identificativo")
            raise osv.except_osv('¡Faltan datos sobre la estructura!',
                                 'Es obligatorio definir que datos de carácter identificativo contiene el fichero.\nPor favor, corrija los datos antes de guardar.')

        # Se comprueba que haya una unidad de ejercicio de derechos definida
        if not vals['id_unidad']:
            mensaje_consola(
                2, "Fichero no creado, no se ha definido la unidad de ejercicio de derechos")
            raise osv.except_osv(
                '¡No hay unidad definida!', 'La unidad de ejercicio de derechos no ha sido definida.\n\nSi la unidad coincide con la dirección de la empresa o asociación, asegurese de que esté marcada la casilla \'Mantener datos de la empresa/asociación\' en la pestaña \'Responsables\'.')

        # TODO: Se comprueba que haya un encargado definido (no realiza la
        # comprobación?)
        if not vals['id_encargado']:
            mensaje_consola(
                2, "Fichero no creado, no se ha definido un encargado")
            raise osv.except_osv(
                '¡No hay encargado definido!', 'Es necesario especificar el encargado de tratamiento, si este coincide con el responsable agréguelo en la pestaña de \'Responsables\'.\nPor favor, corrija los datos antes de guardar.')

        # Se comprueba que haya marcada una finalidad
        if not vals['finalidad']:
            mensaje_consola(
                2, "Fichero no creado, el usuario no ha definido una finalidad")
            raise osv.except_osv('¡No se ha marcado la finalidad!',
                                 'Debe definir al menos una finalidad para el fichero.\nPor favor, corrija los datos antes de guardar.')
        lista = vals['finalidad'].split(';')

        # Se comprueba en caso de haber transferencias internacionales que
        # tengan asignada la categoría de destinatarios
        if not vals['no_transfer']:
            for num in range(1, 6):
                if vals['pais' + str(num)]:
                    if not vals['categoria' + str(num)]:
                        mensaje_consola(
                            2, "Fichero no creado, se han definido transferencias sin categorías asignadas")
                        raise osv.except_osv(
                            '¡Error en las transferencas!', 'Se han especificado paises a los que se realizaran transferencias internacionales, pero no se ha definido la categoría del destinatario.\nPor favor, corrija los datos antes de guardar.')
        # Asignación del nivel del Fichero
        ideologia = vals['ideologia']
        afiliacion = vals['afiliacion']
        religion = vals['religion']
        creencias = vals['creencias']
        raza = vals['raza']
        salud = vals['salud']
        sexo = vals['sexo']
        datos_protegidos = ideologia or afiliacion or religion or creencias or raza or salud or sexo
        # Página 14 - Excepciones Apartado b) 'validaciones XML'
        if not(('401' in lista or '402' in lista) and (afiliacion or salud)):
            # Si hay datos protegidos el nivel deberá ser alto '3'
            if datos_protegidos and vals['nivel'] != '3':
                vals['nivel'] = '3'
            else:
                # En caso de las finalidades 404, 405 y 406 el nivel no podrá
                # ser bajo '1'
                if ('404' in lista) or ('405' in lista) or ('406' in lista) and (vals['nivel'] == '1'):
                    vals['nivel'] = '2'

        mensaje_consola(1, "Método create ejecutado")
        return super(lopd_fichero, self).create(cr, uid, vals, context)

    ##########################################################################
    # Sobreescritura del método write
    ##########################################################################

    def write(self, cr, uid, ids, vals, context=None):
        datos = self.browse(cr, uid, ids, context=context)
        for linea in datos:
            carta_agencia = vals.get('check', linea['check'])
            codigo_agencia = vals.get(
                'codigo_agencia', linea['codigo_agencia'])
            if carta_agencia and not codigo_agencia:
                mensaje_consola(
                    2, "fichero no modificado, código de agencia vacío")
                raise osv.except_osv(
                    '¡Falta el código de la agencia!', 'Ha indicado haber recibido la carta, con el código de inscripción del fichero, en la agencia de protección de datos, pero no ha introducido el código que se le ha proporcionado en la misma.\n Por favor, complete correctamente los datos antes de proseguir.')

            if carta_agencia and codigo_agencia and (linea['estado'] == 'est_pen' or linea['estado'] == 'est_pmo'):
                # return super(lopd_fichero, self).write(cr, uid, ids, vals, context)
                # TODO: Legalizar automáticamente en caso de ir con firma digital se recibe el número de registro
                # Sin firma digital, si se introduce el código a un fichero
                # pendiente se guarda y se marca como legalizado
                mensaje_consola(1, "Fichero legalizado")
                return super(lopd_fichero, self).write(cr, uid, ids, {'check': carta_agencia, 'codigo_agencia': codigo_agencia, 'estado': 'est_leg'})

            if linea['estado'] == 'est_pen' or linea['estado'] == 'est_pmo':
                mensaje_consola(
                    2, "Fichero no modificado, el fichero está pendiente de legalización")
                raise osv.except_osv('¡El fichero está pendiente de legalización!',
                                     'No puede modificar un fichero que ha sido enviado a la Agencia de protección de datos y está pendiente de ser legalizado.\nSi el fichero ya está legalizado y desea solicitar una modificación primero introduzca el código de inscripción del fichero proporcionado por la agencia de datos para el fichero.')
            # Comprobación de datos de carácter identificativo
            datos_iden = (vals.get('dci', linea['dci'])) or (
                vals.get('otrosdatos', linea['otrosdatos']))
            if not datos_iden:
                mensaje_consola(
                    2, "Fichero no modificado, no se han especificado datos de carácter identificativo")
                raise osv.except_osv('¡Se requiere información sobre la estructura!',
                                     'Es obligatorio definir que datos de carácter identificativo contiene el fichero.\nPor favor, corrija los datos antes de guardar.')

            # Comprobación de la unidad de ejercicio de derechos
            unidad = vals.get('id_unidad', linea['id_unidad'])
            if not unidad:
                mensaje_consola(
                    2, "Fichero no modificado, no se ha definido una unidad de ejercicio de derechos")
                raise osv.except_osv(
                    '¡No hay unidad definida!', 'La unidad de ejercicio de derechos no ha sido definida.\n\nSi la unidad coincide con la dirección de la empresa o asociación, asegurese de que esté marcada la casilla \'Mantener datos de la empresa/asociación\' en la pestaña \'Responsables\'.')

            encargado = vals.get('id_encargado', linea['id_encargado'])
            # TODO: Comprobación del encargado de tratamiento (No realiza la
            # comprobación)
            if not encargado:
                mensaje_consola(
                    2, "Fichero no modificado, no se ha definido un encargado")
                raise osv.except_osv(
                    '¡No hay encargado definido!', 'Es necesario especificar el encargado de tratamiento, si este coincide con el responsable agréguelo igualmente en la pestaña de \'Responsables\'.\nPor favor, corrija los datos antes de guardar.')

            # Comprobación de finalidades
            finalidad = vals.get('finalidad', linea['finalidad'])
            if not finalidad:
                mensaje_consola(
                    2, "Fichero no modificado, no se ha definido una finalidad")
                raise osv.except_osv(
                    '¡No se ha marcado la finalidad!', 'Debe definir al menos una finalidad para el fichero.\nPor favor, corrija los datos antes de guardar.')
            lista = finalidad.split(';')

            # Comprobación de transferencias
            trans = vals.get('no_transfer', linea['no_transfer'])
            if not trans:
                for num in range(1, 6):
                    pais = vals.get(
                        'pais' + str(num), linea['pais' + str(num)])
                    if pais:
                        categoria = vals.get(
                            'categoria' + str(num), linea['categoria' + str(num)])
                        if not categoria:
                            mensaje_consola(
                                2, "Fichero no modificado, se han definido transferencias sin categorías asignadas")
                            raise osv.except_osv(
                                '¡Error en las transferencas!', 'Se han especificado paises a los que se realizaran transferencias internacionales, pero no se ha definido la categoría del destinatario.\nPor favor, corrija los datos antes de guardar.')
            # Asignación del nivel del Fichero
            ideologia = vals.get('ideologia', linea['ideologia'])
            afiliacion = vals.get('afiliacion', linea['afiliacion'])
            religion = vals.get('religion', linea['religion'])
            creencias = vals.get('creencias', linea['creencias'])
            raza = vals.get('raza', linea['raza'])
            salud = vals.get('salud', linea['salud'])
            sexo = vals.get('sexo', linea['sexo'])
            datos_protegidos = ideologia or afiliacion or religion or creencias or raza or salud or sexo

            # Página 14 - Excepciones Apartado b) 'validaciones XML'
            if not(('401' in lista or '402' in lista) and (afiliacion or salud)):
                # Si hay datos protegidos el nivel deberá ser alto '3'
                nivel = vals.get('nivel', linea['nivel'])
                if datos_protegidos and nivel != '3':
                    vals['nivel'] = '3'
                # En caso de las finalidades 404, 405 y 406 el nivel no podrá
                # ser bajo '1'
                else:
                    if (('404' in lista) or ('405' in lista) or ('406' in lista)) and (nivel == '1'):
                        vals['nivel'] = '2'

            # Si el fichero está legalizado se guardan los datos que han sido
            # modificados
            if linea['estado'] == 'est_leg':
                # TODO: El responsable por defecto siempre es la empresa
                # inicial
                dr = self.pool.get('res.partner').read(cr, uid, 1, ['vat'])
                nr = dr['vat']  # Nif del responsable
                vals['mod_cif_nif'] = nr
                try:
                    vals['mod_res'] = True
                except:
                    vals['mod_res'] = False
                try:
                    vals['mod_serv'] = True
                except:
                    vals['mod_serv'] = False
                try:
                    vals['mod_iden'] = True
                except:
                    vals['mod_iden'] = False
                if not vals['mod_iden']:
                    try:
                        vals['mod_iden'] = True
                    except:
                        vals['mod_iden'] = False
                try:
                    vals['mod_enc'] = True
                except:
                    vals['mod_enc'] = False

                estructura = ('ideologia', 'afiliacion', 'religion', 'creencias', 'raza',
                              'salud', 'sexo', 'otrosdatos', 'otros_tipos_datos', 'otrostipos', 'dci10', )
                vals['mod_est'] = False
                for clave in estructura:
                    if not vals['mod_est']:
                        try:
                            vals['mod_est'] = True
                        except:
                            vals['mod_est'] = False
                for num in range(1, 10):
                    if not vals['mod_est']:
                        try:
                            vals['dci0' + str(num)]
                            vals['mod_est'] = True
                        except:
                            vals['mod_est'] = False

                try:
                    vals['mod_med'] = True
                except:
                    vals['mod_med'] = False

                origen = ('interesado', 'reg_publico', 'ent_privada', 'fue_publica',
                          'adm_publica', 'otras', 'colectivos', 'otros_colectivos', )
                vals['mod_org'] = False
                for clave in origen:
                    if not vals['mod_org']:
                        try:
                            vals['mod_org'] = True
                        except:
                            vals['mod_org'] = False

                vals['mod_tra'] = False
                for num in range(1, 6):
                    if not vals['mod_tra']:
                        try:
                            vals['pais' + str(num)]
                            vals['mod_tra'] = True
                        except:
                            vals['mod_tra'] = False

                try:
                    vals['mod_com'] = True
                except:
                    vals['mod_com'] = False
                if not vals['mod_com']:
                    try:
                        vals['mod_com'] = True
                    except:
                        vals['mod_com'] = False

                if vals['mod_res'] or vals['mod_serv'] or vals['mod_iden'] or vals['mod_enc'] or vals['mod_est'] or vals['mod_med'] or vals['mod_org'] or vals['mod_tra'] or vals['mod_com']:
                    vals['estado'] = 'est_mod'  # Se marca como modificado

        mensaje_consola(1, "Método write ejecutado")
        return super(lopd_fichero, self).write(cr, uid, ids, vals, context)

    ##########################################################################
    # Sobreescritura del método unlink
    ##########################################################################

    def unlink(self, cr, uid, ids, context=None):
        # Se comprueba si el fichero está legalizado o pendiente y en tal caso
        # no se permite la eliminación
        datos = self.browse(cr, uid, ids, context=context)
        for linea in datos:
            if linea['estado'] == 'est_pen' or linea['estado'] == 'est_pmo':
                mensaje_consola(
                    2, "Fichero no borrado, se ha intentado borrar un fichero pendiente.")
                raise osv.except_osv(
                    '¡Error no se puede eliminar!', 'No se permite la eliminación de un fichero que esté pendiente de legalización, debe esperar la respuesta de la agencia de protección de datos antes.')
            elif linea['estado'] == 'est_leg':
                mensaje_consola(
                    2, "Fichero no borrado, se ha intentado borrar un fichero legalizado.")
                raise osv.except_osv(
                    '¡Error no se puede eliminar!', 'No se permite la eliminación de un fichero legalizado que está dado de alta, debe dar de baja el fichero en la agencia de protección de datos antes.')
            elif linea['estado'] == 'est_mod':
                mensaje_consola(
                    2, "Fichero no borrado, se ha intentado borrar un fichero modificado.")
                raise osv.except_osv(
                    '¡Error no se puede eliminar!', 'No se permite la eliminación de un fichero legalizado que actualmente está modificado, debe dar de baja el fichero en la agencia de protección de datos antes.')
            elif linea['estado'] == 'est_baja':
                mensaje_consola(1, "Método unlink ejecutado")
                return super(lopd_fichero, self).unlink(cr, uid, ids, context)
        return super(lopd_fichero, self).unlink(cr, uid, ids, context)

fichero_metodos_sobrecargados()

##########################################################################
# Campos no guardados en la base de datos
##########################################################################


class fichero_campos(osv.osv):
    _inherit = 'lopd.fichero'
    # Declara campos que no son guardados en la base de datos y no pertecen al
    # diccionario columns

    def fields_get(self, cr, uid, fields=None, context=None, read_access=True):
        result = super(lopd_fichero, self).fields_get(cr, uid, fields, context)
        # Datos de carácter identificativo
        result['n_dci'] = {'string': 'Numero de datos', 'type': 'integer'}
        result['dci01'] = {'string': 'DNI / NIF', 'type': 'boolean'}
        result['dci02'] = {'string': 'Nº S.S. / Mutualidad', 'type': 'boolean'}
        result['dci03'] = {'string': 'Nombre y apellidos', 'type': 'boolean'}
        result['dci04'] = {
            'string': 'Dirección (postal, electrónica)', 'type': 'boolean'}
        result['dci05'] = {'string': 'Tarjeta sanitaria', 'type': 'boolean'}
        result['dci06'] = {'string': 'Teléfono', 'type': 'boolean'}
        result['dci07'] = {
            'string': 'Firma / Huella digital', 'type': 'boolean'}
        result['dci08'] = {'string': 'Imágen / Voz', 'type': 'boolean'}
        result['dci09'] = {'string': 'Marcas físicas', 'type': 'boolean'}
        result['dci10'] = {'string': 'Firma electrónica', 'type': 'boolean'}
        # Otros tipos de datos
        result['n_otd'] = {'string': 'Numero de datos', 'type': 'integer'}
        result['otd01'] = {'string': 'Características personales', 'type': 'boolean', 'help':
                           'Datos de estado civil\nDatos de familia\nFecha de nacimiento\nLugar de nacimiento\nEdad\nSexo\nNacionalidad\nLengua materna\nCaracterísticas físicas o antropométricas'}
        result['otd02'] = {'string': 'Circunstancias sociales', 'type': 'boolean', 'help':
                           'Características de alojamiento, vivienda\nSituación militar\nPropiedades posesiones\nAficiones y estilo de vida\nPertenencia a clubes, asociaciones\nLicencias, permisos, autorizaciones'}
        result['otd03'] = {'string': 'Académicos profesionales', 'type': 'boolean', 'help':
                           'Formación, titulaciones\nHistorial del estudiante\nExperiencia profesional\nPertenencia a colegios o a asociaciones profesionales'}
        result['otd04'] = {'string': 'Detalles del empleo', 'type': 'boolean', 'help':
                           'Profesión y puestos de trabajo\nHistorial del estudiante\nDatos no económicos de nómina\nHistorial del trabajador'}
        result['otd05'] = {'string': 'Información comercial', 'type': 'boolean', 'help':
                           'Actividades y negocios\nLicencias comerciales\nSuscripciones a publicaciones / medios de comunicación\nCreaciones artísticas, literarias, científicas o técnicas'}
        result['otd06'] = {'string': 'Económicos, financieros y de seguros', 'type': 'boolean', 'help':
                           'Ingresos, rentas\nInversiones, bienes patrimoniales\nCréditos, préstamos, avales Bancarios\nPlanes de pensiones, jubilación\nEconómicos de nómina\nDeducciones impositivas / impuestos\nSeguros\nHipotecas\nSubsidios, beneficios\nHistorial créditos\nTarjetas crédito'}
        result['otd07'] = {'string': 'Transformaciones de bienes y servicios', 'type': 'boolean', 'help':
                           'Bienes y servicios suministrados por el afectado\nBienes y servicios recibidos por el afectado\nTransacciones financieras\nCompensaciones / indemnizaciones'}
        # Finalidades
        result['n_fin'] = {
            'string': 'Numero de finalidades', 'type': 'integer'}
        result['f400'] = {
            'string': 'Gestión de clientes contable, fiscal y administrativa', 'type': 'boolean'}
        result['f401'] = {'string': 'Recursos humanos', 'type': 'boolean'}
        result['f402'] = {'string': 'Gestión de nóminas', 'type': 'boolean'}
        result['f403'] = {
            'string': 'Prevención de riesgos laborales', 'type': 'boolean'}
        result['f404'] = {
            'string': 'Prestación de servicios de solvencia patrimonial y crédito', 'type': 'boolean'}
        result['f405'] = {
            'string': 'Cumplimiento/incumplimiento de obligaciones dinerarias', 'type': 'boolean'}
        result['f406'] = {
            'string': 'Servicios económico financieros y seguros', 'type': 'boolean'}
        result['f407'] = {'string': 'Análisis de perfiles', 'type': 'boolean'}
        result['f408'] = {
            'string': 'Publicidad y prospección comercial', 'type': 'boolean'}
        result['f409'] = {
            'string': 'Prestación de servicios de comunicación electrónica', 'type': 'boolean'}
        result['f410'] = {
            'string': 'Guías / repertorios de servicios de comunicaciones electrónicas', 'type': 'boolean'}
        result['f411'] = {'string': 'Comercio electrónico', 'type': 'boolean'}
        result['f412'] = {
            'string': 'Prestación de servicios de certificación electrónica', 'type': 'boolean'}
        result['f413'] = {'string': 'Gestión de asociados o miembros...', 'help':
                          'Gestión de asociados o miembros de partidos políticos, sindicatos, iglesias, confesiones o comunidades religiosas y asociaciones, fundaciones y otras entidades sin ánimo de lucro, cuya finalidad sea política, filosófica, religiosa o sindical', 'type': 'boolean'}
        result['f414'] = {
            'string': 'Gestión de actividades asociativas, culturales, recreativas, deportivas y sociales', 'type': 'boolean'}
        result['f415'] = {
            'string': 'Gestión de asistencia social', 'type': 'boolean'}
        result['f416'] = {'string': 'Educación', 'type': 'boolean'}
        result['f417'] = {
            'string': 'Investigación epidemiológica y otras actividades análogas', 'type': 'boolean'}
        result['f418'] = {
            'string': 'Gestión y control sanitario', 'type': 'boolean'}
        result['f419'] = {'string': 'Historial clínico', 'type': 'boolean'}
        result['f420'] = {'string': 'Seguridad privada', 'type': 'boolean'}
        result['f421'] = {
            'string': 'Seguridad y control de acceso a edificios', 'type': 'boolean'}
        result['f422'] = {'string': 'Videovigilancia', 'type': 'boolean'}
        result['f423'] = {
            'string': 'Fines estadísticos, históricos o científicos', 'type': 'boolean'}
        result['f499'] = {'string': 'Otras finalidades', 'type': 'boolean'}
        # Colectivos
        result['n_col'] = {'string': 'Numero de colectivos', 'type': 'integer'}
        result['c01'] = {'string': 'Empleados', 'type': 'boolean'}
        result['c02'] = {'string': 'Clientes y usuarios', 'type': 'boolean'}
        result['c03'] = {'string': 'Proveedores', 'type': 'boolean'}
        result['c04'] = {'string': 'Asociados o miembros', 'type': 'boolean'}
        result['c05'] = {
            'string': 'Propietarios o arrendatarios', 'type': 'boolean'}
        result['c06'] = {'string': 'Pacientes', 'type': 'boolean'}
        result['c07'] = {'string': 'Estudiantes', 'type': 'boolean'}
        result['c08'] = {'string': 'Personas de contacto', 'type': 'boolean'}
        result['c09'] = {'string': 'Padres o tutores', 'type': 'boolean'}
        result['c10'] = {'string': 'Representante legal', 'type': 'boolean'}
        result['c11'] = {'string': 'Solicitantes', 'type': 'boolean'}
        result['c12'] = {'string': 'Beneficiarios', 'type': 'boolean'}
        result['c13'] = {'string': 'Cargos públicos', 'type': 'boolean'}
        # Cesiones
        result['n_ces'] = {'string': 'Numero de cesiones', 'type': 'integer'}
        result['cc01'] = {
            'string': 'Organizaciones o personas directamente relacionadas con el responsable', 'type': 'boolean'}
        result['cc02'] = {
            'string': 'Organismos de la seguridad social', 'type': 'boolean'}
        result['cc03'] = {'string': 'Registros públicos', 'type': 'boolean'}
        result['cc04'] = {
            'string': 'Colegios profesionales', 'type': 'boolean'}
        result['cc05'] = {
            'string': 'Administración tributaria', 'type': 'boolean'}
        result['cc06'] = {
            'string': 'Otros órganos de la administración pública', 'type': 'boolean'}
        result['cc07'] = {
            'string': 'Comisión nacional del mercado de valores', 'type': 'boolean'}
        result['cc08'] = {
            'string': 'Comisión nacional del juego', 'type': 'boolean'}
        result['cc09'] = {
            'string': 'Notarios y procuradores', 'type': 'boolean'}
        result['cc10'] = {
            'string': 'Fuerzas y cuerpos de seguridad', 'type': 'boolean'}
        result['cc11'] = {
            'string': 'Organismos de la unión europea', 'type': 'boolean'}
        result['cc12'] = {
            'string': 'Entidades dedicadas al cumplimiento / incumplimiento de obligaciones dinerarias', 'type': 'boolean'}
        result['cc13'] = {
            'string': 'Bancos, cajas de ahorros y cajas rurales', 'type': 'boolean'}
        result['cc14'] = {
            'string': 'Entidades aseguradoras', 'type': 'boolean'}
        result['cc15'] = {
            'string': 'Otras entidades financieras', 'type': 'boolean'}
        result['cc16'] = {'string': 'Entidades sanitarias', 'type': 'boolean'}
        result['cc17'] = {
            'string': 'Prestaciones de servicio de telecomunicaciones', 'type': 'boolean'}
        result['cc18'] = {
            'string': 'Empresas dedicadas a publicidad o marketing directo', 'type': 'boolean'}
        result['cc19'] = {
            'string': 'Asociaciones y organizaciones sin ánimo de lucro', 'type': 'boolean'}
        result['cc20'] = {
            'string': 'Sindicatos y juntas de personal', 'type': 'boolean'}
        result['cc21'] = {
            'string': 'Administración pública con competencia en la materia', 'type': 'boolean'}
        # Warning Excepcion
        # result['warn_except'] = {'string':'Excepcion', 'type':'boolean'}
        return result

fichero_campos()

##########################################################################
# Clase para almacenar las solicitudes enviadas a la agencia
##########################################################################


class lopd_solicitudes(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name'], context=context)
        res = []
        for record in reads:
            name = record['name'].split('.')[0]
            print name
            #name = record['name']
            res.append((record['id'], name))
            print res
        return res

    _name = 'lopd.solicitud'
    _description = 'Solicitudes de alta/baja/modificación'
    # Evita que OpenERP cree los campos create_uid, create_date, etc
    _log_access = False
    _columns = {
        'name': fields.char('Número de envío', size=22, required=True, readonly=True),
        'archivo_pdf': fields.binary('Archivo', readonly=True, required=True, filters='*.pdf'),
        # fecha en la que se ha generado el archivo
        'fecha': fields.datetime('Fecha de envío', readonly=True, required=True),
        'id_fichero': fields.many2one('lopd.fichero', 'Fichero', required=True, readonly=True, ondelete='cascade'),
        # Usuario que ha procesado la solicitud
        'usuario': fields.many2one('res.users', 'Usuario que realizó el envío', readonly=True, required=True),
        'tipo': fields.selection([('1', 'Alta'), ('2', 'Modificación'), ('3', 'Supresión')], 'Tipo de solicitud', required=True, readonly=True)
    }
    _order = 'fecha desc'
lopd_solicitudes()


class fichero_solicitudes(osv.osv):
    #    def get_archivo_pdf(self, cr, uid, id):
    #        each = self.read(cr, uid, id, ['archivo_pdf'])
    #        pdf = each['archivo_pdf']
    #        return pdf

    def _mostrar_pdf(self, cr, uid, ids, field_name, arg, context):
        res = {}
        try:
            datos = self.pool.get('lopd.solicitud').search(
                cr, uid, [('id_fichero', '=', ids[0])])
            datos = self.pool.get('lopd.solicitud').read(
                cr, uid, datos[0], ['archivo_pdf', 'name', 'id'])
            for linea in self.browse(cr, uid, ids, context=context):
                res[linea.id] = datos['archivo_pdf']

            #mensaje_consola (1,"La id del ultimo fichero es "+str(datos['id'])+", y su codigo es "+datos['name'])

            #import base64
            #archivo = base64.decodestring(datos['archivo_pdf'])
            # print archivo

        except:
            mensaje_consola(1, "Nothing to do here")

        return res

    _inherit = 'lopd.fichero'
    _columns = {
        'solicitudes': fields.one2many('lopd.solicitud', 'id_fichero', 'Solicitudes', readonly=True),
        'pdf_solicitud': fields.function(_mostrar_pdf, type='binary', method=True, string='Ultima solicitud'),
    }
fichero_solicitudes()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
