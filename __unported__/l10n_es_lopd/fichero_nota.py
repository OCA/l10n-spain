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

from osv import osv


class fichero_nota(osv.osv):
    _inherit = 'lopd.fichero'

    def creacion_fichero(self, cr, uid, ids, context=None, tipo_solicitud=1, motivos="", destino_previsiones=""):
        import base64
        import datetime
        import os
        from .procesos.funciones import mensaje_consola, capitalizar, minimizar, sin_espacios
        from .procesos.fdfgen import crear_fdf
        from .procesos.barcode128 import Code128
        from suds.client import Client
        from xml.dom import minidom
        from reportlab.lib.units import inch

        # usado para completar los datos de la fecha y hora actual
        ahora = datetime.datetime.now()

        def boolean2num(dato):
            if (dato):
                return "1"
            else:
                return "0"

        def _error_datos(mensaje_c):
            mensaje_consola(2, mensaje_c)

        def _error_datos_responsable(mensaje):
            mensaje_c = "No se ha podido procesar %s del responsable" % (
                mensaje,)
            _error_datos(mensaje_c)
            raise osv.except_osv('¡Faltan datos del responsable!',
                                 'No se ha podido procesar %s del responsable, por favor compruebe que los datos del responsable sean correctos.' % (mensaje,))

        def _error_datos_unidad(mensaje):
            mensaje_c = "No se ha podido procesar %s de la unidad de ejercicio de derecho" % (
                mensaje,)
            _error_datos(mensaje_c)
            raise osv.except_osv('¡Faltan datos de la unidad de ejercicio de derechos!',
                                 'No se ha podido procesar %s de la unidad de ejercicio de derechos, por favor compruebe que los datos sean correctos.' % (mensaje,))

        def _error_datos_encargado(mensaje):
            mensaje_c = "No se ha podido procesar %s del encargado de tratamiento" % (
                mensaje,)
            _error_datos(mensaje_c)
            raise osv.except_osv('¡Faltan datos del encargado de tratamiento!',
                                 'No se ha podido procesar %s del encargado de tratamiento, por favor compruebe que los datos sean correctos.' % (mensaje,))

        datos = self.browse(cr, uid, ids, context=context)
        datos_fichero = datos[0]

        contenido_xml = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
        contenido_xml += '<Envio Id="AGPD">\n'

        #######################################################################
        # reg_cero
        #######################################################################
        contenido_xml += '\t<reg_cero>\n'
        contenido_xml += '\t\t<id_rock>0</id_rock>\n'
        # Titularidad (ind_titularidad)
        # 1=Pública 2=Privada
        ind_titularidad = "2"
        contenido_xml += '\t\t<ind_titula>' + \
            ind_titularidad + '</ind_titula>\n'
        # Soporte (ind_soporte)
        # 5=Fichero XML Firmado 6=Fichero XML sin firma
        # TODO Actualmente definido como fichero XML sin firma
        ind_soporte = "6"
        contenido_xml += '\t\t<ind_soporte>' + ind_soporte + '</ind_soporte>\n'
        contenido_xml += '\t\t<f_proceso>' + \
            ahora.strftime("%d%m%Y") + '</f_proceso>\n'
        contenido_xml += '\t\t<h_proceso>' + \
            ahora.strftime("%H%M%S") + '</h_proceso>\n'
        contenido_xml += '\t\t<ind_procesado>0</ind_procesado>\n'
        contenido_xml += '\t</reg_cero>\n'

        #######################################################################
        # reg_uno
        #######################################################################
        contenido_xml += '\t<reg_uno>\n'

        # reg_uno/control
        #######################################################################
        # Este nodo es obligatorio en todos los tipos de solicitud.
        contenido_xml += '\t\t<Control>\n'
        contenido_xml += '\t\t\t<id_rock>1</id_rock>\n'
        # Forma de Cumplimentación (forma_c)
        # XML: u - Alta, v - modificación, w - supresión
        # XML Firmado: x - Alta, y - modificación, z - supresión
        # 0 Notificaciones múltiples que contienen altas y/o modificaciones y/o
        # supresiones.
        if (ind_soporte == "5"):
            if (tipo_solicitud == 1):
                forma_c = "x"
            elif (tipo_solicitud == 2):
                forma_c = "y"
            elif (tipo_solicitud == 3):
                forma_c = "z"
        elif (ind_soporte == "6"):
            if (tipo_solicitud == 1):
                forma_c = "u"
            elif (tipo_solicitud == 2):
                forma_c = "v"
            elif (tipo_solicitud == 3):
                forma_c = "w"
        contenido_xml += '\t\t\t<forma_c>' + forma_c + '</forma_c>\n'
        # Formato y versión del documento XML (signatura)
        # Pr000 para privado, Pu000 para público
        signatura = "Pr000"
        contenido_xml += '\t\t\t<signatura>' + signatura + '</signatura>\n'
        # ID de comunicación Web. (id_upload)
        # Siempre es obligatorio. Se generará en cada envío y servirá como identificador para la solicitud.
        # Tiene un formato compuesto de tres códigos contiguos "cifResponsableddmaaaahhmmss":
        # 1) el cif del responsable -9 caracteres-,
        # 2) la fecha del sistema al realizar el envío, con el mes en hexadecimal -7 caracteres-, y
        # 3) la hora del sistema al realizar el envío -6 caracteres-, sin ningún carácter de separación.
        # 22 caracteres en total.
        # TODO: El responsable pertenece a res_partner
        datos_partner = datos_fichero['id_responsable']
        idup_cifres = datos_partner['vat']
        if not idup_cifres:
            _error_datos_responsable('el CIF/NIF')
        else:
            idup_cifres = idup_cifres[2:]
        mes = hex(int(ahora.strftime("%m")))[2:]
        idup_fecha = ahora.strftime(
            "%d") + str(mes) + ahora.strftime("%Y") + ahora.strftime("%H%M%S")
        id_upload = idup_cifres + idup_fecha
        contenido_xml += '\t\t\t<id_upload>' + id_upload + '</id_upload>\n'
        contenido_xml += '\t\t\t<f_web/>\n'
        contenido_xml += '\t\t\t<h_web/>\n'
        contenido_xml += '\t\t\t<num_reg/>\n'
        contenido_xml += '\t\t</Control>\n'

        # reg_uno/declarante/control
        #######################################################################
        contenido_xml += '\t\t<declarante>\n'
        contenido_xml += '\t\t\t<control>\n'
        contenido_xml += '\t\t\t\t<futuro_uso/>\n'
        contenido_xml += '\t\t\t\t<est_err/>\n'
        contenido_xml += '\t\t\t\t<doc_anexa/>\n'
        contenido_xml += '\t\t\t</control>\n'

        # reg_uno/declarante/hoja_solicitud/persona_fisica
        #######################################################################
        # Este nodo es obligatorio en todos los tipos de solicitud.
        # Consulta del declarante
        datos_declarante = datos_fichero['id_declarante']
        contenido_xml += '\t\t\t<hoja_solicitud>\n'
        contenido_xml += '\t\t\t\t<persona_fisica>\n'
        # Razón social (razon_s) Obligatorio Mayúsculas sin acentos, 140
        # caracteres
        razon_s = datos_partner['name']
        razon_s = capitalizar(razon_s)
        contenido_xml += '\t\t\t\t\t<razon_s>' + razon_s + '</razon_s>\n'
        cif_nif = idup_cifres  # datos_partner['vat'][2:]
        cif_nif = capitalizar(cif_nif)
        contenido_xml += '\t\t\t\t\t<cif_nif>' + cif_nif + '</cif_nif>\n'
        nombre = datos_declarante['name']
        nombre = capitalizar(nombre)
        contenido_xml += '\t\t\t\t\t<nombre>' + nombre + '</nombre>\n'
        apellido1 = datos_declarante['apellido1']
        apellido1 = capitalizar(apellido1)
        contenido_xml += '\t\t\t\t\t<apellido1>' + apellido1 + '</apellido1>\n'
        apellido2 = datos_declarante['apellido2']
        apellido2 = capitalizar(apellido2)
        contenido_xml += '\t\t\t\t\t<apellido2>' + apellido2 + '</apellido2>\n'
        # NIF del declarante
        nif = datos_declarante['nif']
        nif = capitalizar(nif)
        contenido_xml += '\t\t\t\t\t<nif>' + nif + '</nif>\n'
        # TODO: Si se asigna de hr.job leer de la db el cargo
        cargo = datos_declarante['cargo']
        cargo = capitalizar(cargo)
        contenido_xml += '\t\t\t\t\t<cargo>' + cargo + '</cargo>\n'
        contenido_xml += '\t\t\t\t</persona_fisica>\n'

        # reg_uno/declarante/hoja_solicitud/direccion_notif
        #######################################################################
        # Este nodo es obligatorio en todos los tipos de solicitud.
        contenido_xml += '\t\t\t\t<direccion_notif>\n'
        denomina_p = datos_declarante['denomina_p']
        denomina_p = capitalizar(denomina_p)
        contenido_xml += '\t\t\t\t\t<denomina_p>' + \
            denomina_p + '</denomina_p>\n'
        dir_postal = datos_declarante['dir_postal']
        dir_postal = capitalizar(dir_postal)
        contenido_xml += '\t\t\t\t\t<dir_postal>' + \
            dir_postal + '</dir_postal>\n'
        # Se obtiene asigna el pais del declarante
        pais_declarante = datos_declarante['pais']
        pais = pais_declarante['code']
        pais = capitalizar(pais)
        contenido_xml += '\t\t\t\t\t<pais>' + pais + '</pais>\n'
        # Se asigna la provincia del declarante
        provincia_declarante = datos_declarante['provincia']
        provincia = provincia_declarante['code']
        contenido_xml += '\t\t\t\t\t<provincia>' + provincia + '</provincia>\n'
        localidad = datos_declarante['localidad']
        localidad = capitalizar(localidad)
        contenido_xml += '\t\t\t\t\t<localidad>' + localidad + '</localidad>\n'
        postal = datos_declarante['postal']
        contenido_xml += '\t\t\t\t\t<postal>' + postal + '</postal>\n'
        telefono = datos_declarante['telefono']
        telefono = sin_espacios(telefono)
        if (telefono):
            contenido_xml += '\t\t\t\t\t<telefono>' + \
                telefono + '</telefono>\n'
        else:
            contenido_xml += '\t\t\t\t\t<telefono/>\n'
        fax = datos_declarante['fax']
        fax = sin_espacios(fax)
        if (fax):
            contenido_xml += '\t\t\t\t\t<fax>' + fax + '</fax>\n'
        else:
            contenido_xml += '\t\t\t\t\t<fax/>\n'
        email = datos_declarante['email']
        if (email):
            email = minimizar(email)
            contenido_xml += '\t\t\t\t\t<email>' + email + '</email>\n'
        else:
            contenido_xml += '\t\t\t\t\t<email/>\n'
        # Medio de notificación (forma)
        # 1 - Correo postal (Sin firma digital)
        # 2 - DEU-SNTS (Dirección Electrónica Única del Servicio de
        # Notificaciones Telemáticas Seguras)
        forma = 1  # TODO: 1 - Sin firma digital
        contenido_xml += '\t\t\t\t\t<forma>' + str(forma) + '</forma>\n'
        # Dirección electrónica del servicio de notificaciones (Id_notific)
        # Vacío en los envíos realizados sin firma digital.
        Id_notific = ""  # TODO: modificar en caso de incluir firma digital
        Id_notific = capitalizar(Id_notific)
        if (Id_notific):
            contenido_xml += '\t\t\t\t\t<Id_notific>' + \
                Id_notific + '</Id_notific>\n'
        else:
            contenido_xml += '\t\t\t\t\t<Id_notific/>\n'
        # Conocimiento de los deberes del declarane
        contenido_xml += '\t\t\t\t\t<ind_deberes>1</ind_deberes>\n'
        contenido_xml += '\t\t\t\t</direccion_notif>\n'
        contenido_xml += '\t\t\t</hoja_solicitud>\n'
        contenido_xml += '\t\t</declarante>\n'

        # reg_uno/declaracion
        #######################################################################
        contenido_xml += '\t\t<declaracion>\n'
        contenido_xml += '\t\t\t<responsable>\n'

        # reg_uno/declaracion/responsable/control
        #######################################################################
        # Consulta 'address' del responsable
        datos = self.pool.get('res.partner.address').search(
            cr, uid, [('partner_id', '=', datos_partner['id'])])
        datos_responsable = self.pool.get(
            'res.partner.address').browse(cr, uid, datos[0])

        contenido_xml += '\t\t\t\t<control>\n'
        # Ordinal del responsable para el declarante del envío (ordinal)
        # ordinal debe ser un número secuencial entre 01 y 99
        # TODO: modificar en caso de declarar más de un fichero con diferentes
        # responsables
        ordinal = "01"
        contenido_xml += '\t\t\t\t\t<ordinal>' + ordinal + '</ordinal>\n'
        contenido_xml += '\t\t\t\t\t<est_err/>\n'
        contenido_xml += '\t\t\t\t\t<texto_libre/>\n'
        contenido_xml += '\t\t\t\t</control>\n'

        # reg_uno/declaracion/responsable/responsable_fichero
        #######################################################################
        # Datos del responsable de fichero o tratamiento. Este apartado es obligatorio en cualquier tipo de solicitud.
        # TODO El responsable proviene de partner_address
        contenido_xml += '\t\t\t\t<responsable_fichero>\n'
        cif = datos_partner['vat'][2:]
        contenido_xml += '\t\t\t\t\t<cif>' + cif + '</cif>\n'
        if not datos_responsable['street']:
            _error_datos_responsable('la dirección')
        dir_postal = datos_responsable['street']
        dir_postal = capitalizar(dir_postal)
        contenido_xml += '\t\t\t\t\t<dir_postal>' + \
            dir_postal + '</dir_postal>\n'
        if not datos_responsable['zip']:
            _error_datos_responsable('el código postal')
        postal = datos_responsable['zip']
        contenido_xml += '\t\t\t\t\t<postal>' + postal + '</postal>\n'
        if not datos_responsable['city']:
            _error_datos_responsable('la localidad')
        localidad = datos_responsable['city']
        localidad = capitalizar(localidad)
        contenido_xml += '\t\t\t\t\t<localidad>' + localidad + '</localidad>\n'
        # Asignación para obtener la provincia del responsable
        if not datos_responsable['state_id']:
            _error_datos_responsable('la provincia')
        provincia_responsable = datos_responsable['state_id']
        provincia = provincia_responsable['code']
        contenido_xml += '\t\t\t\t\t<provincia>' + provincia + '</provincia>\n'
        # Asignación para obtener el pais del responsable
        if not datos_responsable['country_id']:
            _error_datos_responsable('el pais')
        pais_responsable = datos_responsable['country_id']
        pais = pais_responsable['code']
        pais = capitalizar(pais)
        contenido_xml += '\t\t\t\t\t<pais>' + pais + '</pais>\n'
        telefono = datos_responsable['phone']
        telefono = sin_espacios(telefono)
        if (telefono):
            contenido_xml += '\t\t\t\t\t<telefono>' + \
                telefono + '</telefono>\n'
        else:
            contenido_xml += '\t\t\t\t\t<telefono/>\n'
        fax = datos_responsable['fax']
        fax = sin_espacios(fax)
        if (fax):
            contenido_xml += '\t\t\t\t\t<fax>' + fax + '</fax>\n'
        else:
            contenido_xml += '\t\t\t\t\t<fax/>\n'
        email = datos_responsable['email']
        if (email):
            email = minimizar(email)
            contenido_xml += '\t\t\t\t\t<email>' + email + '</email>\n'
        else:
            contenido_xml += '\t\t\t\t\t<email/>\n'
        if not datos_responsable['name']:
            _error_datos_responsable('el nombre o razón social')
        n_razon = datos_responsable['name']
        n_razon = capitalizar(n_razon)
        contenido_xml += '\t\t\t\t\t<n_razon>' + n_razon + '</n_razon>\n'
        # Asignación para obtener el código de actividad #TODO: Modificar si
        # cambia el origen de los datos del responsable
        if not datos_partner['actividad']:
            _error_datos_responsable('la actividad')
        actividad_responsable = datos_partner['actividad']
        # Código de actividad principal (cap)
        cap = actividad_responsable['codigo']
        contenido_xml += '\t\t\t\t\t<cap>' + cap + '</cap>\n'
        # tip_admin, cod_automia, denomina_ente, denomina_dirdep,
        # denomina_organo (Sólo para ficheros de titularidad pública)
        contenido_xml += '\t\t\t\t\t<tip_admin/>\n'
        contenido_xml += '\t\t\t\t\t<cod_automia/>\n'
        contenido_xml += '\t\t\t\t\t<denomina_ente/>\n'
        contenido_xml += '\t\t\t\t\t<denomina_dirdep/>\n'
        contenido_xml += '\t\t\t\t\t<denomina_organo/>\n'
        contenido_xml += '\t\t\t\t</responsable_fichero>\n'

        # reg_uno/declaracion/responsable/derecho
        #######################################################################
        # Derechos de oposición, acceso, rectificación y cancelación.

        # En solicitudes de alta este apartado no es obligatorio ya que
        # únicamente se deberá cumplimentar en el caso de que el domicilio
        # donde se vaya a atender los derechos del ciudadano sea distinto que
        # el domicilio del responsable. Así pues, si el domicilio es el mismo
        # que el del responsable, estos elementos vendrán vacíos. No obstante,
        # si se cumplimenta algún elemento, entonces deberán estar
        # cumplimentados todos aquellos elementos que a continuación se
        # establecen como obligatorios.

        # Ahora bien, en el caso de que el responsable este ubicado fuera de la
        # Unión Europea, entonces este apartado ES OBLIGATORIO por lo que, en
        # ese caso, deberán cumplimentarse todos los apartados establecidos a
        # continuación como obligatorios y, además, el elemento pais de este
        # nodo deberá ser 'ES'.

        # En solicitudes de modificación, se deberá rellenar este nodo en el
        # caso de que se haya asignado un valor "1" en el elemento
        # Envio/reg_uno/declaración/fichero/control/acciones_mod/servicio_unidad,
        # en cuyo caso se cumplimentarán, al menos, todos los elementos del
        # nodo que se establecen como obligatorios.

        # En solicitudes de supresión, este nodo deberá venir vacío.

        # Tipo de solicitud (tipo_solicitud)
        # 1 ALTA
        # 2 MODIFICACIÓN
        # 3 SUPRESIÓN
        # tipo_solicitud (pasada por parámetro a la función)

        # mod_serv -> en tipos de solicitud de modificación determina si se ha
        # modifiacado servicio_unidad
        mod_serv = datos_fichero['mod_serv']
        if datos_fichero['id_responsable'] == datos_fichero['id_unidad']:
            responsable_diferente = False
        else:
            # True si la dirección de la Ud. de ejercicio de derecho es
            # diferente al responsable
            responsable_diferente = True

        contenido_xml += '\t\t\t\t<derecho>\n'
        if (tipo_solicitud == 1 or (tipo_solicitud == 2 and mod_serv)) and responsable_diferente:
            # TODO: La unidad de ejercicio de derechos se obtiene de res_partner
            # Se obtiene la unidad de ejercicio de derechos de res_partner y se
            # almacena en partner_unidad
            partner_unidad = datos_fichero['id_unidad']
            # Se obtienen los datos de la unidad de ejercicio de derechos y se
            # almacena en datos_unidad
            datos = self.pool.get('res.partner.address').search(
                cr, uid, [('partner_id', '=', datos_fichero['id_unidad']['id'])])
            if not datos:
                _error_datos_unidad('la información de contacto')
            datos_unidad = self.pool.get(
                'res.partner.address').browse(cr, uid, datos[0])
            if not datos_unidad['name']:
                _error_datos_unidad('el nombre de la oficina / razón social')
            oficina = datos_unidad['name']
            oficina = capitalizar(oficina)
            if not oficina:
                _error_datos_unidad('la ofinica')
            contenido_xml += '\t\t\t\t\t<oficina>' + oficina + '</oficina>\n'
            try:
                nif_cif = partner_unidad['vat'][2:]
            except:
                _error_datos_unidad('el NIF/CIF')
            contenido_xml += '\t\t\t\t\t<nif_cif>' + nif_cif + '<nif_cif>\n'
            if not datos_unidad['street']:
                _error_datos_unidad('la dirección postal')
            dir_postal = datos_unidad['street']
            dir_postal = capitalizar(dir_postal)
            contenido_xml += '\t\t\t\t\t<dir_postal>' + \
                dir_postal + '</dir_postal>\n'
            if not datos_unidad['city']:
                _error_datos_unidad('la localidad')
            localidad = datos_unidad['city']
            localidad = capitalizar(localidad)
            contenido_xml += '\t\t\t\t\t<localidad>' + \
                localidad + '</localidad>\n'
            if not datos_unidad['zip']:
                _error_datos_unidad('el código postal')
            postal = datos_unidad['zip']
            contenido_xml += '\t\t\t\t\t<postal>' + postal + '</postal>\n'
            if not datos_unidad['state_id']:
                _error_datos_unidad('la provincia')
            # Asignación de la provincia de la unidad de derecho
            provincia_unidad = datos_unidad['state_id']
            provincia = provincia_unidad['code']
            contenido_xml += '\t\t\t\t\t<provincia>' + \
                provincia + '</provincia>\n'
            if not datos_unidad['country_id']:
                _error_datos_unidad('el pais')
            # Asignación del pais de la unidad de derecho
            pais_unidad = datos_unidad['country_id']
            pais = pais_unidad['code']
            pais = capitalizar(pais)
            if (pais):
                contenido_xml += '\t\t\t\t\t<pais>' + pais + '</pais>\n'
            else:
                contenido_xml += '\t\t\t\t\t<pais/>\n'
            telefono = datos_unidad['phone']
            telefono = sin_espacios(telefono)
            if (telefono):
                contenido_xml += '\t\t\t\t\t<telefono>' + \
                    telefono + '</telefono>\n'
            else:
                contenido_xml += '\t\t\t\t\t<telefono/>\n'
            fax = datos_unidad['fax']
            fax = sin_espacios(fax)
            if (fax):
                contenido_xml += '\t\t\t\t\t<fax>' + fax + '</fax>\n'
            else:
                contenido_xml += '\t\t\t\t\t<fax/>\n'
            email = datos_unidad['email']
            if email:
                email = minimizar(email)
                contenido_xml += '\t\t\t\t\t<email>' + email + '</email>\n'
            else:
                contenido_xml += '\t\t\t\t\t<email/>\n'
        else:
            contenido_xml += '\t\t\t\t\t<oficina/>\n'
            contenido_xml += '\t\t\t\t\t<nif_cif/>\n'
            contenido_xml += '\t\t\t\t\t<dir_postal/>\n'
            contenido_xml += '\t\t\t\t\t<localidad/>\n'
            contenido_xml += '\t\t\t\t\t<postal/>\n'
            contenido_xml += '\t\t\t\t\t<provincia/>\n'
            contenido_xml += '\t\t\t\t\t<pais/>\n'
            contenido_xml += '\t\t\t\t\t<telefono/>\n'
            contenido_xml += '\t\t\t\t\t<fax/>\n'
            contenido_xml += '\t\t\t\t\t<email/>\n'
        contenido_xml += '\t\t\t\t</derecho>\n'
        contenido_xml += '\t\t\t</responsable>\n'

        # reg_uno/declaracion/fichero/control/acciones_generales
        #######################################################################
        contenido_xml += '\t\t\t<fichero>\n'
        contenido_xml += '\t\t\t\t<control>\n'
        contenido_xml += '\t\t\t\t\t<acciones_generales>\n'
        # Ordinal del Fichero para el responsable y declarante del envío (ordinal)
        # ordinal debe ser un número secuencial entre 0001 y 9999
        # TODO: modificar en caso de que se declarasen varios ficheros en 1
        # solicitud
        ordinal = "0001"
        contenido_xml += '\t\t\t\t\t\t<ordinal>' + ordinal + '</ordinal>\n'
        contenido_xml += '\t\t\t\t\t\t<tipo_solicitud>' + \
            str(tipo_solicitud) + '</tipo_solicitud>\n'
        contenido_xml += '\t\t\t\t\t\t<est_err/>\n'
        contenido_xml += '\t\t\t\t\t\t<doc_anexa/>\n'
        contenido_xml += '\t\t\t\t\t</acciones_generales>\n'

        # reg_uno/declaracion/fichero/control/acciones_not_alta
        #######################################################################
        contenido_xml += '\t\t\t\t\t<acciones_not_alta>\n'
        contenido_xml += '\t\t\t\t\t\t<fecha_reg/>\n'
        contenido_xml += '\t\t\t\t\t\t<num_reg/>\n'
        contenido_xml += '\t\t\t\t\t\t<id_resolucion/>\n'
        contenido_xml += '\t\t\t\t\t</acciones_not_alta>\n'

        # reg_uno/declaracion/fichero/control/acciones_mod
        #######################################################################
        # Campos de control para la solicitud de modificación de un fichero inscrito con anterioridad.
        # Vendrán vacíos los elementos de este nodo si el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_generales/tipo_solicitud tiene valor "1" ó "3".
        # Si el valor del citado elemento es "2", se cumplimentarán con valor "1" aquellos elementos correspondientes a los apartados de los que se notifica la modificación de los datos que figuran inscritos en el Registro General de Protección de Datos, y tendrán valor "0" aquellos elementos correspondientes a los apartados que no sufran variación.
        # Deberá haber al menos un elemento correspondiente a los apartados a
        # modificar que tenga valor "1".

        # Asimismo, si se cumplimenta este nodo también deberá cumplimentarse el elemento
        # Envio/reg_uno/declaracion/fichero/identifica_finalidad/denominación/c_inscripcion
        # indicando el código de inscripción del fichero cuya modificación se
        # solicita.

        contenido_xml += '\t\t\t\t\t<acciones_mod>\n'
        if (tipo_solicitud == 1 or tipo_solicitud == 3):
            contenido_xml += '\t\t\t\t\t\t<responsable/>\n'
            contenido_xml += '\t\t\t\t\t\t<cif_nif_ant/>\n'
            contenido_xml += '\t\t\t\t\t\t<servicio_unidad/>\n'
            contenido_xml += '\t\t\t\t\t\t<disposicion/>\n'
            contenido_xml += '\t\t\t\t\t\t<iden_finalid/>\n'
            contenido_xml += '\t\t\t\t\t\t<encargado/>\n'
            contenido_xml += '\t\t\t\t\t\t<estruct_sistema/>\n'
            contenido_xml += '\t\t\t\t\t\t<medidas_seg/>\n'
            contenido_xml += '\t\t\t\t\t\t<origen/>\n'
            contenido_xml += '\t\t\t\t\t\t<trans_inter/>\n'
            contenido_xml += '\t\t\t\t\t\t<comunic_ces/>\n'
        elif (tipo_solicitud == 2):
            # Indica si se ha modificado el responsable
            mod_res = datos_fichero['mod_res']
            if (mod_res):
                contenido_xml += '\t\t\t\t\t\t<responsable>1</responsable>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<responsable/>\n'
            # CIF/NIF Anterior (mod_cif_nif)
            # En caso de modificaciones se deber hacer constar el CIF o NIF del
            # Responsable con el que figura inscrito el fichero en el Registro
            # General de Protección de Datos.
            mod_cif_nif = datos_fichero['mod_cif_nif']
            if (mod_cif_nif):
                contenido_xml += '\t\t\t\t\t\t<cif_nif_ant>' + \
                    mod_cif_nif + '</cif_nif_ant>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<cif_nif_ant/>\n'
            # mod_serv = datos_fichero['mod_serv'] # Asignado previamente
            # Indica si se ha modificado el servicio o unidad de acceso
            if (mod_serv):
                contenido_xml += '\t\t\t\t\t\t<servicio_unidad>1</servicio_unidad>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<servicio_unidad/>\n'
            mod_disp = False  # Sólo para ficheros de titularidad pública
            if (mod_disp):
                contenido_xml += '\t\t\t\t\t\t<disposicion>1</disposicion>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<disposicion/>\n'
            # Indica modificación de los datos descriptivos del fichero y sus
            # finalidades
            mod_iden = datos_fichero['mod_iden']
            if (mod_iden):
                contenido_xml += '\t\t\t\t\t\t<iden_finalid>1</iden_finalid>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<iden_finalid/>\n'
            # Indica modificación de los datos del encargado de tratamiento
            mod_enc = datos_fichero['mod_enc']
            if (mod_enc):
                contenido_xml += '\t\t\t\t\t\t<encargado>1</encargado>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<encargado/>\n'
            # Indica modificación de los tipos de datos, estructura o sistema
            # de tratamiento
            mod_est = datos_fichero['mod_est']
            if (mod_est):
                contenido_xml += '\t\t\t\t\t\t<estruct_sistema>1</estruct_sistema>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<estruct_sistema/>\n'
            # Indica modificación de las medidas de seguridad y auditorías
            mod_med = datos_fichero['mod_med']
            if (mod_med):
                contenido_xml += '\t\t\t\t\t\t<medidas_seg>1</medidas_seg>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<medidas_seg/>\n'
            # Indica modificación del origen y procedencia de los datos
            mod_org = datos_fichero['mod_org']
            if (mod_org):
                contenido_xml += '\t\t\t\t\t\t<origen>1</origen>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<origen/>\n'
            # Indica modificación de la información referida a transferencias
            # internacionales
            mod_tra = datos_fichero['mod_tra']
            if (mod_tra):
                contenido_xml += '\t\t\t\t\t\t<trans_inter>1</trans_inter>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<trans_inter/>\n'
            # Indica modificación de la información referida a comunicación de
            # datos
            mod_com = datos_fichero['mod_com']
            if (mod_com):
                contenido_xml += '\t\t\t\t\t\t<comunic_ces>1</comunic_ces>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<comunic_ces/>\n'

        contenido_xml += '\t\t\t\t\t</acciones_mod>\n'

        # reg_uno/declaracion/fichero/control/acciones_supr
        #######################################################################
        # Campos de control para la solicitud de supresión de un fichero inscrito con anterioridad.
        # Vendrán vacíos los elementos de este nodo si el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_generales/tipo_solicitud tiene valor "1" ó "2".
        # Si el valor del citado elemento es "3", deberán cumplimentarse los
        # siguientes elementos:
        contenido_xml += '\t\t\t\t\t<acciones_supr>\n'
        if (tipo_solicitud == 3):
            # Motivos de la supresión (pasados por parámetro)
            motivos = capitalizar(motivos)
            contenido_xml += '\t\t\t\t\t\t<motivos>' + motivos + '</motivos>\n'
            # Destino de la información y Previsiones Adoptadas para su
            # destrucción (pasados por parámetro)
            destino_previsiones = capitalizar(destino_previsiones)
            contenido_xml += '\t\t\t\t\t\t<destino_previsiones>' + \
                destino_previsiones + '</destino_previsiones>\n'
            # CIF/NIF del responsable
            # TODO datos obtenidos del partner responsable
            nif_cif = datos_partner['vat'][2:]
            contenido_xml += '\t\t\t\t\t\t<cifnif>' + nif_cif + '</cifnif>\n'
        elif (tipo_solicitud == 1 or tipo_solicitud == 2):
            contenido_xml += '\t\t\t\t\t\t<motivos/>\n'
            contenido_xml += '\t\t\t\t\t\t<destino_previsiones/>\n'
            contenido_xml += '\t\t\t\t\t\t<cifnif/>\n'
        contenido_xml += '\t\t\t\t\t</acciones_supr>\n'
        contenido_xml += '\t\t\t\t</control>\n'

        # reg_uno/declaracion/fichero/dispo_gen_cms
        #######################################################################
        # Este apartado se refiere a la disposición general de creación,
        # modificación o supresión de ficheros de titularidad pública, por lo
        # que en las notificaciones de titularidad privada todos los elementos
        # de este nodo deberán venir vacíos.

        contenido_xml += '\t\t\t\t<dispo_gen_cms>\n'
        contenido_xml += '\t\t\t\t\t<cod_boletin/>\n'
        contenido_xml += '\t\t\t\t\t<num_boletin/>\n'
        contenido_xml += '\t\t\t\t\t<fecha/>\n'
        contenido_xml += '\t\t\t\t\t<disposicion/>\n'
        contenido_xml += '\t\t\t\t\t<url/>\n'
        contenido_xml += '\t\t\t\t</dispo_gen_cms>\n'

        # reg_uno/declaracion/fichero/encargado
        #######################################################################
        # Datos del encargado del fichero.

        # En notificaciones de alta este apartado no es obligatorio ya que
        # únicamente se deberá cumplimentar en el caso de que el tratamiento de
        # los datos se realice por persona, física o jurídica, distinta al
        # responsable del fichero. Así pues, si el tratamiento lo realiza el
        # propio responsable, estos elementos vendrán vacíos. No obstante, si
        # se cumplimenta algún elemento, entonces deberán estar cumplimentados
        # todos aquellos elementos que a continuación se establecen como
        # obligatorios.

        # En notificaciones de modificación, deberán cumplimentarse -al menos- los elementos que a continuación se especifican como obligatorios en el caso de que se haya indicado un valor "1" en el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/encargado.

        # En notificaciones de supresión, los elementos de este nodo vendrán
        # vacíos.

        if datos_fichero['id_encargado'][0] == datos_fichero['id_responsable']:
            encargado_tratamiento = False
        else:
            # es necesario especificar el encargado
            encargado_tratamiento = True
        # Se asigna la id del 1er encargado en la relación
        id_encargado = datos_fichero['id_encargado'][0]['id']

        contenido_xml += '\t\t\t\t<encargado>\n'
        if ((tipo_solicitud == 1 and not(encargado_tratamiento)) or (tipo_solicitud == 2 and not(mod_enc)) or (tipo_solicitud == 3)):
            contenido_xml += '\t\t\t\t\t<n_razon/>\n'
            contenido_xml += '\t\t\t\t\t<cif_nif/>\n'
            contenido_xml += '\t\t\t\t\t<dir_postal/>\n'
            contenido_xml += '\t\t\t\t\t<localidad/>\n'
            contenido_xml += '\t\t\t\t\t<postal/>\n'
            contenido_xml += '\t\t\t\t\t<provincia/>\n'
            contenido_xml += '\t\t\t\t\t<pais/>\n'
            contenido_xml += '\t\t\t\t\t<telefono/>\n'
            contenido_xml += '\t\t\t\t\t<fax/>\n'
            contenido_xml += '\t\t\t\t\t<email/>\n'
        elif ((tipo_solicitud == 1 and encargado_tratamiento) or (tipo_solicitud == 2 and mod_enc)):
            # Se obtiene el partner encargado y se almacena en
            # partner_encargado
            datos = self.pool.get('res.partner').search(
                cr, uid, [('id', '=', id_encargado)])
            partner_encargado = self.pool.get(
                'res.partner').browse(cr, uid, datos[0])
            # Se obtienen los datos del encargado y se almacena en
            # datos_encargado
            datos = self.pool.get('res.partner.address').search(
                cr, uid, [('partner_id', '=', id_encargado)])
            if not datos:
                _error_datos_encargado('la información de contacto')
            datos_encargado = self.pool.get(
                'res.partner.address').browse(cr, uid, datos[0])
            if not datos_encargado['name']:
                _error_datos_encargado('el nombre o razón social')
            n_razon = datos_encargado['name']
            n_razon = capitalizar(n_razon)
            contenido_xml += '\t\t\t\t\t<n_razon>' + n_razon + '</n_razon>\n'
            try:
                cif_nif = partner_encargado['vat'][2:]
            except:
                _error_datos_encargado('el CIF/NIF')
            contenido_xml += '\t\t\t\t\t<cif_nif>' + cif_nif + '</cif_nif>\n'
            if not datos_encargado['street']:
                _error_datos_encargado('la dirección')
            dir_postal = datos_encargado['street']
            dir_postal = capitalizar(dir_postal)
            contenido_xml += '\t\t\t\t\t<dir_postal>' + \
                dir_postal + '</dir_postal>\n'
            if not datos_encargado['city']:
                _error_datos_encargado('la localidad')
            localidad = datos_encargado['city']
            localidad = capitalizar(localidad)
            contenido_xml += '\t\t\t\t\t<localidad>' + \
                localidad + '</localidad>\n'
            if not datos_encargado['zip']:
                _error_datos_encargado('el código postal')
            postal = datos_encargado['zip']
            contenido_xml += '\t\t\t\t\t<postal>' + postal + '</postal>\n'
            # Consulta para obtener la provincia del encargado
            if not datos_encargado['state_id']:
                _error_datos_unidad('la provincia')
            else:
                provincia_encargado = datos_encargado['state_id']
            provincia = provincia_encargado['code']
            contenido_xml += '\t\t\t\t\t<provincia>' + \
                provincia + '</provincia>\n'
            # Cosulta para obtener el pais del encargado
            if not datos_encargado['country_id']:
                _error_datos_unidad('el pais')
            else:
                pais_encargado = datos_encargado['country_id']
            pais = pais_encargado['code']
            pais = capitalizar(pais)
            contenido_xml += '\t\t\t\t\t<pais>' + pais + '</pais>\n'
            telefono = datos_encargado['phone']
            if (telefono):
                contenido_xml += '\t\t\t\t\t<telefono>' + \
                    telefono + '</telefono>\n'
            else:
                contenido_xml += '\t\t\t\t\t<telefono/>\n'
            fax = datos_encargado['fax']
            if (fax):
                contenido_xml += '\t\t\t\t\t<fax>' + fax + '</fax>\n'
            else:
                contenido_xml += '\t\t\t\t\t<fax/>\n'
            email = datos_encargado['email']
            if email:
                email = minimizar(email)
                contenido_xml += '\t\t\t\t\t<email>' + email + '</email>\n'
            else:
                contenido_xml += '\t\t\t\t\t<email/>\n'
        contenido_xml += '\t\t\t\t</encargado>\n'

        # reg_uno/declaracion/fichero/identifica_finalidad/denominacion
        #######################################################################
        # En solicitudes de modificación, deberá cumplimentarse este nodo cuando se haya indicado un valor "1" en el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/iden_finalid
        # (en este supuesto, también debe cumplimentarse el nodo
        # Envio/reg_uno/declaracion/fichero/identifica_finalidad/tipificacion).

        # Con independencia del valor consignando en el citado elemento, en
        # solicitudes de modificación siempre se deberá cumplimentar el
        # elemento <c_inscripcion>.

        # En solicitudes de supresión, los elementos de este nodo vendrán
        # vacíos, salvo lo indicado para el elemento <c_inscripcion>.

        contenido_xml += '\t\t\t\t<identifica_finalidad>\n'
        contenido_xml += '\t\t\t\t\t<denominacion>\n'
        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_iden))):
            contenido_xml += '\t\t\t\t\t\t<fichero/>\n'
            c_inscripcion = datos_fichero['codigo_agencia']
            contenido_xml += '\t\t\t\t\t\t<c_inscripcion>' + \
                c_inscripcion + '</c_inscripcion>\n'
            contenido_xml += '\t\t\t\t\t\t<c_inscrip_t/>\n'
            contenido_xml += '\t\t\t\t\t\t<f_inscrip/>\n'
            contenido_xml += '\t\t\t\t\t\t<desc_fin_usos/>\n'
        elif (tipo_solicitud == 1 or (tipo_solicitud == 2 and mod_iden)):
            fichero = datos_fichero['name']
            fichero = capitalizar(fichero)
            contenido_xml += '\t\t\t\t\t\t<fichero>' + fichero + '</fichero>\n'
            if (tipo_solicitud == 1):
                contenido_xml += '\t\t\t\t\t\t<c_inscripcion/>\n'
            else:
                c_inscripcion = datos_fichero['codigo_agencia']
                contenido_xml += '\t\t\t\t\t\t<c_inscripcion>' + \
                    c_inscripcion + '</c_inscripcion>\n'
            contenido_xml += '\t\t\t\t\t\t<c_inscrip_t/>\n'
            contenido_xml += '\t\t\t\t\t\t<f_inscrip/>\n'
            desc_fin_usos = datos_fichero['descripcion']
            desc_fin_usos = capitalizar(desc_fin_usos)
            contenido_xml += '\t\t\t\t\t\t<desc_fin_usos>' + \
                desc_fin_usos + '</desc_fin_usos>\n'
        contenido_xml += '\t\t\t\t\t</denominacion>\n'

        # reg_uno/declaracion/fichero/identifica_finalidad/tipificacion
        #######################################################################
        # En solicitudes de alta, este nodo es obligatorio.

        # En solicitudes de modificación, deberá cumplimentarse este nodo cuando se haya indicado un valor "1" en el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/iden_finalid
        # (en este caso, también deben cumplimentarse -al menos- los campos indicados como obligatorios en el nodo
        # Envio/reg_uno/declaracion/fichero/identifica_finalidad/denominacion).

        # En solicitudes de supresión, el elemento de este nodo vendrá vacío.

        contenido_xml += '\t\t\t\t\t<tipificacion>\n'
        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_iden))):
            contenido_xml += '\t\t\t\t\t\t<finalidades/>\n'
        else:
            finalidades = datos_fichero['finalidad']
            contenido_xml += '\t\t\t\t\t\t<finalidades>' + \
                finalidades + '</finalidades>\n'
        contenido_xml += '\t\t\t\t\t</tipificacion>\n'
        contenido_xml += '\t\t\t\t</identifica_finalidad>\n'

        # reg_uno/declaracion/fichero/procedencia/origen
        #######################################################################
        # Especifica el origen de los datos.

        # En notificaciones de alta este apartado es obligatorio, por lo que al menos un elemento deberá tener valor "1".
        # En modificación, deberán cumplimentarse cuando se haya indicado un valor "1" en el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/origen, debiendo también cumplimentar el nodo
        # Envio/reg_uno/declaracion/fichero/procedencia/colectivos_categ

        # En notificaciones de supresión los elementos de este nodo vendrán
        # vacíos.

        contenido_xml += '\t\t\t\t<procedencia>\n'
        contenido_xml += '\t\t\t\t\t<origen>\n'
        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_org))):
            contenido_xml += '\t\t\t\t\t\t<indica_inte/>\n'
            contenido_xml += '\t\t\t\t\t\t<indica_otras/>\n'
            contenido_xml += '\t\t\t\t\t\t<indic_fap/>\n'
            contenido_xml += '\t\t\t\t\t\t<indic_rp/>\n'
            contenido_xml += '\t\t\t\t\t\t<indic_ep/>\n'
            contenido_xml += '\t\t\t\t\t\t<indic_ap/>\n'
        else:
            indica_inte = boolean2num(datos_fichero['interesado'])
            contenido_xml += '\t\t\t\t\t\t<indica_inte>' + \
                indica_inte + '</indica_inte>\n'
            indica_otras = boolean2num(datos_fichero['otras'])
            contenido_xml += '\t\t\t\t\t\t<indica_otras>' + \
                indica_otras + '</indica_otras>\n'
            indic_fap = boolean2num(datos_fichero['fue_publica'])
            contenido_xml += '\t\t\t\t\t\t<indic_fap>' + \
                indic_fap + '</indic_fap>\n'
            indic_rp = boolean2num(datos_fichero['reg_publico'])
            contenido_xml += '\t\t\t\t\t\t<indic_rp>' + \
                indic_rp + '</indic_rp>\n'
            indic_ep = boolean2num(datos_fichero['ent_privada'])
            contenido_xml += '\t\t\t\t\t\t<indic_ep>' + \
                indic_ep + '</indic_ep>\n'
            indic_ap = boolean2num(datos_fichero['adm_publica'])
            contenido_xml += '\t\t\t\t\t\t<indic_ap>' + \
                indic_ap + '</indic_ap>\n'

        contenido_xml += '\t\t\t\t\t</origen>\n'

        # reg_uno/declaracion/fichero/procedencia/colectivos_categ
        #######################################################################
        # Colectivos o categorías de interesados.

        # En notificaciones de alta este apartado es obligatorio. Deberá
        # indicarse en el elemento colectivos al menos una categoría de
        # colectivo o bien, en el caso de que ninguna de las categorías de la
        # tabla describa adecuadamente el colectivo, se cumplimentará con texto
        # una breve descripción del colectivo en el elemento otro_col. Si
        # alguno de los elementos no se cumplimenta, entonces vendrá vacío.

        # En notificaciones de modificación, deberán cumplimentarse cuando se haya indicado un valor "1" en el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/origen, debiendo también cumplimentar el nodo
        # Envio/reg_uno/declaracion/fichero/procedencia/origen.

        # En notificaciones de supresión los elementos de este nodo vendrán
        # vacíos.

        contenido_xml += '\t\t\t\t\t<colectivos_categ>\n'

        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_org))):
            contenido_xml += '\t\t\t\t\t\t<colectivos/>\n'
            contenido_xml += '\t\t\t\t\t\t<otro_col/>\n'
        else:
            colectivos = datos_fichero['colectivos']
            if colectivos:
                contenido_xml += '\t\t\t\t\t\t<colectivos>' + \
                    colectivos + '</colectivos>\n'
                contenido_xml += '\t\t\t\t\t\t<otro_col/>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<colectivos/>\n'
                otro_col = datos_fichero['otros_colectivos']
                if (otro_col):
                    otro_col = capitalizar(otro_col)
                    contenido_xml += '\t\t\t\t\t\t<otro_col>' + \
                        otro_col + '</otro_col>\n'
                else:
                    contenido_xml += '\t\t\t\t\t\t<otro_col/>\n'
        contenido_xml += '\t\t\t\t\t</colectivos_categ>\n'
        contenido_xml += '\t\t\t\t</procedencia>\n'

        # reg_uno/declaracion/fichero/medidas_seg
        #######################################################################
        # Se especifica el nivel de seguridad.
        # En notificaciones de alta es obligatorio el elemento nivel, y los
        # elementos f_audit y t_audit vendrán vacíos.

        # En notificaciones de modificación, se cumplimentará cuando se haya indicado un valor "1" en el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/medidas_seg

        # En notificaciones de supresión los elementos de este nodo vendrán
        # vacíos.

        contenido_xml += '\t\t\t\t<medidas_seg>\n'
        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_med))):
            contenido_xml += '\t\t\t\t\t<nivel/>\n'
        else:
            nivel = datos_fichero['nivel']
            contenido_xml += '\t\t\t\t\t<nivel>' + nivel + '</nivel>\n'

        contenido_xml += '\t\t\t\t\t<f_audit/>\n'
        contenido_xml += '\t\t\t\t\t<t_audit/>\n'
        contenido_xml += '\t\t\t\t</medidas_seg>\n'

        # reg_uno/declaracion/fichero/estructura/datos_esp_proteg
        #######################################################################
        # Se rellenará con un "1" si el fichero contiene este tipo de dato, o con "0" en caso contrario.
        # Si alguno de estos elementos tiene valor "1", entonces el elemento
        # Envio/reg_uno/declaracion/fichero/medidas_seg/nivel deberá tener valor "3"
        # (salvo que se encuadre en alguna de las excepciones mencionadas en el nodo correspondiente a medidas de seguridad).

        contenido_xml += '\t\t\t\t<estructura>\n'
        contenido_xml += '\t\t\t\t\t<datos_esp_proteg>\n'
        ind_ide = boolean2num(datos_fichero['ideologia'])
        contenido_xml += '\t\t\t\t\t\t<ind_ide>' + ind_ide + '</ind_ide>\n'
        ind_as = boolean2num(datos_fichero['afiliacion'])
        contenido_xml += '\t\t\t\t\t\t<ind_as>' + ind_as + '</ind_as>\n'
        ind_r = boolean2num(datos_fichero['religion'])
        contenido_xml += '\t\t\t\t\t\t<ind_r>' + ind_r + '</ind_r>\n'
        ind_c = boolean2num(datos_fichero['creencias'])
        contenido_xml += '\t\t\t\t\t\t<ind_c>' + ind_c + '</ind_c>\n'
        contenido_xml += '\t\t\t\t\t</datos_esp_proteg>\n'

        # reg_uno/declaracion/fichero/estructura/otros_esp_proteg
        #######################################################################
        # Se rellenará con un "1" si el fichero contiene este tipo de dato, o con "0" en caso contrario.
        # Si alguno de estos elementos tiene valor "1", entonces el elemento
        # Envio/reg_uno/declaracion/fichero/medidas_seg/nivel deberá tener valor "3"
        # (salvo que se encuadre en alguna de las excepciones mencionadas en el nodo correspondiente a medidas de seguridad).

        contenido_xml += '\t\t\t\t\t<otros_esp_proteg>\n'
        ind_re = boolean2num(datos_fichero['raza'])
        contenido_xml += '\t\t\t\t\t\t<ind_re>' + ind_re + '</ind_re>\n'
        ind_sal = boolean2num(datos_fichero['salud'])
        contenido_xml += '\t\t\t\t\t\t<ind_sal>' + ind_sal + '</ind_sal>\n'
        ind_sexo = boolean2num(datos_fichero['sexo'])
        contenido_xml += '\t\t\t\t\t\t<ind_sexo>' + ind_sexo + '</ind_sexo>\n'
        contenido_xml += '\t\t\t\t\t</otros_esp_proteg>\n'

        # reg_uno/declaracion/fichero/estructura/infracciones_penal
        #######################################################################
        # Sólo se rellenará para las declaraciones de ficheros de titularidad
        # pública (en ficheros de titularidad privada estos elementos vendrán
        # vacíos).

        contenido_xml += '\t\t\t\t\t<infracciones_penal>\n'
        contenido_xml += '\t\t\t\t\t\t<ind_ipen/>\n'
        contenido_xml += '\t\t\t\t\t\t<ind_iad/>\n'
        contenido_xml += '\t\t\t\t\t</infracciones_penal>\n'

        # reg_uno/declaracion/fichero/estructura/identificativos
        #######################################################################
        # En notificaciones de alta este apartado es obligatorio, por lo que al menos uno de los elementos de este nodo deberá tener valor "1". Asimismo, en notificaciones de modificación, si se ha señalado con valor "1" el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/estruct_sistema, entonces al menos uno de los elementos de este nodo deberá tener valor "1" (en este caso, además, deberá también cumplimentarse el nodo
        # Envio/reg_uno/declaracion/fichero/estructura/sist_tratamiento).

        # En notificaciones de supresión los elementos de este nodo vendrán
        # vacíos.

        contenido_xml += '\t\t\t\t\t<identificativos>\n'
        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_est))):
            contenido_xml += '\t\t\t\t\t\t<ind_nif/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_ss/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_n_a/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_ts/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_dir/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_tel/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_huella/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_img/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_marcas/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_firma/>\n'
            contenido_xml += '\t\t\t\t\t\t<ind_registro/>\n'
            contenido_xml += '\t\t\t\t\t\t<ODCI/>\n'
        else:
            lista_dci = datos_fichero['dci'].split(';')
            claves_dci = (
                '01', '02', '03', '04', '05', '06', '07', '08', '09', '10')
            dic_dci = {}
            for clave in claves_dci:
                if clave in lista_dci:
                    dic_dci['dci' + clave] = '1'
                else:
                    dic_dci['dci' + clave] = '0'
            ind_nif = dic_dci['dci01']
            contenido_xml += '\t\t\t\t\t\t<ind_nif>' + ind_nif + '</ind_nif>\n'
            ind_ss = dic_dci['dci02']
            contenido_xml += '\t\t\t\t\t\t<ind_ss>' + ind_ss + '</ind_ss>\n'
            ind_n_a = dic_dci['dci03']
            contenido_xml += '\t\t\t\t\t\t<ind_n_a>' + ind_n_a + '</ind_n_a>\n'
            ind_ts = dic_dci['dci04']
            contenido_xml += '\t\t\t\t\t\t<ind_ts>' + ind_ts + '</ind_ts>\n'
            ind_dir = dic_dci['dci05']
            contenido_xml += '\t\t\t\t\t\t<ind_dir>' + ind_dir + '</ind_dir>\n'
            ind_tel = dic_dci['dci06']
            contenido_xml += '\t\t\t\t\t\t<ind_tel>' + ind_tel + '</ind_tel>\n'
            ind_huella = dic_dci['dci07']
            contenido_xml += '\t\t\t\t\t\t<ind_huella>' + \
                ind_huella + '</ind_huella>\n'
            ind_img = dic_dci['dci08']
            contenido_xml += '\t\t\t\t\t\t<ind_img>' + ind_img + '</ind_img>\n'
            ind_marcas = dic_dci['dci09']
            contenido_xml += '\t\t\t\t\t\t<ind_marcas>' + \
                ind_marcas + '</ind_marcas>\n'
            ind_firma = dic_dci['dci10']
            contenido_xml += '\t\t\t\t\t\t<ind_firma>' + \
                ind_firma + '</ind_firma>\n'
            # ind_registro 0 en ficheros de titularidad privada
            contenido_xml += '\t\t\t\t\t\t<ind_registro>0</ind_registro>\n'
            odci = datos_fichero['otrosdatos']
            if odci:
                odci = capitalizar(odci)
                contenido_xml += '\t\t\t\t\t\t<ODCI>' + odci + '</ODCI>\n'
            else:
                contenido_xml += '\t\t\t\t\t\t<ODCI/>\n'

        contenido_xml += '\t\t\t\t\t</identificativos>\n'

        # reg_uno/declaracion/fichero/estructura/otros
        #######################################################################

        contenido_xml += '\t\t\t\t\t<otros>\n'
        otros_tipos = datos_fichero['otros_tipos_datos']
        if (otros_tipos and (tipo_solicitud == 1 or (tipo_solicitud == 2 and (mod_est)))):
            contenido_xml += '\t\t\t\t\t\t<otros_tipos>' + \
                otros_tipos + '</otros_tipos>\n'
        else:
            contenido_xml += '\t\t\t\t\t\t<otros_tipos/>\n'
        desc_otros_tipos = datos_fichero['otrostipos']
        if desc_otros_tipos:
            desc_otros_tipos = capitalizar(desc_otros_tipos)
            contenido_xml += '\t\t\t\t\t\t<desc_otros_tipos>' + \
                desc_otros_tipos + '<desc_otros_tipos>\n'
        else:
            contenido_xml += '\t\t\t\t\t\t<desc_otros_tipos/>\n'
        contenido_xml += '\t\t\t\t\t</otros>\n'

        # reg_uno/declaracion/fichero/estructura/sist_tratamiento
        #######################################################################
        # Se refiere a la forma en que se organiza y se trata la información
        # del fichero.

        # En notificaciones de alta este nodo es obligatorio.

        # En notificaciones de modificación deberá cumplimentarse si se ha señalado con valor "1" el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/estruct_sistema
        # (en este caso, además, deberá también cumplimentarse el nodo Envio/reg_uno/declaracion/fichero/estructura/identificativos).

        # En notificaciones de supresión, el elemento de este nodo vendrá
        # vacío.

        contenido_xml += '\t\t\t\t\t<sist_tratamiento>\n'
        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_est))):
            contenido_xml += '\t\t\t\t\t\t<sis_trata/>\n'
        else:
            sis_trata = "3"  # TODO 1 Automatizado 2 Manual 3 Mixto
            contenido_xml += '\t\t\t\t\t\t<sis_trata>' + \
                sis_trata + '</sis_trata>\n'

        contenido_xml += '\t\t\t\t\t</sist_tratamiento>\n'
        contenido_xml += '\t\t\t\t</estructura>\n'

        # reg_uno/declaracion/fichero/estructura/sist_tratamiento
        #######################################################################
        # En notificaciones de alta este apartado no es obligatorio, por lo que
        # estos elementos únicamente han de cumplimentarse en caso de que se
        # prevea realizar cesiones o comunicaciones de datos. No se considerará
        # cesión de datos la prestación de un servicio al responsable del
        # fichero por parte del encargado del tratamiento. La comunicación de
        # los datos ha de ampararse en alguno de los supuestos legales
        # establecidos en la LOPD.

        # En notificaciones de modificación, deberá cumplimentarse este nodo si se ha señalado con valor "1" el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/comunic_ces

        no_cesion = datos_fichero['no_cesion']
        cesiones = datos_fichero['cesiones']
        desc_otros = datos_fichero['otras_cesiones']
        contenido_xml += '\t\t\t\t<cesion>\n'
        if no_cesion:
            contenido_xml += '\t\t\t\t\t<cesiones/>\n'
            contenido_xml += '\t\t\t\t\t<desc_otros/>\n'
        else:
            if cesiones:
                contenido_xml += '\t\t\t\t\t<cesiones>' + \
                    cesiones + '</cesiones>\n'
            else:
                contenido_xml += '\t\t\t\t\t<cesiones/>\n'
            if desc_otros:
                desc_otros = capitalizar(desc_otros)
                contenido_xml += '\t\t\t\t\t<desc_otros>' + \
                    desc_otros + '</desc_otros>\n'
            else:
                contenido_xml += '\t\t\t\t\t<desc_otros/>\n'

        contenido_xml += '\t\t\t\t</cesion>\n'

        # reg_uno/declaracion/fichero/estructura/transfer_inter
        #######################################################################
        # En notificaciones de alta este nodo únicamente debe cumplimentarse en el caso de que se realice o esté previsto realizar un tratamiento de datos fuera del territorio del Espacio Económico Europeo.
        # No obstante, si se ha cumplimentado el nodo Envio/reg_uno/declaracion/fichero/encargado,
        # y el código del elemento pais corresponde a un país fuera de la Unión
        # Europea, entonces deberá cumplimentarse este nodo, figurando -al
        # menos- el país del encargado y la categoría de correspondiente a
        # éste.

        # En notificaciones de modificación, este nodo se cumplimentará si se ha señalado con valor "1"
        # el elemento
        # Envio/reg_uno/declaracion/fichero/control/acciones_mod/trans_inter.

        # En notificaciones de supresión, los elementos de este nodo vendrán
        # vacíos.

        contenido_xml += '\t\t\t\t<transfer_inter>\n'
        no_transfer = datos_fichero['no_transfer']
        if (tipo_solicitud == 3 or (tipo_solicitud == 2 and not(mod_tra)) or no_transfer):
            contenido_xml += '\t\t\t\t\t<pais/>\n'
            contenido_xml += '\t\t\t\t\t<categoria/>\n'
            contenido_xml += '\t\t\t\t\t<otros/>\n'
        else:
            paises = []
            categorias = []
            for num in range(1, 6):
                if datos_fichero['pais' + str(num)]:
                    pais_destino = datos_fichero['pais' + str(num)]['code']
                    if not pais_destino:
                        mensaje_consola(
                            2, "Fallo al intentar obtener datos del pais de la transferencia")
                        raise osv.except_osv(
                            '¡Error al cargar datos de paises!', 'No se ha podido procesar de la transferencia internacional.')
                    cod_pais = pais_destino
                    paises.append(cod_pais)
            pais = ';'.join(paises)

            if pais != '':
                for num in range(1, 5):
                    if datos_fichero['categoria' + str(num)]:
                        categoria_destino = datos_fichero[
                            'categoria' + str(num)]['id']
                        if not categoria_destino:
                            mensaje_consola(
                                2, "No se han podido cargar los datos de la categoría")
                            raise osv.except_osv(
                                '¡Error al cargar la categoría!', 'Se ha producido un error tratando de obtener la categoría para la transferencia internacional.')
                        cod_cat = categoria_destino
                        if (cod_cat < 10):
                            cod_cat = "0" + str(cod_cat)
                        else:
                            cod_cat = str(cod_cat)
                        categorias.append(cod_cat)
                categoria = ';'.join(categorias)

                otros = datos_fichero['categoria5']
                contenido_xml += '\t\t\t\t\t<pais>' + pais + '</pais>\n'
                if categoria:
                    contenido_xml += '\t\t\t\t\t<categoria>' + \
                        categoria + '</categoria>\n'
                else:
                    contenido_xml += '\t\t\t\t\t<categoria/>\n'
                if otros:
                    contenido_xml += '\t\t\t\t\t<otros>' + otros + '</otros>\n'
                else:
                    contenido_xml += '\t\t\t\t\t<otros/>\n'
            else:
                contenido_xml += '\t\t\t\t\t<pais/>\n'
                contenido_xml += '\t\t\t\t\t<categoria/>\n'
                contenido_xml += '\t\t\t\t\t<otros/>\n'

        contenido_xml += '\t\t\t\t</transfer_inter>\n'
        contenido_xml += '\t\t\t</fichero>\n'
        contenido_xml += '\t\t</declaracion>\n'

        # reg_uno/final
        #######################################################################
        contenido_xml += '\t\t<final>\n'
        contenido_xml += '\t\t\t<contador/>\n'
        contenido_xml += '\t\t\t<tot_altas/>\n'
        contenido_xml += '\t\t\t<tot_modif/>\n'
        contenido_xml += '\t\t\t<tot_bajas/>\n'
        contenido_xml += '\t\t</final>\n'

        contenido_xml += '\t</reg_uno>\n'
        contenido_xml += '</Envio>'

        # Lineas para pruebas
        #filename = "/tmp/lopdtest_"+ str(ids[0]) +".xml"
        #file = open(filename, 'w')
        # file.write(contenido_xml)
        # file.close()
        #mensaje_consola(1,filename+" Generado correctamente")
        #mensaje_consola(1,'Tests Ok.')
        #raise osv.except_osv('Finalizado','Fin de ejecución de pruebas!')

        try:
            # Se codifica en base64 para realizar el envío
            envio = base64.standard_b64encode(contenido_xml)
        except:
            mensaje_consola(3, "Error en la codificación de los datos")
            raise osv.except_osv(
                '¡Error en la codificación!', 'Se ha producido un error intentado codificar los datos que van a ser enviados, es posible que haya introducido algún carácter no válido en la solicitud, por favor revise los campos.')

        try:
            url = 'https://www.aespd.es:443/agenciapd/axis/SolicitudService?wsdl'
            client = Client(url)
            # TODO: TODO: TODO: probarXml para realizar pruebas. registrarXml
            # para registrar los ficheros oficialmente
            resultado = client.service.probarXml(envio)
            #resultado = client.service.registrarXml(envio)
            mensaje_consola(1, "Envío Ok")
        except:
            mensaje_consola(3, "Error en el envío de datos a la Agencia")
            raise osv.except_osv(
                '¡Error de envío!', 'Se ha producido un error tratando de enviar la solicitud a la agencia, puede que su equipo no esté conectado a la red o que haya un fallo en el sistema de la Agencia de protección de datos, pruebe a enviar la solicitud más tarde.')

        # Se decodifican los datos que han sido devueltos por el servidor de la
        # agencia
        xml_agencia = base64.standard_b64decode(resultado)
        # Lineas para pruebas
        # file=open('/tmp/xml_recibido.xml','w')
        # file.write(xml_agencia)
        # file.close()

        dom = minidom.parseString(xml_agencia)

        def getText(listanodos):
            texto = ""
            for nodo in listanodos:
                if nodo.nodeType == nodo.TEXT_NODE:
                    texto += nodo.data
            return texto

        datos = {}
        # 00 Solicitud Correcta.
        try:
            datos['est_err'] = getText(
                dom.getElementsByTagName("est_err")[0].childNodes)
        except Exception, e:
            mensaje_consola(3, "No se puede procesar el archivo recibido")
            raise osv.except_osv(
                '¡Error en la recepción!', 'Se ha procesado su petición en el servidor de la agencia de protección de datos, pero no se han podido interpretar los datos devueltos por la agencia.\n\nSe esperaba un formato diferente, si el problema persiste contacte con su administrador.')

        if datos['est_err'] == '00':
            mensaje_consola(1, "Recepción Ok")
        elif datos['est_err'] == '01':
            mensaje_consola(2, "Err.01 - Envío duplicado")
            raise osv.except_osv(
                'Envío duplicado', 'La notificación enviada ya consta como recibida en la Agencia Española de Protección de Datos.')
        elif datos['est_err'] == '02':
            mensaje_consola(2, 'Err.02 - Error en formato XML')
            raise osv.except_osv(
                'Error en formato XML', 'El formato de la notificación enviada no cumple con la definición publicada por la Agencia Española de Protección de Datos del formato XML de notificación de ficheros al Registro General de Protección de Datos.')
        elif datos['est_err'] == '03':
            mensaje_consola(2, 'Err.03 - Error en formato Pdf')
            raise osv.except_osv(
                'Error en formato Pdf', 'El formato de la notificación enviada no cumple con la estructura esperada por la Agencia Española de Protección de Datos. Puede descargarse el formulario electrónico para la notificación de ficheros a la AEPD desde www.agpd.es.')
        elif datos['est_err'] == '04':
            mensaje_consola(
                2, 'Err.04 - El certificado no corresponde al declarante')
            raise osv.except_osv('El certificado no corresponde al declarante',
                                 'El certificado digital con el que se ha firmado la notificación no se corresponde con los datos del declarante señalados en la hoja de solicitud.')
        elif datos['est_err'] == '05':
            mensaje_consola(2, 'Err.05 - Certificado revocado')
            raise osv.except_osv(
                'Certificado revocado', 'El certificado digital con el que se ha firmado la notificación está revocado y no es admitido por la Agencia Española de Protección de Datos. Vuelva a realizar el envío de la notificación con un certificado digital válido.')
        elif datos['est_err'] == '06':
            mensaje_consola(2, 'Err.06 - Certificado no válido por CA')
            raise osv.except_osv('Certificado no válido por CA',
                                 'El certificado digital con el que se ha firmado la notificación no es reconocido por la Agencia Española de Protección de Datos. Vuelva a realizar el envío de la notificación con un certificado digital válido. Puede consultar las Autoridades de Certificación reconocidas por la Agencia en www.agpd.es.')
        elif datos['est_err'] == '07':
            mensaje_consola(2, 'Err.07 - Firma incorrecta')
            raise osv.except_osv(
                'Firma incorrecta', 'Se han detectado inconsistencias en la validación de la firma. El documento firmado o el certificado digital pueden haber sido alterados con posterioridad a la firma.')
        elif datos['est_err'] == '08':
            mensaje_consola(
                2, 'Err.08 - Faltan datos obligatorios en la solicitud')
            raise osv.except_osv('Faltan datos obligatorios en la solicitud',
                                 'La notificación enviada no contiene todos los datos obligatorios necesarios para realizar la inscripción en el Registro General de Protección de Datos. Revise el contenido de la notificación y vuelva a realizar el envío.')
        elif datos['est_err'] == '09':
            mensaje_consola(
                2, 'Err.09 - No hay manifestación del conocimiento de los deberes del declarante')
            raise osv.except_osv('No hay manifestación del conocimiento de los deberes del declarante',
                                 'En la solicitud no se ha manifestado que el declarante disponga de representación suficiente para solicitar la inscripción en nombre del responsable del fichero, que este esté informado del resto de obligaciones que se derivan de la LOPD, que todos los datos consignados son ciertos y que el responsable del fichero ha sido informado de los supuestos legales que habilitan el tratamiento de datos especialmente protegidos, la cesión y la transferencia internacional de datos.')
        elif datos['est_err'] == '10':
            mensaje_consola(
                2, 'Err.10 - Error interno del sistema, la solicitud no puede ser procesada')
            raise osv.except_osv(
                'Error', 'Error interno del sistema, la solicitud no puede ser procesada.')
        elif datos['est_err'] == '11':
            mensaje_consola(2, 'Err.11 - Credenciales incorrectas')
            raise osv.except_osv('Error', 'Credenciales incorrectas.')
        elif datos['est_err'] == '12':
            mensaje_consola(
                2, 'Err.12 - Error interno del sistema, no se ha podido firmar el acuse de recibo')
            raise osv.except_osv(
                'Error', 'Error interno del sistema, no se ha podido firmar el acuse de recibo.')
        elif datos['est_err'] == '13':
            mensaje_consola(2, 'Err.13 - Notificación sin firmar')
            raise osv.except_osv(
                'Notificación sin firmar', 'Ha seleccionado la presentación de la notificación a través de Internet firmada con certificado de firma electrónica reconocido y, sin embargo, la notificación enviada no figura correctamente firmada.')

        import tools

        datos['forma_c'] = getText(
            dom.getElementsByTagName("forma_c")[0].childNodes)
        datos['id_upload'] = getText(
            dom.getElementsByTagName("id_upload")[0].childNodes)
        datos['num_reg'] = getText(
            dom.getElementsByTagName("num_reg")[0].childNodes)
        datos['razon_s'] = getText(
            dom.getElementsByTagName("razon_s")[0].childNodes)
        datos['cif_nif'] = getText(
            dom.getElementsByTagName("cif_nif")[0].childNodes)
        datos['nombre'] = tools.ustr(
            getText(dom.getElementsByTagName("nombre")[0].childNodes))
        datos['apellido1'] = tools.ustr(
            getText(dom.getElementsByTagName("apellido1")[0].childNodes))
        datos['apellido2'] = tools.ustr(
            getText(dom.getElementsByTagName("apellido2")[0].childNodes))
        datos['nif'] = getText(dom.getElementsByTagName("nif")[0].childNodes)
        datos['cargo'] = getText(
            dom.getElementsByTagName("cargo")[0].childNodes)
        datos['denomina_p'] = tools.ustr(
            getText(dom.getElementsByTagName("denomina_p")[0].childNodes))
        datos['dir_postal'] = tools.ustr(
            getText(dom.getElementsByTagName("dir_postal")[0].childNodes))
        # datos['pais'] =
        # getText(dom.getElementsByTagName("pais")[0].childNodes) #Devuelve el
        # código del pais ej: ES
        datos['pais'] = capitalizar(pais_declarante['name'])
        # TODO : Sólo traduce España, el resto los pondrá en inglés
        if datos['pais'] == 'ES' or datos['pais'] == 'SPAIN':
            datos['pais'] = u'ESPAÑA'  # TODO : Ñ ?
        # datos['provincia'] =
        # getText(dom.getElementsByTagName("provincia")[0].childNodes)
        # #Devuelve el código de la provincia ej:29
        datos['provincia'] = capitalizar(provincia_declarante['name'])
        datos['localidad'] = tools.ustr(
            getText(dom.getElementsByTagName("localidad")[0].childNodes))
        datos['postal'] = getText(
            dom.getElementsByTagName("postal")[0].childNodes)
        datos['telefono'] = getText(
            dom.getElementsByTagName("telefono")[0].childNodes)
        datos['fax'] = getText(dom.getElementsByTagName("fax")[0].childNodes)
        datos['email'] = getText(
            dom.getElementsByTagName("email")[0].childNodes)
        datos['forma'] = getText(
            dom.getElementsByTagName("forma")[0].childNodes)
        datos['Id_notific'] = getText(
            dom.getElementsByTagName("Id_notific")[0].childNodes)
        datos['ind_deberes'] = getText(
            dom.getElementsByTagName("ind_deberes")[0].childNodes)

        fdf = crear_fdf(datos)
        #fdf = fdf.encode('utf-8')
        #fdf = fdf.replace('ESPANA',u'ESPA\xd1A')
        #fdf = fdf.replace('MUNIZ',u'MU\xd1IZ')

        # Se obtiene la ruta del pdf de la solicitud
        try:
            archivo_pdf = os.path.dirname(
                os.path.realpath(__file__)) + "/pdf/solicitud_pr.pdf"
        except:
            mensaje_consola(
                3, "No se ha podido encontrar el pdf de la solicitud")
            raise osv.except_osv('Error al procesar la solicitud',
                                 'Se ha producido un error itentando obetener el modelo de solicitud pdf, si el problema persiste contacte con su administrador.')

        # Se crea el archivo fdf
        archivo_fdf = "/tmp/tmpf" + \
            datos['id_upload'][9:] + "_" + str(ids[0]) + "fdf"
        # archivo_fdf = "/tmp/base64.standard_b64encode(datos['id_upload'][9:])
        file = open(archivo_fdf, 'w')
        #import codecs
        #file = codecs.open(archivo_fdf,"w","utf-8-sig")
        file.write(fdf)
        file.close()

        #raise osv.except_osv('Interrupción','Ejecución interrumpida')

        # pdftk pdf_origen fill_form archivo_datos output
        # resultado([id_fichero]+id_upload.pdf) flatten
        pdf_datos = "/tmp/tmpd" + \
            datos['id_upload'][9:] + "_" + str(ids[0]) + ".pdf"
        #pdf_datos = "/tmp/"+base64.standard_b64encode(datos['id_upload'][9:])
        comando = 'pdftk ' + archivo_pdf + ' fill_form ' + \
            archivo_fdf + ' output ' + pdf_datos + ' flatten'

        try:
            os.system(comando)
        except:
            mensaje_consola(3, "Error al crear pdf intermedio")
            os.remove(archivo_fdf)
            raise osv.except_osv('Error al procesar la solicitud',
                                 'Se ha producido un error itentando cumplimentar el modelo de solicitud pdf, si el problema persiste contacte con su administrador.')

        # Se borra el archivo temporal fdf
        os.remove(archivo_fdf)

        # Se crea el código de barras
        bar = Code128()
        # bar.crear_imagen(datos['id_upload'],int(0.354*inch),"png")
        try:
            pdf_imagen = bar.crear_imagen(
                datos['id_upload'], int(0.354 * inch), "png")
        except:
            mensaje_consola(3, "Error al intentar generar el código de barras")
            raise osv.except_osv(
                'Error de código de barras', 'Se ha producido un error al intentar generar el código de barras que debe ser adjuntado en la solicitud, si el problema persiste contacte con su administrador.')

        mensaje_consola(1, "Código de barras Ok")
        solicitud_final = '/tmp/tmps' + \
            datos['id_upload'][9:] + '_' + str(ids[0]) + '.pdf'
        # solicitud_final='/tmp/'+base64.standard_b64encode(datos['id_upload'][9:])
        # pdftk pdf_superpuesto.pdf background pdf_fondo.pdf output
        # resultado.pdf
        comando = 'pdftk ' + pdf_datos + ' background ' + \
            pdf_imagen + ' output ' + solicitud_final
        try:
            os.system(comando)
        except:
            mensaje_consola(3, "Error al crear la solicitud final")
            os.remove(pdf_datos)
            os.remove(pdf_imagen)
            raise osv.except_osv('Error al procesar la solicitud',
                                 'Se ha producido un error itentando crear el documento final de solicitud, si el problema persiste contacte con su administrador.')

        mensaje_consola(1, "Solicitud PDF Ok")
        os.remove(pdf_imagen)  # Elimina el pdf con el código de barras
        os.remove(pdf_datos)  # Elimina el pdf inicial sin código de barras

        # TODO: Mostrar pdf para imprimir
        f = open(solicitud_final, 'rb')

        archivo = base64.encodestring(f.read())
        solicitud = {'name': datos['id_upload'], 'archivo_pdf': archivo, 'id_fichero': ids[
            0], 'fecha': ahora, 'usuario': uid, 'tipo': str(tipo_solicitud)}

        adjunto = {'create_uid': uid, 'create_date': ahora, 'description': str(tipo_solicitud), 'res_model': 'lopd.fichero', 'company_id': 1, 'res_name': datos_fichero['name'], 'datas_fname': datos[
            'id_upload'], 'type': 'binary', 'res_id': datos_fichero['id'], 'db_datas': archivo, 'name': datos['id_upload'], 'file_type': 'pdf', 'file_size': 0, 'user_id': uid, 'parent_id': 'Directorio', 'index_content': datos['id_upload']}

        if tipo_solicitud == 1:
            self.pool.get('lopd.solicitud').create(
                cr, uid, solicitud, context={})
            # TODO: Para pruebas est_null, versión final est_pen
            #self.write( cr, uid, ids, {'estado':'est_null', 'pdf_solicitud':archivo})
            self.write(cr, uid, ids, {'estado': 'est_pen'})

        # *elif sólo en caso de confirmarse la legalización (control manual al introducir el número de registro [sin firma])
        elif tipo_solicitud == 2:
            self.pool.get('lopd.solicitud').create(
                cr, uid, solicitud, context={})
            self.write(cr, uid, ids, {'estado': 'est_pmo', 'mod_res': False, 'mod_serv': False, 'mod_iden': False,
                                      'mod_enc': False, 'mod_est': False, 'mod_med': False, 'mod_org': False, 'mod_tra': False, 'mod_com': False})
        # En caso de supresión, se marca el fichero como baja, el fichero sólo
        # se puede borrar, cuando está legalizado, dándolo de baja previamente,
        # o bien borrandolo antes de haber sido enviado.
        elif tipo_solicitud == 3:
            self.pool.get('lopd.solicitud').create(
                cr, uid, solicitud, context={})
            self.write(cr, uid, ids, {'estado': 'est_baja'})

        f.close()  # cierra el archivo que queda abierto (solicitud_final)
        # Elimina el pdf final con código de barras tras haber sido adjuntado
        os.remove(solicitud_final)

        return True

fichero_nota()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
