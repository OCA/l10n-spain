# Copyright (C) 2023 FactorLibre - Alejandro Ji Cheung
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "AEAT modelo 390 - Datos extra",
    "summary": "Módulo para incluir los impuestos extra en el modelo 390.",
    "author": "FactorLibre (www.factorlibre.com), Odoo Community Association (OCA)",
    "maintainers": ["FactorLibre"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "version": "11.0.2.0.0",
    "depends": ["l10n_es_aeat_mod390", "l10n_es_extra_data"],
    "data": ["data/2022/l10n_es_aeat_map_tax_line.xml"],
    "installable": True,
    "autoinstall": True,
}
