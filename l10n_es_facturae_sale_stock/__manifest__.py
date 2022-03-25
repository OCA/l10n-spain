# Copyright 2017 Creu Blanca
# Copyright 2020 NuoBiT Solutions - Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Entregas en Factura-e",
    "version": "11.0.1.0.0",
    "author": "Creu Blanca, " "NuoBiT Solutions, " "Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_facturae",
        "stock_picking_invoice_link",
    ],
    "data": [
        "views/report_facturae.xml",
    ],
    "installable": True,
    "auto_install": False,
}
