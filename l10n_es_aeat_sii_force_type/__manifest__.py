# © 2019 FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# © 2024 FactorLibre - Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Force SII communication type on invoices",
    "version": "16.0.1.0.1",
    "depends": ["l10n_es_aeat_sii_oca"],
    "category": "Accounting & Finance",
    "author": "FactorLibre, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "data": [
        "views/account_move_view.xml",
        "views/account_fiscal_position_view.xml",
    ],
    "installable": True,
    "application": False,
}
