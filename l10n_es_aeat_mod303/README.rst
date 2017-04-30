.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============
AEAT Modelo 303
===============

Módulo para la presentación del modelo 303 (IVA - Autodeclaración) de la
Agencia Española de Administración Tributaria.

Instrucciones del modelo: http://goo.gl/pgVbXH

Diseño de registros BOE en Excel: https://goo.gl/HKOGec

Incluye la exportación al formato BOE para su uso telemático.

Uso
===

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/9.0

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
* Posibilidad de marcar en el resultado el ingreso/devolución en la cuenta
  corriente tributaria.
* El régimen de criterio de caja no está tampoco contemplado.
* No se puede definir por el momento la prorrata del IVA.
* Falta generar el asiento de regularización del IVA al confirmar la
  declaración (y eliminarlo si se cancela).

Créditos
========

Contribuidores
--------------

* GuadalTech (http://www.guadaltech.es)
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* AvanzOSC (http://www.avanzosc.es)
* Comunitea (http://www.comunitea.com)
* Antonio Espinosa <antonio.espinosa@tecnativa.com>

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
