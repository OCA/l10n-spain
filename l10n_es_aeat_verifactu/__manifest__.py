# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Comunicación Veri*FACTU",
    "version": "16.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Aures Tic, ForgeFlow," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": ["zeep", "requests"]},
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
        "account_invoice_refund_link",
        "queue_job",
        "account",
    ],
    "data": [
        "data/aeat_verifactu_tax_agency_data.xml",
        "data/aeat_verifactu_registration_keys.xml",
        "data/aeat_verifactu_map_data.xml",
        "security/ir.model.access.csv",
        "views/aeat_tax_agency_view.xml",
        "views/account_move_view.xml",
        "views/account_fiscal_position_view.xml",
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
        "views/account_journal_view.xml",
        "views/aeat_verifactu_map_view.xml",
        "views/aeat_verifactu_map_lines_view.xml",
        "views/aeat_verifactu_registration_keys_view.xml",
        "views/report_invoice.xml",
    ],
}
