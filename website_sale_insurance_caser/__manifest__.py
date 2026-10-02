# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Website Sale Insurance Caser",
    "summary": "Add Caser insurance to eCommerce products",
    "version": "18.0.1.0.0",
    "category": "Website/Website",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["juancarlosonate-tecnativa"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "sale_insurance_caser",
        "website_sale",
    ],
    "data": [
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_sale_insurance_caser/static/src/js/website_sale_insurance_caser.esm.js",
            "website_sale_insurance_caser/static/src/js/checkout_insurance.esm.js",
        ],
    },
}
