# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "TicketBAI - Batuz - "
            "declaración de todas las operaciones de venta realizadas por las personas "
            "y entidades que desarrollan actividades económicas en Bizkaia",
    "version": "12.0.1.3.1",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Binovo,"
              "Digital5,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "development_status": "Alpha",
    "maintainers": [
        "Binovo",
        "enriquemartin"
    ],
    "depends": [
        "l10n_es_ticketbai_api_batuz",
        "l10n_es_ticketbai",
        "queue_job",
    ],
    "data": [
        "security/ir_rule.xml",
        "data/tbai_vat_regime_key_data.xml",
        "data/account_fiscal_position_template_data.xml",
        "data/queue_job_data.xml",
        "data/tbai_tax_map_data.xml",
        "wizard/account_invoice_refund_views.xml",
        "views/account_fiscal_position_views.xml",
        "views/account_invoice_views.xml",
        "views/lroe_operation_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/tbai_vat_regime_key_views.xml",
        "views/account_journal_views.xml",
    ],
    "post_init_hook": "post_init_hook",
}
