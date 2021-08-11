# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "TicketBAI - "
            "declaración de todas las operaciones de venta realizadas por las personas "
            "y entidades que desarrollan actividades económicas",
    "version": "11.0.0.2.0",
    "category": "Accounting & Finance",
    "website": "http://www.binovo.es",
    "author": "Binovo,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": [
        'ljsalvatierra-binovo'
    ],
    "depends": [
        "base_vat",
        "l10n_es",
        "l10n_es_aeat",
        "l10n_es_aeat_certificate",
        "l10n_es_ticketbai_api",
        "account_invoice_tax_required",
        "l10n_es_account_invoice_sequence",
        "account_cancel"
    ],
    "external_dependencies": {
        "python": ["OpenSSL"]
    },
    "data": [
        "security/ir.model.access.csv",
        "data/tax_map_data.xml",
        "data/vat_exemption_key_data.xml",
        "data/vat_regime_key_data.xml",
        "data/account_fiscal_position_template.xml",
        "views/l10n_es_ticketbai_views.xml",
        "views/account_fiscal_position_template_views.xml",
        "views/account_fiscal_position_views.xml",
        "views/account_invoice_views.xml",
        "views/report_invoice.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/tax_map_views.xml",
        "views/ticketbai_invoice_views.xml",
        "views/vat_exemption_key_views.xml",
        "views/vat_regime_key_views.xml",
        "wizard/ticketbai_info_views.xml"
    ],
    "post_init_hook": "post_init_hook",
}
