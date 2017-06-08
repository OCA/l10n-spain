.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Categoría profesional
=====================

Este módulo extiende la funcionalidad del gestor de contactos para permitir
añadir a cada contacto una categoría profesional, la cual es necesaria para
ciertos tipos de comunicación con la Seguridad Social.

.. warning::
    No confunda las categorías profesionales con el grupo de cotización. Eso es
    otro módulo diferente.

Installation
============

To install this module, you need to:

* Install the `partner-contact`_ repository.
* Install the `l10n-spain`_ repository.

Configuration
=============

Default professional categories are:

1. Executive
2. Intermediate head
3. Technician
4. Qualified worker
5. Low-qualified worker

If you wish to change those, your user must have the following permissions:

* Sales / Manager. You may install the ``sale`` module for that.
* Technical features.

Then go to *Sales > Configuration > Address Book > Professional Categories* and
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

* If you edit any of the default professional categories, those will be reset
  if you upgrade the module.

Credits
=======

Default professional categories taken from `Cuestionario de evaluación`_.

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
.. _Cuestionario de evaluación: http://www.fundaciontripartita.org/Empresas%20y%20organizaciones/Documents/Cuestionario%20de%20Evaluaci%C3%B3n.pdf
