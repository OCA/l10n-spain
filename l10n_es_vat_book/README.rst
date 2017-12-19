.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

============
Libro de IVA
============

Módulo que calcula el libro de IVA español.
Esto módulo introduce el menú "Libro de IVA" en Contabilidad -> Informe ->
Declaraciones AEAT -> Libro de IVA.
Es posible visualizar e imprimir por separado:
* Libro Registro de Facturas Emitidas
* Libro Regirsto de Facturas Recibidas

En el modo de visualización de los informes es posible navegar a los asientos
 contables relacionados con la factura.

Instalación
===========

Para instalar este modulo necesitas:

* account
* base_vat
* l10n_es
* l10n_es_aeat

Se instalan automáticamente si están disponibles en la lista de addons.

Consideraciones adicionales:

* Es importante que en facturas que deban aparecer en los libros registros,
  no sujetos a IVA, informar el tipo de IVA 'No Sujeto' en facturas. Para
  evitar que los usuarios olviden informarlo es recomendable instalar el
  módulo 'account_invoice_tax_required', disponible en
  `account_invoice_tax_required <https://github.com/OCA/account-financial-
  tools/tree/10.0>`_.


Configuración
=============

Los códigos de impuestos incluidos en el Libro de IVA pueden verse en:
Contabilidad -> Configuración -> AEAT -> Mapeo de códigos de impuesto ->
Declaración AEAT 340


Problemas conocidos / Hoja de ruta
==================================

Funcionalidades del Libro Registro de IVA no incluídas por el momento:
* Libro Registro de Bienes de Inversión
* Libro Registro de Determinadas Operaciones Intracomunitarias


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_pos%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Créditos
========

Contribuidores
--------------

* Daniel Rodriguez <drl.9319@gmail.com>
* Jordi Ballester (EFICENT) <jordi.ballester@eficent.com>


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
