# -*- encoding: utf-8 -*-
##############################################################################
#
#    Module Writen to Odoo, Open Source Management Solution
#    
#    Copyright (C) 2013 Obertix Free Solutions (<http://obertix.net>).
#                       cubells <info@obertix.net>
#       
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published 
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################



{
    "name" : "Suministro Inmediato de Información en el IVA",
    "version" : "7.0.0.0",
    "author" : "Acysos S.L., Odoo Community Association (OCA), Infobit Informatica S.L., Diagram Software S.L. ",
    "category" : "Generic Modules",
    "website": "https://odoo-community.org/",
    "license": "AGPL-3",
    "description": """.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============
Suministro Inmediato de Información en el IVA
==============

Módulo para la presentación inmediata del IVA
http://www.agenciatributaria.es/static_files/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/Suministro_inmediato_informacion/FicherosSuministros/V_05/SII_Descripcion_ServicioWeb_v0.5_es_es.pdf

Instalación
============

Para instalar esté módulo necesita:

#. Libreria Python Zeep, se puede instalar con el comando 'pip install zeep'
#. Libreria Python Requests, se puede instalar con el comando 'pip install requests'
#. Libreria pyOpenSSL, versión 0.15 o posterior, se puede instalar con el comando 'pip install pyopenssl'

Configuración
=============

Para configurar este módulo necesitas:

#. En la compañia se almacenan las URLs del servicio SOAP de hacienda.
Estas URLs pueden cambiar según comunidades
#. En la compañia se almacenan los certificados, deben alojarse en una carpeta accesible por la instalación
de Odoo. 


Uso
=====

Cuando se válida una factura automáticamente se envia la comunicación al servidor
de AEAT.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/{repo_id}/{branch}

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Known issues / Roadmap
======================

* Comunicación de cobros y pagos.
* Determinadas facturas intracomunitarias (Articulo 66 RIVA).
* Facturas simplificadas.
* Asistente para consultar los documentos comunicados.
* Libro de bienes de inversión (Libro anual se crea un módulo aparte).
* Regímenes especiales de seguros y de agencias de viaje.
* Comunicación de las facturas del primer semestre.
* Usar modulo connector

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
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Susana Vázquez <svazquez@netquest.com>


Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.""",

    "depends" : [
        'l10n_es_aeat', 'account', 'account_invoice_currency'
    ],
    "init_xml" : [],
    "demo_xml" : [],
    "external_dependencies": {
       "python": ["zeep",
                  "requests",
                  "OpenSSL",]
    },
    "update_xml" : [
        'wizard/aeat_sii_password_view.xml',
        'wizard/account_invoice_refund_views.xml',
        'views/res_company_view.xml',
        'views/account_invoice_view.xml',
        'views/aeat_sii_map_view.xml',
        'views/aeat_sii_mapping_registration_keys_view.xml',
        'views/aeat_sii_view.xml',
        'views/account_fiscal_position_view.xml',
        'views/product_view.xml'
    ],
     "data": [
        "data/ir_config_parameter.xml",
        "data/aeat_sii_map_data.xml",
        "data/aeat_sii_mapping_registration_keys_data.xml",
        "security/ir.model.access.csv",
	    "security/aeat_sii.xml"
    ],
    "installable": True
}

