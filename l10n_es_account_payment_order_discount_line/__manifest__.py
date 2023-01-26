# Copyright 2022 Punt Sistemes - Isaac Gallart
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Control líneas de descuento",
    "summary": "Contabilidad",
    "version": "13.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Punt Sistemes, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": [
        "igallart@puntsistemes.es",
        "portega@puntsistemes.es",
        "sbenlloch@puntsistemes.es",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
    "data": [
        "views/account_payment_mode_view.xml",
        "views/account_payment_order_view.xml",
    ],
    "depends": ["account_payment_mode", "account_payment_order", "l10n_es"],
}
