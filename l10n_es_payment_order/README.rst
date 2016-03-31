.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================================================
Exportación de ficheros bancarios CSB 19, 32, 34 y 58
=====================================================

Módulo para la exportación de ficheros bancarios según las normas CSB 19
(recibos domiciliados), CBS 32 (descuento comercial), CSB 58 (anticipos de
créditos) y CSB 34 (emisión de transferencias, nóminas, cheques, pagarés y
pagos certificados) para poder ser enviados a la entidad bancaria.

**AVISO:** Se mantienen los modos de pago CSB19 y CSB 34, porque hay bancos
como Ing Direct que no aceptan SEPA.

Instalación
===========

Si está realizando la instalación de forma local (no desde Aplicaciones), este
módulo requiere el módulo *account_banking_payment_export*, disponible en:

https://github.com/OCA/bank-payment

Configuración
=============

Antes de generar un fichero bancario CSB, hay que definir un modo de pago que
use un tipo de pago CSB (19, 32, 34 o 58), y las opciones de configuración
correspondientes según el modo elegido.

Uso
===

Al crear el fichero bancario CSB:

* Se pueden agrupar o no los pagos de una misma empresa y cuenta bancaria
* El fichero creado se guarda como adjunto de la orden de pagos. Se puede
  volver a crear el fichero de remesas siempre que sea necesario (puede tener
  que renombrar el anterior fichero adjunto si tienen el mismo nombre).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Bug Tracker
===========

Gestión de errores
==================

Los errores/fallos se gestionan en `las incidencias de GitHub <https://github.com/OCA/
l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla proveyendo
una detallada y bienvenida retroalimentación
`aquí <https://github.com/OCA/
l10n-spain/issues/new?body=m%f3dulo:%20
l10_es_payment_order%0Aversi%f3n:%20
8.0%0A%0A**Pasos%20para%20reproducirlo**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

Créditos
========

Contribuidores
--------------

* Ignacio Ibeas <ignacio@acysos.com>
* Jordi Esteve <jesteve@zikzakmedia.com
* Pablo Rocandio 
* Nan·tic
* Ainara Galdona <comercial@avanzosc.es>
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Alexis de Lattre <alexis.delattre@akretion.com>

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
