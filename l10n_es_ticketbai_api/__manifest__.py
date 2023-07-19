# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "TicketBAI - API",
    "version": "16.0.1.0.4",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Binovo," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": ["ao-landoo"],
    "depends": ["base", "base_setup"],
    "external_dependencies": {
        "python": [
            "qrcode",
            "xmlsig",
            "xmltodict",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/l10n_es_ticketbai_security.xml",
        "data/tax_agency_data.xml",
        "data/ticketbai_invoice.xml",
        "views/l10n_es_ticketbai_api_views.xml",
        "views/res_company_views.xml",
        "views/res_config_settings_views.xml",
        "views/ticketbai_certificate_views.xml",
        "views/ticketbai_installation_views.xml",
    ],
    "demo": ["demo/res_partner_demo.xml"],
}
