AEAT Base
=========
Módulo base para declaraciones de la AEAT.
* Crea campos base de los modelos aeat.
* Especifica un esqueleto base para todos los modelos.
* Crea una secuencia automática para los registros diferenciando por modelo.
* La exportación del BOE. Define una exportación básica, definiendo los diferentes registros del fichero.
  Genera el registro del declarante con los campos genericos de los modelos.

Configuration
=============

Todos aquellos modelos que se especifiquen en los módulos adicionales y hereden el AEAT base, deberán
definir una variable interna que se llame '_aeat_number' asignándole como valor, el nombre del modelo.

Credits
=======

Contributors
------------

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
