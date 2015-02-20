Extractos bancarios españoles (Norma 43)
========================================

Importación y tratamiento de los extractos bancarios españoles que siguen la
norma/cuaderno 43 de la 'Asociación Española de la Banca'. Puede consultarse la
especificación del formato aquí_.

.. _aquí: http://goo.gl/2zzlmu

Instalación
===========

Para instalar este módulo, es necesario tener disponible el módulo
*account_bank_statement_import* del repositorio
https://github.com/OCA/bank-statement-import

Igualmente, para poder seleccionar un diario y que la importación pueda
llevarse a cabo sin ningún error, es necesario instalar el módulo
*account_bank_statement_import_qif* del mismo repositorio.

Configuración
=============

No es necesaria ninguna configuración especial.

Uso
===

Vaya a Contabilidad > Extractos bancarios > Importar extracto bancario,
seleccione el archivo Norma 43 a importar, el diario en el que registrarlo,
y pulse en 'Importar'.

Incidencias conocidas / Hoja de ruta
====================================

* Reconocimiento de partners para otros bancos distintos del Santander o
  CaixaBank.
* Es necesario el módulo para importar archivos QIF para poder seleccionar el
  diario en el que hacer la importación y que no dé error.

Credits
=======

Contributors
------------

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
