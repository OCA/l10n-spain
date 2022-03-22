# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    fps = env["account.fiscal.position"]
    for company in companies:
        fps |= company.get_fps_from_templates(env.ref("l10n_es.fp_extra"))
    fps.write({"tbai_vat_regime_purchase_key": env.ref(
        "l10n_es_ticketbai_batuz.tbai_vat_regime_purchase_01").id})
