# Copyright 2023 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    companies = env["res.company"].search([])
    fps = env["account.fiscal.position"]
    for company in companies:
        fps |= company.get_fps_from_templates(
            env.ref("l10n_es.fp_recargo") + env.ref("l10n_es.fp_recargo_isp")
        )
    fps.write(
        {"tbai_vat_regime_key": env.ref("l10n_es_ticketbai.tbai_vat_regime_01").id}
    )
