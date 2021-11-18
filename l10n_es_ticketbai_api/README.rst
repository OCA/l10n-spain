================================
TicketBAI (API) - Gobierno Vasco
================================

.. |badge1| image:: https://img.shields.io/badge/maturity-Alpha-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--spain-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-spain/tree/11.0/l10n_es_ticketbai_api
    :alt: OCA/l10n-spain

|badge1| |badge2| |badge3|

Módulo base (API) para la declaración de todas las operaciones de venta realizadas por las personas y entidades
que desarrollan actividades económicas
https://www.euskadi.eus/contenidos/informacion/ticketbai/es_14815/adjuntos/TicketBAI_Especificaciones_v_1_1.pdf

**Table of contents**

.. contents::
   :local:

Installation
============

Para instalar esté módulo se necesita:

#. Los módulos base y base_setup
#. Las librerías Python OpenSSL, xmlsig, cryptography, qrcode, xmltodict y requests_pkcs12.

Configuration
=============

Para configurar este módulo es necesario:

En la compañía:

* Habilitar TicketBAI (modo desarrollador)
* Habilitar entorno de pruebas (envía las facturas a los servidores de prueba)
* Certificado TicketBAI
* Instalación TicketBAI
* Hacienda en la que se tributa a elegir entre:

  * Araba
  * Bizkaia
  * Gipuzkoa

* Régimen simplificado (en caso de que la compañía tribute en régimen simplificado)

Instalación TicketBAI:

* Nombre del software registrado en la Hacienda
* Versión del software
* Entidad Desarrolladora
* Licencia TicketBAI (es necesario dar de alta la entidad desarrolladora en Hacienda)

En la configuración general:

* Número de serie del dispositivo (opcional)

En los parámetros del sistema:

* Alimentar el dato "database.ticketbai" con el nombre de la BBDD de la instalación. Este parámetro está concebido como medida de seguridad para evitar que una BB.DD. copiada envíe facturas que están en estado pendiente en lugar de la BB.DD. original. Se inicializará si no está presente con el nombre de la BB.DD. actual. Si está presente las actualizaciones conservarán el valor original.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_ticketbai_api%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Binovo IT Human Project S.L.

Contributors
~~~~~~~~~~~~

* Victor Laskurain <blaskurain@binovo.es>
* Guillermo Murcia <gmurcia@binovo.es>
* Alicia Rodriguez <arodriguez@binovo.es>
* Luis J. Salvatierra <ljsalvatierra@binovo.es>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-spain <https://github.com/OCA/l10n-spain/tree/11.0/l10n_es_ticketbai_api>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
