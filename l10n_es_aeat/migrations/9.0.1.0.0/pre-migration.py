# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

TABLE_RENAMES = [
    ('aeat_mod_map_tax_code', 'l10n_es_aeat_map_tax'),
    ('aeat_mod_map_tax_code_line', 'l10n_es_aeat_map_tax_line'),
]
MODEL_RENAMES = [
    ('aeat.mod.map.tax.code', 'l10n.es.aeat.map.tax'),
    ('aeat.mod.map.tax.code.line', 'l10n.es.aeat.map.tax.line'),
]


@openupgrade.migrate()
def migrate(cr, version):
    openupgrade.rename_tables(cr, TABLE_RENAMES)
    openupgrade.rename_models(cr, MODEL_RENAMES)
