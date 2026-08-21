# Copyright 2025 Binhex - Mario Montes <m.montes@binhex.cloud>
# Copyright 2025 Binhex - Christian Ramos <c.ramos@binhex.cloud>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Comunicación Veri*FACTU IGIC",
    "summary": "Comunicación Veri*FACTU para IGIC",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Binhex, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es",
        "l10n_es_verifactu_oca",
    ],
    "data": [
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/atc_verifactu_map_data.xml",
        "data/atc_verifactu_tax_agency_data.xml",
    ],
    "post_init_hook": "post_init_hook",
}
