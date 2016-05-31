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
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Omar Castiñeira Saavedra <omar@comunitea.com>

Financiadores
-------------
La migración de este módulo forma parte de una campaña de migración de la
localización española que ha sido posible gracias a la colaboración económica
de las siguientes empresas (por orden alfabético):

* `Aizean evolution <http://www.aizean.com>`_
* `Aselcis consulting <https://www.aselcis.com>`_
* `AvanzOSC <http://avanzosc.es>`_
* `Diagram software <http://diagram.es>`_
* `Domatix <http://www.domatix.com>`_
* `Eficent <http://www.eficent.com>`_
* `FactorLibre <http://factorlibre.com>`_
* `Fairhall solutions <http://www.fairhall.es>`_
* `GAFIC SLP <http://www.gafic.com>`_
* `Incaser <http://www.incaser.es>`_
* `Ingeos <http://www.ingeos.es>`_
* `Nubistalia <http://www.nubistalia.es>`_
* `Punt sistemes <http://www.puntsistemes.es>`_
* `Praxya <http://praxya.com>`_
* `Reeng <http://www.reng.es>`_
* `Soluntec <http://www.soluntec.es>`_
* `Tecnativa <https://www.tecnativa.com>`_
* `Trey <https://www.trey.es>`_
* `Vicent Cubells <http://vcubells.net>`_

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
