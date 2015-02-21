Presentación del Modelo AEAT 347
================================

(Declaración Anual de Operaciones con Terceros)
Basado en la Orden EHA/3012/2008, de 20 de Octubre, por el que se aprueban los
diseños físicos y lógicos del 347.

De acuerdo con la normativa de la Hacienda Española, están obligados a
presentar el modelo 347:

* Todas aquellas personas físicas o jurídicas que no esten acogidas al régimen
  de módulos en el IRPF, de naturaleza pública o privada que desarrollen
  actividades empresariales o profesionales, siempre y cuando hayan realizado
  operaciones que, en su conjunto, respecto de otra persona o Entidad,
  cualquiera que sea su naturaleza o carácter, hayan superado la cifra de
  3.005,06 € durante el año natural al que se refiere la declaración. Para el
  cálculo de la cifra de 3.005,06 € se computan de forma separada las entregas
  de biene y servicios y las adquisiciones de los mismos.
* En el caso de Sociedades Irregulares, Sociedades Civiles y Comunidad de
  Bienes no acogidas el regimen de módulos en el IRPF, deben incluir las
  facturas sin incluir la cuantía del IRPF.
* En el caso de facturas de proveedor con IRPF, no deben ser presentadas en
  este modelo. Se presentan en el modelo 190. Desactivar en la ficha del
  proveedor la opción de "Incluir en el informe 347".

De acuerdo con la normativa, no están obligados a presentar el modelo 347:

* Quienes realicen en España actividades empresariales o profesionales sin
  tener en territorio español la sede de su actividad, un establecimiento
  permanente o su domicilio fiscal.
* Las personas físicas y entidades en régimen de atribución de rentas en
  el IRPF, por las actividades que tributen en dicho impuesto por el
  régimen de estimación objetiva y, simultáneamente, en el IVA por los
  régimenes especiales simplificados o de la agricultura, ganadería
  y pesca o recargo de equivalencia, salvo las operaciones que estén
  excluidas de la aplicación de los expresados regímenes.
* Los obligados tributarios que no hayan realizado operaciones que en su
  conjunto superen la cifra de 3.005,06 €.
* Los obligados tributarios que hayan realizado exclusivamente operaciones
  no declarables.
* Los obligados tributarios que deban informar sobre las operaciones
  incluidas en los libros registro de IVA (modelo 340) salvo que realicen
  operaciones que expresamente deban incluirse en el modelo 347.

(http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)

Installation
============

Para instalar este módulo, es necesario el módulo *account_invoice_currency*,
disponible en:

https://github.com/OCA/account-financial-tools

Configuration
=============

Para aquellas empresas (clientes/proveedores) que no se quieran incluir en el
cálculo del 347, hay que marcar la casilla "No incluida en el modelo 347" desde
su formulario.

Usage
=====

En Contabilidad > Informe > Informes legales > Declaraciones AEAT > Modelo 347,
se podrá acceder a crear nuevas declaraciones.

Known issues / Roadmap
======================

* Las operaciones intracomunitarias no se descartan automáticamente. Es
  necesario marcar la empresa como no incluida en el  modelo 347.

Credits
=======

Contributors
------------

* Pexego (http://www.pexego.es)
* ASR-OSS (http://www.asr-oss.com)
* NaN·tic (http://www.nan-tic.com)
* Acysos (http://www.acysos.com)
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Joaquín Gutierrez (http://gutierrezweb.es)

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
