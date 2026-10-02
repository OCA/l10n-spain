# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "España - Reporte DeCA (Lotes)",
    "summary": "Impresión de DeCA desde Agrupaciones de Albaranes",
    "version": "19.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_deca_oca",
        "stock_picking_batch",
    ],
    "data": [
        "report/stock_picking_batch_reports.xml",
        "report/report_picking_deca.xml",
    ],
}
