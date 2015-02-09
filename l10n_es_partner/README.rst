Adaptación de los clientes, proveedores y bancos para España
============================================================

Funcionalidad:
--------------

 * Añade el campo *Nombre comercial* a las empresas y permite buscar por él.
 * Convierte el NIF a mayúsculas.
 * Añade los campos nombre largo, NIF y web a los bancos.
 * Añade los datos de los bancos españoles extraídos del registro oficial del
   Banco de España (http://goo.gl/mtx6ic). Últ. actualización: 06/02/2015.
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

Credits
=======

Contributors
------------
* Jordi Esteve <jesteve@zikzakmedia.com>
* Ignacio Ibeas <ignacio@acysos.com>
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Sergio Teruel <sergio@incaser.es>
* Ismael Calvo <ismael.calvo@factorlibre.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
