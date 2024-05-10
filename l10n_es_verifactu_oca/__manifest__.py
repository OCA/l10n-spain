# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Comunicación Veri*FACTU",
    "version": "16.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Aures Tic," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    # "external_dependencies": {"python": ["zeep", "requests"]},
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
        # "queue_job",
    ],
    "data": [
        "data/aeat_sii_tax_agency_data.xml",
        "views/aeat_tax_agency_view.xml",
        "views/account_move_view.xml",
        "views/account_fiscal_position_view.xml",
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
    ],
}
