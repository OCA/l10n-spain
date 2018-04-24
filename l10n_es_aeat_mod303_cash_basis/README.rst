.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================================
AEAT Modelo 303 - Extensión para criterio de caja
=================================================

Módulo que extiende el modelo 303 para las empresas que requieran criterio de
caja.

Configuración
=============

Para su correcto uso, se deben configurar manualmente los impuestos estándar
que correspondan, activando la opción de criterio de caja.

Uso
===

#. Ir a *Contabilidad > Declaraciones AEAT > Modelo 303*.
#. Crear una nueva declaración. Si se detecta algún impuesto de venta o de
   compra con criterio de caja, se marcará la correspondiente casilla en el
   modelo, aunque dichos valores se pueden cambiar a mano.
#. Pulsar en "Calcular".
#. Los importes correspondientes a los impuestos no cobrados/pagados aparecerán
   en sus correspondientes casillas 62, 63, 74 y 75.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/10.0

Gestión de errores
==================

Los errores/fallos se gestionan en `las incidencias de GitHub <https://github.com/OCA/
l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla indicando
una detallada descripción `aquí <https://github.com/OCA/l10n-spain/issues/new>`_.

Créditos
========

Contribuidores
--------------

* `Tecnativa <https://www.tecnativa.com>`_

  * Pedro M. Baeza.

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
