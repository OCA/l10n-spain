Adaptación de los clientes, proveedores y bancos para España
============================================================

Funcionalidad:
--------------

* Añade el campo *Nombre comercial* a las empresas y permite buscar por él.
* Permite definir un patrón del nombre a mostrar a partir del nombre y el
  nombre comercial de la empresa.
* Añade un *Cliente de contado* para las facturas simplificadas.
* Convierte el NIF a mayúsculas.
* Añade los campos nombre largo, NIF y web a los bancos.
* Añade los datos de los bancos españoles extraídos del registro oficial del
  Banco de España (http://goo.gl/mtx6ic). El asistente realiza la descarga
  automática de Internet, pero si por cualquier razón hay algún problema,
  existe una copia local cuya última actualización fue el 16/02/2015.
* Permite validar las cuentas bancarias españolas. Para ello, se añade un
  campo de país a las cuentas bancarias de las empresas y se realizan
  validaciones cuando el país es España.


Funcionamiento de la validación de la cuenta bancaria para cuentas españolas:
-----------------------------------------------------------------------------

* Se comprueba si la cuenta consta de 20 dígitos (con o sin espacios).
* Si no los tiene, se devuelve un error de longitud incorrecta.
* Si los dígitos son 20, se calculan los dos dígitos de control (DC) y se
  comprueba que coinciden con los introducidos.
* Si el DC no coincide, se devuelve un error de que la cuenta es incorrecta.
* Si el DC es correcto, presenta el resultado con el formato
  "1234 5678 06 1234567890"


Funcionamiento de la validación de la cuenta bancaria para cuentas IBAN:
------------------------------------------------------------------------

* Se limpia la cuenta de espacios.
* Se divide lo introducido en bloques de 4 caracteres.
* Se comprueba los dos números de control (NC) después del ES.
* Si el NC es incorrecto, se devuelve un error.
* Se comprueba también el DC.

Configuración
=============

Para añadir cuentas bancarias a la compañía, el mejor camino es ir a
Contabilidad > Configuración > Contabilidad > Cuentas bancarias.

Para añadir cuentas bancarias a los clientes/proveedores, hay que ir a la
lista de empresas desde cualquiera de los accesos, y pulsar sobre el enlace
"n Cuenta(s) bancaria(s)" que hay en la pestaña "Ventas y compras".

Para definir el patron del nombre a mostrar en empresas, hay que ir a
Configuración > Técnico > Parámetros > Parámetros del sistema
Seleccionar la clave l10n_es_partner.name_pattern
Definir el patron utilizando las etiquetas *%(name)s* para nombre y
*%(comercial_name)s* para nombre comercial.

Créditos
========

Contribuidores
--------------

* Jordi Esteve <jesteve@zikzakmedia.com>
* Ignacio Ibeas <ignacio@acysos.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Sergio Teruel <sergio@incaser.es>
* Ismael Calvo <ismael.calvo@factorlibre.com>
* Carlos Dauden <carlos.dauden@tecnativa.com>

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
