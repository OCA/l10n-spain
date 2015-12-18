.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================================================
Exportación de fichero de confirming para Confirminet (Bankinter)
=================================================================

Módulo para la exportación de ficheros bancarios según el formato Confirminet,
que es una adaptación libre del formato CSB 34.

Para consultar el diseño de registros, puede ir a https://goo.gl/raeWCt.

Instalación
===========

Este módulo depende de *l10n_es_payment_order*, que se encuentra también en el
mismo repositorio.

Configuración
=============

Antes de generar un fichero bancario de Confirminet, hay que definir un modo de
pago que use el tipo de pago "Confirminet". Para ello, vaya a Contabilidad >
Configuración > Varios > Modos de pago, y escoja el tipo de pago a realizar
(Transferencia o cheque).

El nº de contrato de Confirminet será el número de cuenta bancario que se
utilice en el modo de pago, por lo que hay que definir una cuenta bancaria con
ese número en Configuración > Compañías.

Uso
===

Cree una orden de cobro en Contabilidad > Pago > Órdenes de pago, y escoja
el modo de pago creado antes.

Confirme la orden de pago, y pulse en el botón "Realizar pagos". Pulse en
"Generar" en la pantalla resultante, y obtendra el archivo exportado.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Errores conocidos / Hoja de ruta
================================

* Permitir agrupar pagos en una sola línea.
* Incluir registro 06-017 con el teléfono del proveedor (no es posible porque
  no se puede inferir directamente el prefijo internacional de un número).
* Soportar códigos adicionales (para países extranjeros) ABA/BLZ/FW/SC.

Gestión de errores
==================

Los errores/fallos se gestionan en `las incidencias de GitHub <https://github.com/OCA/
l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla proveyendo
una detallada y bienvenida retroalimentación
`aquí <https://github.com/OCA/
l10n-spain/issues/new?body=m%f3dulo:%20
l10_es_payment_order_confirminet%0Aversi%f3n:%20
8.0%0A%0A**Pasos%20para%20reproducirlo**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

Créditos
========

Contribuidores
--------------

* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>

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
