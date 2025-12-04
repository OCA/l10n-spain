from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_es_aeat_mod390_use_303 = fields.Boolean(
        related="company_id.l10n_es_aeat_mod390_use_303",
        readonly=False,
    )
