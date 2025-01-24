# Copyright 2025 Binhex - Christian Ramos Barrera
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Creación de Facturae IGIC",
    "version": "16.0.1.0.0",
    "author": "Binhex, Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_facturae",
        "l10n_es_igic",
    ],
    "data": [
        "data/account_tax_template.xml",
    ],
    "installable": True,
    "autoinstall": True,
    "maintainers": ["Christian-RB"],
}
