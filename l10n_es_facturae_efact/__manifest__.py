# Copyright 2015 Creu Blanca
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Envío de Factura-e a e.FACT",
    "version": "13.0.2.0.0",
    "author": "Creu Blanca, " "Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_facturae_face"],
    "data": ["data/efact_data.xml"],
    "external_dependencies": {"python": ["paramiko", "OpenSSL", "xmlsec"]},
    "installable": True,
}
