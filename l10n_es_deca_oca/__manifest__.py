# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "España - Reporte DeCA",
    "summary": "Document for electronic Control of Administration (DeCA)",
    "version": "19.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_delivery",
    ],
    "external_dependencies": {
        "python": ["pypdf"],
    },
    "data": [
        "data/ir_actions_server_data.xml",
        "report/stock_picking_reports.xml",
        "report/report_picking_deca.xml",
        "views/stock_picking_views.xml",
        "views/delivery_carrier_views.xml",
    ],
}
