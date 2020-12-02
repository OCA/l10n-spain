{
    "name": "SILICIE",
    "version": "12.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Alquemy",
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {
        "python": [
            "zeep",
            "requests",
            "OpenSSL",
        ],
    },
    "depends": [
        "l10n_es_aeat",
        "stock",
        "queue_job",
        "report_csv",
        "purchase",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "data/aeat_move_type_silicie_data.xml",
        "data/aeat_container_type_silicie_data.xml",
        "data/aeat_epigraph_silicie_data.xml",
        "data/aeat_product_key_silicie_data.xml",
        "data/aeat_uom_silicie_data.xml",
        "data/aeat_proof_type_silicie_data.xml",
        "data/aeat_processing_silicie_data.xml",
        "data/aeat_loss_silicie_data.xml",
        "data/sequence.xml",
        "data/cron.xml",
        "views/aeat_move_type_silicie_views.xml",
        "views/aeat_container_type_silicie_views.xml",
        "views/aeat_epigraph_silicie_views.xml",
        "views/aeat_product_key_silicie_views.xml",
        "views/aeat_uom_silicie_views.xml",
        "views/aeat_proof_type_silicie_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/product_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_move_views.xml",
        "views/account_fiscal_position_views.xml",
        "views/queue_job_views.xml",
        "reports/aeat_silicie_csv_export_views.xml",
        "wizards/import_silicie_views.xml",
        "wizards/not_declare_wizard_views.xml",
        "wizards/regenerate_wizard_views.xml",
        "wizards/send_aeat_wizard_views.xml",
    ],
}
