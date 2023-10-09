# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Set the intrastat field of the private fiscal position records.
    This is necessary for the intrastat report generation
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    items = env["ir.model.data"].search(
        [
            ("model", "=", "account.fiscal.position"),
            ("name", "like", "%_fp_intra%"),
            ("module", "=", "l10n_es"),
        ]
    )
    env["account.fiscal.position"].browse(items.mapped("res_id")).write(
        {"intrastat": "b2b", "vat_required": True}
    )
