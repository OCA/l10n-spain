.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===============
AEAT Modelo 303
===============

Módulo para la presentación del modelo 303 (IVA - Autodeclaración) de la
Agencia Española de Administración Tributaria.

Instrucciones del modelo: http://goo.gl/pgVbXH

Diseño de registros BOE en Excel: https://goo.gl/HKOGec

Incluye la exportación al formato BOE para su uso telemático y la creación
del asiento de regularización de las cuentas de impuestos.

Uso
===

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/11.0

Gestión de errores
==================

Los errores/fallos se gestionan en `las incidencias de GitHub <https://github.com/OCA/
l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla indicando
una detallada descripción `aquí <https://github.com/OCA/l10n-spain/issues/new>`_.

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
* No se puede rellenar la casilla [109]: Devoluciones acordadas por la Agencia
  Tributaria como consecuencia de la tramitación de anteriores autoliquidaciones
  correspondientes al ejercicio y período objeto de la autoliquidación.
* El régimen de criterio de caja está contemplado por el módulo adicional
  `l10n_es_aeat_mod303_cash_basis`.
* La prorrata del IVA está contemplada por el módulo adicional
  `l10n_es_aeat_vat_prorrate`.
* Existen 2 casos de IVA no sujeto que van a la casilla 61 del modelo, que no
  están cubiertos en este módulo:

  - Con reglas de localización, pero que no corresponde a Canarias, Ceuta y
    Melilla. Por ejemplo, un abogado de España que da servicios en Francia.
  - Articulos 7,14, Otros

  Para dichos casos, se espera un módulo extra que añada los impuestos y
  posiciones fiscales.

  Más información en https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-12329

Créditos
========

Contribuidores
--------------

* GuadalTech (http://www.guadaltech.es)
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* AvanzOSC (http://www.avanzosc.es)
* Comunitea (http://www.comunitea.com)
* Antonio Espinosa <antonio.espinosa@tecnativa.com>
* Luis M. Ontalba <luis.martinez@tecnativa.com>
* Jordi Ballester <jordi.ballester@eficent.com>

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
