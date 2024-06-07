# Copyright 2023 Tecnativa - Ernesto García Medina
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Exportación de fichero bancario Confirming estándar AEF",
    "version": "16.0.1.1.0",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "category": "Localisation/Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["account_payment_order", "l10n_es"],
    "data": [
        "data/account_payment_method.xml",
        "views/account_payment_mode_view.xml",
    ],
    "installable": True,
}
