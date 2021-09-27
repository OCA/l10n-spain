# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    map_lines = env.ref("l10n_es_dua_sii.aeat_sii_map_line_DUA")
    map_lines.write(
        {
            "taxes": [
                (3, env.ref("l10n_es.account_tax_template_p_iva21_sp_ex").id),
                (3, env.ref("l10n_es.account_tax_template_p_iva10_sp_ex").id),
                (3, env.ref("l10n_es.account_tax_template_p_iva4_sp_ex").id),
            ]
        }
    )
