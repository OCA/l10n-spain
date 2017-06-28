.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

================================================================
Punto de venta Punto de venta adaptado a la legislación española
================================================================

* Adapta el terminal punto de venta a la legislación Española (no se permite la
  emisión de tiquets, todo deben ser facturas o facturas simplificadas con
  numeración)
* Adapta el ticket de venta a la factura simplificada, añadiendo una secuencia correlativa y el NIF del emisor.
* Incluye los datos del cliente (nombre, NIF y dirección) si hay uno asignado, de lo contrario, asigna un 'cliente
  de contado' por defecto.
* Chequea que no se realice una factura simplificada con valor
  superior a 3.000 euros (la cantidad es configurable por TPV).


Instalación
===========

Para instalar este modulo necesitas:

* point_of_sale (Odoo addon)
* l10n_es_partner (OCA addon, repositorio l10n-spain)

Se instalan automáticamente si están disponibles en la lista de addons.

También es necesario definir una secuencia de factura simplificada en la
configuración de cada TPV.


Configuración
=============

Se puede configurar el límite a partir del cual no se considera factura
simplificada, por defecto es 3.000,00 €. También permite modificar la secuencia de factura simplificada.
Para modificarlos es necesario ir a:
Configuracion > Terminal punto de venta (TPV)

`Ver enlace de la AEAT <http://www.agenciatributaria.es/AEAT.internet/Inicio_es_ES/_Segmentos_/Empresas_y_profesionales/Empresas/IVA/Obligaciones_de_facturacion/Tipos_de_factura.shtml>`_


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_pos%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Licencia
========

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/agpl-3.0-standalone.html>.


Créditos
========

Contribuidores
--------------

* Endika Iglesias <endikaig@antiun.com>
* Pedro M. Baeza [Serv. Tecnológicos Avanzados] <pedro.baeza@serviciosbaeza.com>
* Antonio Espinosa <antonioea@antiun.com>
* Rafael Blasco <rafabn@antiun.com>
* David Gómez <david.gomez@aselcis.com>
* Miguel Paraíso <miguel.paraiso@aselcis.com>


Mantenedor
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
