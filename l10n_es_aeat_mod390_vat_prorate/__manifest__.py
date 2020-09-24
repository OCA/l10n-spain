# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT - Prorrata de IVA 390",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Invoices & Payments",
    "depends": [
        "l10n_es_aeat_mod390",
    ],
    "maintainers": ["victoralmau"],
    "data": [
        "data/aeat_export_mod390_prorate_data.xml",
        "security/ir.model.access.csv",
        "views/mod390_view.xml"
    ],
    "installable": True,
}
