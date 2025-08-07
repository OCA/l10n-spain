# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Canon digital",
    "summary": "Aplicación automática del canon digital en facturas, ventas y compras",
    "version": "14.0.1.0.0",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["account", "l10n_es"],
    "data": [
        "reports/invoice_document_report.xml",
        "data/account_tax_data.xml",
        "views/res_partner_views.xml",
        "views/product_product_views.xml",
    ],
    "installable": True,
}
