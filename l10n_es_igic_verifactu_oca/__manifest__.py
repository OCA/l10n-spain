# Copyright 2025 Binhex - Mario Montes <m.montes@binhex.cloud>
# Copyright 2025 Binhex - Christian Ramos <c.ramos@binhex.cloud>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Comunicación Veri*FACTU IGIC",
    "summary": "Comunicación Veri*FACTU para IGIC",
    "version": "16.0.1.0.1",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Binhex," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_igic",
        "l10n_es_verifactu_oca",
    ],
    "data": [
        "data/atc_verifactu_map_data.xml",
        "data/atc_verifactu_tax_agency_data.xml",
        "data/account_fiscal_position_template_canary_data.xml",
    ],
    "post_init_hook": "post_init_hook",
}
