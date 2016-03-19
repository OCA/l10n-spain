.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================================
Account balance reporting engine
================================

The module allows the user to create account balance reports and templates,
comparing the values of 'accounting concepts' between two fiscal years
or a set of fiscal periods.

Accounting concepts values can be calculated as the sum of some account
balances, the sum of its children, other account concepts or constant values.

Generated reports are stored as objects on the server,
so you can check them anytime later or edit them
(to add notes for example) before printing.

The module lets the user add new templates of the reports concepts,
and associate them an specific "XML report" (OpenERP RML files for example)
with the design used when printing.
So it is very easy to add predefined country-specific official reports.

The user interface has been designed to be as much user-friendly as it can be.

Note: It has been designed to meet Spanish/Spain localization needs,
but it might be used as a generic accounting report engine.

Configuration
=============

#. Go to *Accounting > Configuration > Financial Reports > Financial Reports*.
#. Create or edit one existing template.
#. Add report lines with formulas to configure your financial report.

Usage
=====

#. Go to *Accounting > Reporting > Legal Reports > Accounting Reports > Financial Reports*.
#. Select a reporting template.
#. Select dates or periods.
#. Click on *Calculate*.
#. See results on *"Report lines"* tab.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Known issues / Roadmap
======================

* Accounts in other currencies are not converted to the company currency.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/l10n-spain/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/OCA/
l10n-spain/issues/new?body=module:%20
account_balance_reporting%0Aversion:%20
8.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Borja López Soilán <borjals@pexego.es>
* Iker Coranti (AvanzOSC)
* Juanjo Algaz <juanjoa@malagatic.com>
* Joaquín Gutierrez <joaquing.pedrosa@gmail.com>
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>

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