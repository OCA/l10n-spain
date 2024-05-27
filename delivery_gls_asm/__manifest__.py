# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery GLS-ASM",
    "summary": "Delivery Carrier implementation for GLS with ASMRed API",
    "version": "16.0.1.1.1",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery_package_number", "delivery_state"],
    "external_dependencies": {"python": ["suds-py3"]},
    "data": [
        "data/delivery_asm_data.xml",
        "security/ir.model.access.csv",
        "views/delivery_asm_view.xml",
        "views/gls_asm_manifest_template.xml",
        "views/stock_picking_views.xml",
        "wizard/gls_asm_manifest_wizard_views.xml",
    ],
    "maintainers": ["chienandalu", "hildickethan-S73"],
}
