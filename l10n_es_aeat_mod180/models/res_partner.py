from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    real_estate_ids = fields.One2many("l10n.es.aeat.real_estate", "partner_id")
