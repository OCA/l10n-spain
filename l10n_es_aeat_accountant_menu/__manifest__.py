# Copyright 2022 Eduardo de Miguel <edu@moduon.team> - Moduon Team
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    "name": "AEAT Enterprise menu",
    "summary": "Modulo para mover el menú de AEAT "
    "dentro de la APP de Contabilidad en Enterprise",
    "version": "14.0.1.0.0",
    "author": "Moduon, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting & Finance",
    "development_status": "Mature",
    "depends": [
        "l10n_es_aeat",
    ],
    "data": [
        "views/aeat_menuitem.xml",
    ],
    "installable": True,
    "maintainers": ["shide"],
}
