Adaptación de los clientes, proveedores y bancos para España
============================================================

Funcionalidad:
--------------

* Añade el campo *Nombre comercial* a las empresas y permite buscar por él.
* Permite definir un patrón del nombre a mostrar a partir del nombre y el
  nombre comercial de la empresa.
* Convierte el NIF a mayúsculas.
* Añade los campos nombre largo, NIF y web a los bancos.
* Añade los datos de los bancos españoles extraídos del registro oficial del
  Banco de España (http://goo.gl/mtx6ic). El asistente realiza la descarga
  automática de Internet, pero si por cualquier razón hay algún problema,
  existe una copia local cuya última actualización fue el 26/10/2017.

Configuración
=============

Este módulo depende de base_bank_from_iban que se encuentra en el repositorio
https://github.com/OCA/community-data-files

Para añadir cuentas bancarias a la compañía, el mejor camino es ir a
Contabilidad > Configuración > Contabilidad > Cuentas bancarias.

Para añadir cuentas bancarias a los clientes/proveedores, hay que ir a la
lista de empresas desde cualquiera de los accesos, y pulsar sobre el enlace
"n Cuenta(s) bancaria(s)" que hay en la pestaña "Ventas y compras".

Para definir el patrón del nombre a mostrar en empresas, hay que ir a
Configuración > Técnico > Parámetros > Parámetros del sistema
Seleccionar la clave l10n_es_partner.name_pattern
Definir el patron utilizando las etiquetas *%(name)s* para nombre y
*%(comercial_name)s* para nombre comercial.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/11.0

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
