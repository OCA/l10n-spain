=======================
TicketBAI - OSS Support
=======================

.. |badge1| image:: https://img.shields.io/badge/maturity-Alpha-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Alpha
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1| |badge2|

Módulo para hacer compatible el envío de facturas Ticketbai con el OSS

Añade 2 campos nuevos en los impuestos (account.tax):

* Tipo de causa de no sujeción (se añade el tipo IE)
* Tipo de impuesto Ticketbai

A la hora de generar el fichero XML de envío a TicketBai, si estos campos están rellenados,
se tendrán en cuenta dichos campos, sino seguirá el flujo normal como hasta ahora.


**Table of contents**

.. contents::
   :local:

Installation
============

Para instalar este módulo se necesita:

#. Los módulos l10n_es_ticketbai

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_ticketbai_oss%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Binovo IT Human Project S.L.

Contributors
~~~~~~~~~~~~

* Alicia Rodríguez <arodriguez@binovo.es>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-spain <https://github.com/OCA/l10n-spain/tree/12.0/l10n_es_ticketbai_oss>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
