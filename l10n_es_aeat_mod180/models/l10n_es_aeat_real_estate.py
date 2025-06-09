from odoo import api, fields, models


class L10nEsAeatRealEstate(models.Model):
    _inherit = "l10n.es.aeat.real_estate"

    real_estate_situation = fields.Selection(
        [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04")],
        compute="_compute_real_estate_situation",
        store=True,
        readonly=False,
    )

    @api.depends("zip", "reference", "state_id.code")
    def _compute_real_estate_situation(self):
        for rec in self:
            if not rec.reference:
                rec.real_estate_situation = "4"
            elif rec.zip:
                code = rec.state_id.code
                if code and code not in ["NA", "BI", "SS", "VI"]:
                    rec.real_estate_situation = "1"
                elif code in ["BI", "SS", "VI"]:
                    rec.real_estate_situation = "2"
                elif code == "NA":
                    rec.real_estate_situation = "3"
