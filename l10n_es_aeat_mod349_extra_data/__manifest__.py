# Copyright (C) 2023 FactorLibre - Rodrigo Bonilla
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "AEAT modelo 349 - Datos extra",
    "summary": "Módulo para incluir los impuestos extra en el modelo 349.",
    "author": "FactorLibre (www.factorlibre.com), Odoo Community Association (OCA)",
    "maintainers": ["FactorLibre"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "version": "12.0.1.0.0",
    "depends": ["l10n_es_aeat_mod349", "l10n_es_extra_data"],
    "data": ["data/aeat_349_map_data.xml"],
    "installable": True,
    "autoinstall": True,
}
