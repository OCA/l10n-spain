.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Regiones NUTS para España
=========================

Este módulo permite importar las regiones NUTS para España.

* Provincias españolas (NUTS level 4) como Provincia en el formulario de Empresa
  (res.partner.state_id)
* Comunidades autónomas españolas (NUTS level 3) como Comunidad Autónoma en el
  formulario de Empresa (res.partner.substate)
* Regiones españolas (NUTS level 2) como Regiones en el formulario de Empresa
  (res.partner.region)


Instalación
===========

Para instalar éste addon, necesitarás el módulo python 'request':

* pip intall requests


Configuración
=============

Después de instalar, debes clicar en el asistente de importación para añadir
las regiones NUTS en la base de datos de Odoo.
Ventas > Configuración > Libreta de direcciones > Importar NUTS 2013

Este asistente descargará del servicio europeo RAMON los metadatos para añadir
las regiones NUTS en Odoo. Este módulo específico de la localización española
hereda este asistente genérico para relacionar cada region NUTS española con las
provincias españolas definidas en el módulo l10n_es_toponyms


Uso
=====

Sólo el administrador puede gestionar las regiones NUTS (realmente no es necesario
porque es una convención a nivel Europeo) pero cualquier usuario puede leerlas,
para que pueda asignarlas en eel objeto Empresa (res.partner)


Créditos
========

Contribudores
-------------
* Antonio Espinosa <antonioea@antiun.com>

Mantenido por
-------------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

Este módulo lo mantiene la OCA.

OCA (Odoo Community Association) es una organización sin ánimo de lucro cuya
misión es mantener el desarrollo colaborativo de funcionalidad de Odoo
y promocionar su uso por todo el mundo.

Para contribuir a éste módulo, por favor visita http://odoo-community.org
