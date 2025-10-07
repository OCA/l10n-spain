# Copyright 2024 Aures Tic - Jose Zambudio
# Copyright 2024,2025 Aures TIC - Almudena de La Puente
# Copyright 2024 FactorLibre - Aritz Olea
# Copyright 2024,2025 ForgeFlow S.L.
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Comunicación VERI*FACTU",
    "version": "18.0.1.1.0",
    "category": "Accounting/Localizations/EDI",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Aures Tic,"
    "ForgeFlow,"
    "Tecnativa,"
    "Factor Libre,"
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account_invoice_refund_link", "l10n_es_aeat"],
    "data": [
        "data/verifactu_tax_agency_data.xml",
        "data/verifactu_registration_key_data.xml",
        "data/l10n.es.aeat.map.tax.line.tax.csv",  # should be before verifactu.map*
        "data/verifactu.map.csv",
        "data/verifactu.map.line.csv",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "data/mail_activity_data.xml",
        "security/verifactu_security.xml",
        "security/ir.model.access.csv",
        "views/aeat_tax_agency_view.xml",
        "views/account_move_view.xml",
        "views/account_fiscal_position_view.xml",
        "views/res_company_view.xml",
        "views/account_journal_view.xml",
        "views/verifactu_map_view.xml",
        "views/verifactu_map_lines_view.xml",
        "views/verifactu_registration_keys_view.xml",
        "views/verifactu_invoice_entry_view.xml",
        "views/verifactu_chaining_view.xml",
        "views/verifactu_developer_view.xml",
        "views/report_invoice.xml",
        "views/verifactu_invoice_entry_response_view.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
