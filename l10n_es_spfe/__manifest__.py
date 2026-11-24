# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AEAT SPFE - Solución Pública de Facturación Electrónica",
    "summary": (
        "Presentación, consulta, descarga y comunicación de estados de facturas "
        "electrónicas en el SPFE de la AEAT"
    ),
    "version": "19.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "maintainers": ["acysos"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "development_status": "Beta",
    "depends": [
        "l10n_es_aeat",
        "base_ubl_parse",
        "account_tax_unece",
        "account_payment_mode",
        "account_payment_unece",
        "uom_unece",
    ],
    "external_dependencies": {
        "python": ["lxml", "requests"],
    },
    "data": [
        "security/spfe_security.xml",
        "security/ir.model.access.csv",
        "data/unece_data.xml",
        "data/spfe_registration_key_data.xml",
        "data/aeat_tax_agency_data.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "wizards/spfe_cancel_invoice_wizard_views.xml",
        "wizards/spfe_invoice_event_wizard_views.xml",
        "wizards/spfe_sync_invoices_wizard_views.xml",
        "views/spfe_registration_key_views.xml",
        "views/spfe_submission_views.xml",
        "views/aeat_tax_agency_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/account_journal_views.xml",
        "views/account_fiscal_position_views.xml",
        "views/account_tax_views.xml",
        "views/account_move_views.xml",
        "views/spfe_menuitem.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
