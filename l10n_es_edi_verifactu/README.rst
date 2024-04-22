.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :alt: License: AGPL-3

Spain - Verifactu
=================

When posting an invoice, a Verifactu XML is created, sending of the XML to the Verifactu systems is not implemented
because there is not developing environment yet.

Supported and tested validation schemas: 0.11.5	03/04/2024

Supported and tested invoices:

* Standard sale invoice to a Spanish customer
* Taxes: Exento, Sujeto, No Sujeto, No Sujeto por reglas de Localization

Not supported invoices, in these cases, when invoice confirmation a validation error is raised and the invoice
is not validated:

* Sale invoices to EU customers, services and merchandises
* Exportation, sale invoices to non EU customers, services and merchandises
* Refund invoices
* Simplified invoices
* Taxes: Sujeto ISP, Retencion, Recargo de Equivalencia
* Cancellation of invoices

Dependencies
============

Module: l10n_es_edi_sii

System: to execute verifactu-xmlgen node is required, version Debian Bookworm v18.19.0.

Configuration
=============

l10n_es_edi_verifactu.verifactu_xml_cmd config_parameter indicates which version of command to use to generates Verifactu xml files, default value is addon_dir/lib/verifactu-xmlgen, the command is distributed with the addon it self.

Credits
=======

Contributors
------------

* Ugaitz Olaizola <uolaizola@binovo.es>

Maintainer
----------

.. image:: /l10n_es_edi_verifactu/static/description/icon.png
   :alt: Binovo IT Human Project SL
   :target: http://www.binovo.es

This module is maintained by Binovo IT Human Project SL.
