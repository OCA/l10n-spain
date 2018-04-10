.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

================================================================
Punto de venta Punto de venta adaptado a la legislación española
================================================================

* Adapta el terminal punto de venta a la legislación Española (no se permite la
  emisión de tiquets, todo deben ser facturas o facturas simplificadas con
  numeración)
* Adapta el ticket de venta a la factura simplificada, añadiendo una secuencia
  correlativa y el NIF del emisor.
* Incluye los datos del cliente (nombre, NIF y dirección) si hay uno asignado.
* Chequea que no se realice una factura simplificada con valor
  superior a 3.000 euros (la cantidad es configurable por TPV).

Instalación
===========

Antes de instalar el módulo, podemos definir el relleno y el prefijo automático
en *Configuración > Parámetros del sistema*:

- `l10n_es_pos.simplified_invoice_sequence.padding` (o 4 cifras por defecto)
- `l10n_es_pos.simplified_invoice_sequence.prefix` (nombre del TPV más este
  valor)

Al instalarse el módulo, se define una secuencia para factura simplificada por
cada TPV existente.

Configuración
=============

Para activar la factura simplificada en un TPV, iremos a
*Punto de Venta > Configuración > Punto de Venta* y escogeremos uno de la
lista. En la sección *Facturación y recibos* activaremos la opción
*Secuencia de Factura Simplificada*. Podemos configurar el límite a partir del
cual no se considera factura simplificada, que por defecto es 3.000,00 €.

Si entramos en la configuración del TPV en modo debug, podremos también
configurar la sequencia asociada al TPV.

`Ver enlace de la AEAT <https://www.agenciatributaria.es/AEAT.internet/Inicio/_Segmentos_/Empresas_y_profesionales/Empresas/IVA/Obligaciones_de_facturacion/Tipos_de_factura.shtml>`_

Problemas conocidos
===================

No se comprueba el límite en operaciones separadas para un mismo cliente, algo
que Hacienda proscribe.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/l10n-spain/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Créditos
========

Imágenes
--------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contribuidores
--------------

* `Antiun <https://www.antiun.com>`_:

  * Endika Iglesias <endikaig@antiun.com>

* `Aselcis <https://www.aselcis.com>`_:

  * David Gómez <david.gomez@aselcis.com>
  * Miguel Paraíso <miguel.paraiso@aselcis.com>

* `Acysos <https://www.acysos.com>`_:

  * Ignacio Ibeas <ignacio@acysos.com>

* `Tecnativa <https://www.tecnativa.com>`_:

  * David Vidal <david.vidal@tecnativa.com>
  * Pedro M. Baeza <pedro.baeza@tecnativa.com>
  * Antonio Espinosa <antonio.espinosa@tecnativa.com>
  * Rafael Blasco <rafael.blasco@tecnativa.com>

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
