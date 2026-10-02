# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Insurance Caser",
    "summary": "Automate insurance policy request with Caser",
    "version": "18.0.1.0.0",
    "category": "Sales/Sales",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["juancarlosonate-tecnativa"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "sale_stock",
        "queue_job",
        "product_brand",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/queue_job_channel_data.xml",
        "data/caser_price_range_data.xml",
        "data/ir_actions_server.xml",
        "views/caser_price_range_views.xml",
        "views/product_brand_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_views.xml",
        "views/product_category_views.xml",
    ],
}
