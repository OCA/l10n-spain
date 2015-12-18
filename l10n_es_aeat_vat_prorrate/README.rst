.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
AEAT - Prorrata de IVA
======================

Módulo para gestionar la prorrata del IVA en las declaraciones de la AEAT (por
el momento, en el modelo 303), según el artículo 92 de la Ley 37/1992, de 28 de
diciembre, del Impuesto sobre el Valor Añadido.

Configuración
=============

En la declaración del modelo 303 del último periodo del ejercicio (4º trimestre
o diciembre), hay que introducir la cuenta contable y opcionalmente la cuenta
analítica a la que llevar la regularización según el porcentaje de prorrata
definitivo, que es el que se introduce en ese periodo.

Uso
===

Realizando el modelo 303, se puede seleccionar si se desea aplicar prorrata de
IVA.

Prorrata general
----------------

En el caso de seleccionar "Prorrata general", aparece un nuevo campo llamado
"Porcentaje de prorrata de IVA" que puede ser rellenado a mano.

Además, cuando se realice el asiento de regularización, la parte proporcional
de la cuota no deducida se compensará como gasto.

Se ha incluido un calculador del porcentaje de prorrata, utilizable en 2 casos:

* Al comienzo de un nuevo ejercicio, para determinar el porcentaje provisional
  a aplicar hasta el último periodo de ese ejercicio.
* En la última declaración del ejercicio, para determinar el porcentaje
  definitivo de prorrata, y sobre el que se compensará la diferencia.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Problemas conocidos / Hoja de ruta
==================================

* La prorrata especial de IVA no está contemplada aún.
* Este módulo no incluye la posibilidad de las facturas de actividad
  diferenciada, de las que te puedes deducir el 100% del IVA de la factura.

Créditos
========

Contribudores
-------------

* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Ainara Galdona <agaldona@avanzosc.es>

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
