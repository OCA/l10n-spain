.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==================================================
Account Banking Sepa - FSDD (Anticipos de crédito)
==================================================

Este módulo permite establecer el prefijo FSDD en el identificador de un
fichero sepa para el producto nicho de anticipos de crédito, antiguamente
exportado en el cuaderno 58.

Installation
============

Para instalar este módulo, es necesario tener disponible el módulo
*account_banking_sepa_direct_debit* del repositorio
https://github.com/OCA/bank-payment

Usage
=====

Se dispone de un campo "Cobro financiado" en el modo de pago, si se marca,
al exportar la órden de cobro con ese modo de pago nos añadirá FSDD
al identificador del fichero.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/l10n-spain/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Omar Castiñeira Saavedra <omar@comunitea.com>
* Luis M. Ontalba <luis.martinez@tecnativa.com>

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
