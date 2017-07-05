.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================================
Suministro Inmediato de Información en el IVA
=============================================

Módulo para la presentación inmediata del IVA
http://www.agenciatributaria.es/static_files/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/Suministro_inmediato_informacion/FicherosSuministros/V_05/SII_Descripcion_ServicioWeb_v0.5_es_es.pdf

Installation
============

Para instalar esté módulo necesita:

#. Libreria Python Zeep, se puede instalar con el comando 'pip install zeep'
#. Libreria Python Requests, se puede instalar con el comando 'pip install requests'
#. Libreria pyOpenSSL, versión 0.15 o posterior

Configuration
=============

Para configurar este módulo necesitas:

#. En la compañia se almacenan las URLs del servicio SOAP de hacienda.
   Estas URLs pueden cambiar según comunidades
#. Los certificados deben alojarse en una carpeta accesible por la instalación
   de Odoo.
#. Preparar el certificado. El certificado enviado por la FMNT es en formato
   p12, este certificado no se puede usar directamente con Zeep. Se tiene que
   extraer la clave pública y la clave privada.

En Linux se pueden usar los siguientes comandos:

- Clave pública: "openssl pkcs12 -in Certificado.p12 -nokeys -out publicCert.crt -nodes"
- Clave privada: "openssl pkcs12 -in Certifcado.p12 -nocerts -out privateKey.pem -nodes"

Connector:

#. Ajustar variables de entorno:

     ODOO_CONNECTOR_CHANNELS=root:4

   u otro canal de configuración. Por defecto es root:1

   Si xmlrpc_port no esta definido: ODOO_CONNECTOR_PORT=8069

#. Otra alternativa es usuando un fichero de configuración:

     [options]
     (...)
     workers = 4
     server_wide_modules = web,web_kanban,connector

     (...)
     [options-connector]
     channels = root:4

#. Arranca Odoo con --load=web,web_kanban,connector y --workers más grande que 1.

Más información http://odoo-connector.com

Usage
=====

Cuando se valida una factura automáticamente envia la comunicación al servidor
de AEAT.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Known issues / Roadmap
======================

* Comunicación de cobros y pagos.
* Determinadas facturas intracomunitarias (Articulo 66 RIVA).
* Facturas simplificadas.
* Asistente para consultar los documentos comunicados.
* Libro de bienes de inversión (Libro anual se crea un módulo aparte).
* Regímenes especiales de seguros y de agencias de viaje.
* Comunicación de las facturas del primer semestre.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/l10n-spain/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Ignacio Ibeas <ignacio@acysos.com>
* Rubén Cerdà <ruben.cerda.roig@diagram.es>
* Ramon Guiu <ramon.guiu@minorisa.net>
* Pablo Fuentes <pablo@studio73.es>
* Jordi Tolsà <jordi@studio73.es>
* Ismael Calvo <ismael.calvo@factorlibre.es>
* Omar Castiñeira - Comunitea S.L. <omar@comunitea.com>
* Juanjo Algaz <jalgaz@gmail.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
