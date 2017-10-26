Extractos bancarios españoles (Norma 43)
========================================

Importación y tratamiento de los extractos bancarios españoles que siguen la
norma/cuaderno 43 de la 'Asociación Española de la Banca'. Puede consultarse la
especificación del formato aquí_.

.. _aquí: http://goo.gl/2zzlmu

Uso
===

#. Vaya a Contabilidad (Facturación) > Tablero, y escoja "Importar extracto" en
   el cuadro que corresponda con el diario de su banco.
#. Seleccione el archivo Norma 43 a importar.
#. Pulse en 'Importar'.
#. Aparecerá el asistente para conciliación inmediatamente después.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/11.0

Incidencias conocidas / Hoja de ruta
====================================

* Reconocimiento de partners para otros bancos distintos del Santander,
  CaixaBank, Bankia o Sabadell.
* La moneda se extrae del diario con el cual se va a importar o, en su defecto,
  de la compañia, no del extracto norma 43 que se importa, para lo cual sería
  necesario usar códigos numéricos según la norma ISO 4217.
* Los códigos de operación N43 no se utilizan para asociar una cuenta contable
  genérica, ya que Odoo no lo permite.

Créditos
========

Contribuidores
--------------
* Tecnativa (https://www.tecnativa.com):
  * Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Comunitea (https://www.comunitea.com)
  * Omar Castiñeira Saavedra <omar@comunitea.com>

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
