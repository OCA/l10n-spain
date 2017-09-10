# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


XMLID_RENAMES = [
    ("l10n_es_toponyms.ES15", "base.state_es_c"),
    ("l10n_es_toponyms.ES01", "base.state_es_vi"),
    ("l10n_es_toponyms.ES02", "base.state_es_ab"),
    ("l10n_es_toponyms.ES03", "base.state_es_a"),
    ("l10n_es_toponyms.ES04", "base.state_es_al"),
    ("l10n_es_toponyms.ES33", "base.state_es_o"),
    ("l10n_es_toponyms.ES05", "base.state_es_av"),
    ("l10n_es_toponyms.ES06", "base.state_es_ba"),
    ("l10n_es_toponyms.ES07", "base.state_es_pm"),
    ("l10n_es_toponyms.ES08", "base.state_es_b"),
    ("l10n_es_toponyms.ES09", "base.state_es_bu"),
    ("l10n_es_toponyms.ES10", "base.state_es_cc"),
    ("l10n_es_toponyms.ES11", "base.state_es_ca"),
    ("l10n_es_toponyms.ES39", "base.state_es_s"),
    ("l10n_es_toponyms.ES12", "base.state_es_cs"),
    ("l10n_es_toponyms.ES51", "base.state_es_ce"),
    ("l10n_es_toponyms.ES13", "base.state_es_cr"),
    ("l10n_es_toponyms.ES14", "base.state_es_co"),
    ("l10n_es_toponyms.ES16", "base.state_es_cu"),
    ("l10n_es_toponyms.ES17", "base.state_es_gi"),
    ("l10n_es_toponyms.ES18", "base.state_es_gr"),
    ("l10n_es_toponyms.ES19", "base.state_es_gu"),
    ("l10n_es_toponyms.ES20", "base.state_es_ss"),
    ("l10n_es_toponyms.ES21", "base.state_es_h"),
    ("l10n_es_toponyms.ES22", "base.state_es_hu"),
    ("l10n_es_toponyms.ES23", "base.state_es_j"),
    ("l10n_es_toponyms.ES26", "base.state_es_lo"),
    ("l10n_es_toponyms.ES35", "base.state_es_gc"),
    ("l10n_es_toponyms.ES24", "base.state_es_le"),
    ("l10n_es_toponyms.ES25", "base.state_es_l"),
    ("l10n_es_toponyms.ES27", "base.state_es_lu"),
    ("l10n_es_toponyms.ES28", "base.state_es_m"),
    ("l10n_es_toponyms.ES29", "base.state_es_ma"),
    ("l10n_es_toponyms.ES52", "base.state_es_ml"),
    ("l10n_es_toponyms.ES30", "base.state_es_mu"),
    ("l10n_es_toponyms.ES31", "base.state_es_na"),
    ("l10n_es_toponyms.ES32", "base.state_es_or"),
    ("l10n_es_toponyms.ES34", "base.state_es_p"),
    ("l10n_es_toponyms.ES36", "base.state_es_po"),
    ("l10n_es_toponyms.ES37", "base.state_es_sa"),
    ("l10n_es_toponyms.ES38", "base.state_es_tf"),
    ("l10n_es_toponyms.ES40", "base.state_es_sg"),
    ("l10n_es_toponyms.ES41", "base.state_es_se"),
    ("l10n_es_toponyms.ES42", "base.state_es_so"),
    ("l10n_es_toponyms.ES43", "base.state_es_t"),
    ("l10n_es_toponyms.ES44", "base.state_es_te"),
    ("l10n_es_toponyms.ES45", "base.state_es_to"),
    ("l10n_es_toponyms.ES46", "base.state_es_v"),
    ("l10n_es_toponyms.ES47", "base.state_es_va"),
    ("l10n_es_toponyms.ES48", "base.state_es_bi"),
    ("l10n_es_toponyms.ES49", "base.state_es_za"),
    ("l10n_es_toponyms.ES50", "base.state_es_z"),
]


@openupgrade.migrate()
def migrate(env, version):
    """Rename XML-IDs for not duplicating states as now Odoo core has
    integrated them.
    """
    openupgrade.rename_xmlids(env.cr, XMLID_RENAMES)
