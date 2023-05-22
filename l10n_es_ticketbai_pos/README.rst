=========================
TicketBAI - Point of Sale
=========================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--spain-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-spain/tree/11.0/l10n_es_ticketbai_pos
    :alt: OCA/l10n-spain

|badge1| |badge2| |badge3|

Módulo de TPV para la declaración de todas las operaciones de venta realizadas por las personas y entidades
que desarrollan actividades económicas
https://www.euskadi.eus/contenidos/informacion/ticketbai/es_14815/adjuntos/TicketBAI_Especificaciones_v_1_1.pdf

**Table of contents**

.. contents::
   :local:

Installation
============

Para instalar éste módulo necesita:

#. Los módulos l10n_es_pos, pos_order_mgmt y l10n_es_ticketbai.


Usage
=====

* Factura simplificada/Ticket de cliente

  * Se genera el fichero y se firma al validar la factura/ticket.

* Es posible utilizar un certificado específico por cada TPV, se debe crear en el menú `TicketBAI Certificados`, accesible desde la configuración de punto de venta y se establece en la configuración de cada TPV, si no se establece dicho certificado, se utiliza el definido en la compañía.

  * Es importante recordar, de cara a la seguridad, la importancia de generar un certificado de dispositivo (Izempe) ya que este se gestiona en el cliente y con dichos certificados no puede hacerse ninguna acción fuera del dispositivo.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_ticketbai_pos%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Binovo IT Human Project S.L.

Contributors
~~~~~~~~~~~~

* Victor Laskurain <blaskurain@binovo.es>
* Luis J. Salvatierra <ljsalvatierra@binovo.es>
* Miquel Alzanillas <malzanillas@apsl.net>
* Adrián Cifuentes <acifuentes@kernet.es>
* Omar Castiñeira Saavedra <omar@comunitea.com>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-spain <https://github.com/OCA/l10n-spain/tree/11.0/l10n_es_ticketbai_pos>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
