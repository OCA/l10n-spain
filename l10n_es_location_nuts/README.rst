.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

=========================
Regiones NUTS para España
=========================

Este módulo permite relacionar las regiones NUTS para España de nivel 4 con las
provincias españolas.

Configuración
=============

Después de instalar, debes clicar en el asistente de importación para añadir
las regiones NUTS en la base de datos de Odoo.

Ventas > Configuración > Libreta de direcciones > Importar NUTS 2013

Este asistente descargará del servicio europeo RAMON (Reference And Management
Of Nomenclatures) los metadatos para añadir las regiones NUTS en Odoo. Este
módulo específico de la localización española hereda este asistente genérico
para relacionar cada region NUTS española con las provincias españolas
definidas en Odoo.

Uso
===

Sólo el administrador puede gestionar las regiones NUTS (realmente no es
necesario porque es una convención a nivel Europeo) pero cualquier usuario
puede leerlas, para que pueda asignarlas en el objeto Empresa (res.partner)

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/10.0

Créditos
========

Contribuidores
--------------

* Antonio Espinosa <antonio.espinosa@tecnativa.com>
* Rafael Blasco <rafael.blasco@tecnativa.com>
* Jairo Llopis <jairo.llopis@tecnativa.com>
* David Vidal <david.vidal@tecnativa.com>

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
