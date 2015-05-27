.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Grupo de cotización en los contactos
====================================

Este módulo extiende la funcionalidad del gestor de contactos para permitir
añadir a cada contacto un grupo de cotización, el cual es necesario para
ciertos tipos de comunicación con la Seguridad Social.

.. warning::
    No confunda el grupo de cotización con la categoría profesional. Eso es
    otro módulo diferente.

Installation
============

To install this module, you need to:

* Install the `partner-contact`_ repository.
* Install the `l10n-spain`_ repository.

Configuration
=============

There are 11 default contribution groups. If you wish to change those, your
user must have the following permissions:

* Sales / Manager. You may install the ``sale`` module for that.
* Technical features.

Then go to *Sales > Configuration > Address Book > Contribution Groups* and
edit what you want.

Usage
=====

To use this module, you need to:

* Edit a partner or create a new one.
* Ensure the partner is **not** a company.
* Go to the *Personal information* sheet.
* Set the professional category there.

For further information, please visit:

* https://www.odoo.com/forum/help-1
* https://github.com/OCA/l10n-spain/

Known issues / Roadmap
======================

* If you edit any of the default contribution groups, those will be reset if
  you upgrade the module.

Credits
=======

Default contribution groups taken from `seg-social.es`_ and the inner usage of
the https://empresas.fundaciontripartita.org web app.

Contributors
------------

* Jairo Llopis <j.llopis@grupoesoc.es>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.


.. _l10n-spain: https://github.com/OCA/l10n-spain/
.. _partner-contact: https://github.com/OCA/partner-contact/
.. _seg-social.es: http://www.seg-social.es/Internet_1/Trabajadores/CotizacionRecaudaci10777/Basesytiposdecotiza36537/index.htm
