# -*- coding: utf-8 -*-
# © 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "AEAT modelo 347 - Datos extra",
    "summary": "Módulo para incluir los impuestos extra en el modelo 347.",
    "author": "Binovo,"
              "Odoo Community Association (OCA)",
    "maintainers": ["Binovo"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "version": "12.0.1.0.0",
    "depends": ["l10n_es_aeat_mod347", "l10n_es_extra_data"],
    "data": ["data/l10n_es_aeat_map_tax_line.xml"],
    "installable": True,
    "autoinstall": True,
}
