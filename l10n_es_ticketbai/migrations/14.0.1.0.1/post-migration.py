# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    fps = env["account.fiscal.position"]
    for company in companies:
        fps |= company.get_fps_from_templates(env.ref("l10n_es.fp_not_subject_tai"))
    fps.write(
        {"tbai_vat_regime_key": env.ref("l10n_es_ticketbai.tbai_vat_regime_08").id}
    )
