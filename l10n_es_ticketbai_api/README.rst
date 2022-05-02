==========================================
TicketBAI (API) - Haciendas Forales Vascas
==========================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--spain-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-spain/tree/14.0/l10n_es_ticketbai_api
    :alt: OCA/l10n-spain

|badge1| |badge2| |badge3|

Módulo base (API) para la declaración de todas las operaciones de venta realizadas por las personas y entidades
que desarrollan actividades económicas y tributan en alguno de los territorios históricos del País Vasco/Euskadi.

TicketBAI es un proyecto común de las Haciendas Forales Vascas
y del Gobierno Vasco.
https://www.euskadi.eus/contenidos/informacion/ticketbai/es_14815/adjuntos/TicketBAI_Especificaciones_v_1_1.pdf

**Table of contents**

.. contents::
   :local:

Installation
============

Para instalar esté módulo se necesita:

#. Los módulos base y base_setup
#. Las librerías Python xmlsig, cryptography, qrcode, xmltodict y requests_pkcs12.

Configuration
=============

Para configurar este módulo es necesario:

En la compañía:

* Habilitar TicketBAI
* Habilitar entorno de pruebas (envía las facturas a los servidores de prueba)
* Certificado P12 TicketBAI (se puede descargar uno de pruebas desde Izenpe, sello entidad es el mas adecuado).
* Configurar instalación TicketBAI con nombre de software, código de licencia etc. (es necesario dar de alta la entidad desarrolladora en Hacienda).
* Hacienda foral vasca en la que se tributa a elegir entre:

  * Araba
  * Bizkaia
  * Gipuzkoa

* Régimen simplificado (en caso de que la compañía tribute en régimen simplificado)

En la configuración general:

* Número de serie del dispositivo (opcional)

TODO
====

* Incorporar URLs servidores de producción (TBD)

  * Araba
  * Bizkaia

* Desarrollar envío a TicketBAI Araba

* Desarrollar envío a Batuz para Bizkaia

* Si la comunicación con hacienda falla una cantidad establecida de veces, dejar de intentar enviar y mostrar un botón para volver a realizar una cantidad de intentos cuando el usuario haga click.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_ticketbai_api%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Binovo IT Human Project S.L.

Contributors
~~~~~~~~~~~~

* Josean Soroa <js@landoo.es>
* Aritz Olea <ao@landoo.es>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-spain <https://github.com/OCA/l10n-spain/tree/14.0/l10n_es_ticketbai_api>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
