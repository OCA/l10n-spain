.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================================================
Exportación de fichero de confirming para Abanca
=======================================================

Módulo para la exportación de ficheros bancarios según el formato Confirming,
para Abanca.


Instalación
===========

Este módulo depende de *l10n_es_base_confirming*, que se encuentra también en el
mismo repositorio.

Configuración
=============

Antes de generar un fichero bancario de Confirming, hay que definir un modo de
pago que use el método de pago "Confirming Abanca". Para ello, vaya a Contabilidad >
Configuración > Administración > Modos de pago, y escoja el tipo de pago a realizar
(Transferencia, Cheque o Pagos confirmados).

Si se selecciona el Tipo de pago "Transferencia" o "Cheque" se tendrá que establecer a cuenta de quien corren los Gastos de la operación (Ordenante o Beneficiario)

Si se selecciona el Tipo de pago "Pagos confirmados" se tendrá que establecer la Forma de pago (Cheque o Transferencia)

Uso
===

Cree una orden de pago en Contabilidad > Pagos > Órdenes de pago, y escoja
el modo de pago creado antes.

Confirme la orden de pago, y pulse en el botón "Confirmar pagos". Luego
Pulse en "generar archivo de pago" para obtener el archivo de confirming


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

* Comunitea Servicios Tecnológicos S.L.
* Basado en módulo l10n_es_payment_order_confirminet de Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Santi Argüeso (Comunitea) <santi@comunitea.com>
* Ramón Castro (Las Rías)

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
