# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    sigaus_has_amount = fields.Boolean(compute="_compute_sigaus_has_amount", store=True)

    @api.depends("sigaus_subject", "categ_id", "categ_id.sigaus_subject")
    def _compute_sigaus_has_amount(self):
        for rec in self:
            rec.sigaus_has_amount = rec.sigaus_subject == "yes" or (
                rec.sigaus_subject == "category" and rec.categ_id.sigaus_subject
            )
