.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================================================
Exportación de fichero de confirming para Banco Sabadell
========================================================

Módulo para la exportación de ficheros bancarios según el formato Confirming,
para Banco Sabadell.


Instalación
===========

Este módulo depende de *l10n_es_payment_order*, que se encuentra también en el
mismo repositorio.

Configuración
=============

Antes de generar un fichero bancario de Confirming, hay que definir un modo de
pago que use el tipo de pago "Confirming Sabadell". Para ello, vaya a Contabilidad >
Configuración > Varios > Modos de pago, y escoja el tipo de pago a realizar
(Transferencia, cheque o Transferencia extranjero).

Seleccione el tipo de envío información al Proveedor.

El nº de contrato de deberá ser configurado al crear el modo de pago.

Si es una Transferencia extranjero se debe de establecer el Código Estadístico para Transferencia Internacional (6 carácteres) y la cuenta bancaria del Proveedor debe ser con formato IBAN.

Nota: La exportación de fichero esta establecido a un código de divisa fijo en Euros.


Uso
===

Cree una orden de cobro en Contabilidad > Pago > Órdenes de pago, y escoja
el modo de pago creado antes.

Confirme la orden de pago, y pulse en el botón "Realizar pagos". Pulse en
"Generar" en la pantalla resultante, y obtendra el archivo exportado.


Errores conocidos / Hoja de ruta
================================

Gestión de errores
==================

Los errores/fallos se gestionan en `las incidencias de GitHub <https://github.com/OCA/
l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla proveyendo
una detallada y bienvenida retroalimentación


Créditos
========

Contribuidores
--------------

* Soluntec Proyectos y Soluciones TIC S.L. (info@soluntec.es)
* Basado en módulo l10n_es_payment_order_confirmintet de Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>

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
