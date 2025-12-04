from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_es_aeat_mod390_use_303 = fields.Boolean(
        string="Use 303 reports in Mod 390",
        default=False,
    )
