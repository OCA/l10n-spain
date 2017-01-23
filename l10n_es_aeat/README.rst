.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========
AEAT Base
=========

Módulo base para declaraciones de la AEAT, que incluye:

* Campos base para todo los modelos AEAT.
* Vista base para todos los modelos.
* Crea una secuencia automática para los registros diferenciando por modelo.
* Exportación del BOE. Define una exportación básica, con los diferentes
  registros del fichero.
* Generación del registro del declarante con los campos genéricos de los
  modelos.
* Motor de exportación paramétrica basado en una configuración que puede ser
  introducida por datos XML o por interfaz.
* Motor de cálculo de importes por impuestos.
* Generador del asiento de regularización con cargo a un proveedor "Agencia
  Estatal de Administración Tributaria" creado al efecto.

Configuración
=============

Todos aquellos modelos que se especifiquen en los módulos adicionales y
hereden el AEAT base, deberán definir una variable interna que se llame
'_aeat_number' asignándole como valor, el número del modelo (130, 340, 347...).

Para poder utilizar el motor genérico de cálculo de casillas por impuestos
(como el 303), hay que heredar del modelo "l10n.es.aeat.report.tax.mapping" en
lugar de "l10n.es.aeat.report". Para la vista, hay que añadir el campo a mano,
ya que la herencia de vistas no permite una doble herencia de AbstractModel,
pero lo que es la vista tree ya está definida.

Para activar la creación del asiento de regularización en un modelo, hay que
poner en el modelo correspondiente el campo allow_posting a True, y establecer
en la configuración de impuestos los conceptos que se regularizarán con el
flag "to_regularize". Esto sólo es posible sobre los modelos que utilicen
el cálculo de casillas por códigos de impuestos.

Uso
===

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

Problemas conocidos / Hoja de ruta
==================================

* La configuración de exportación a BOE no se filtran ni se auto-selecciona por
  fechas de validez.
* Las partes específicas de las Diputaciones Forales no están incluidas.

Créditos
========

Contribudores
-------------

* Pexego (http://www.pexego.es)
* Ignacio Ibeas, Acysos (http://www.acysos.com)
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Santi Argüeso <santi@comunitea.com>
* cubells <info@obertix.net>
* AvanzOSC (http://www.avanzosc.es)
* Ainara Galdona
* Antonio Espinosa <antonio.espinosa@tecnativa.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
