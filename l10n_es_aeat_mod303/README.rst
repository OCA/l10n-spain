Presentación del Modelo AEAT 303
================================
Módulo para la presentación del modelo 303 (IVA - Autodeclaración) de la
Agencia Española de Administración Tributaria.

Instrucciones del modelo: http://goo.gl/pgVbXH

Diseño de registros BOE en Excel: https://goo.gl/HKOGec

Incluye la exportación al formato BOE para su uso telemático.

Problemas conocidos / Hoja de ruta
==================================

* Los regimenes simplificado y agrícola, ganadero y forestal no están
  contemplados en el desarrollo actual.
* No se permite definir que una compañía realiza tributación conjunta.
* No se permite definir que una compañía está en concurso de acreedores.
* No se permite definir que una compañía es de una Administración Tributaria
  Foral.
* Posibilidad de marcar en el resultado el ingreso/devolución en la cuenta
  corriente tributaria.
* El régimen de criterio de caja está contemplado por el módulo adicional
  `l10n_es_aeat_mod303_cash_basis`.
* La prorrata del IVA está contemplada por el módulo adicional
  `l10n_es_aeat_vat_prorrate`.
* Para el último periodo, si está exonerado del 390 y el ejercicio fiscal no
  coincide con el año natural, las casillas de totales no saldrán
  correctamente.

Créditos
========

Contribuidores
--------------

* GuadalTech (http://www.guadaltech.es)
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* AvanzOSC (http://www.avanzosc.es)
* Comunitea (http://www.comunitea.com)
* Daniel Rodriguez <drl.9319@gmail.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
