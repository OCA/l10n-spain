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
* Motor de cálculo de importes por códigos de impuestos.

Configuration
=============

Todos aquellos modelos que se especifiquen en los módulos adicionales y
hereden el AEAT base, deberán definir una variable interna que se llame
'_aeat_number' asignándole como valor, el número del modelo (130, 340, 347...).

Créditos
========

Contribudores
-------------

* Pexego (http://www.pexego.es)
* Acysos (http://www.acysos.com)
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* AvanzOSC (http://www.avanzosc.es)

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
