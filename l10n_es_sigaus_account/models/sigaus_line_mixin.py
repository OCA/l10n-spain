# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SigausLineMixin(models.AbstractModel):
    _name = "sigaus.line.mixin"
    _description = "Sigaus Line Mixin"

    is_sigaus = fields.Boolean(copy=True, default=False)
    sigaus_amount = fields.Float(
        compute="_compute_sigaus_amount", digits="Product Price"
    )

    _sigaus_secondary_unit_fields = {}

    def _compute_sigaus_amount(self):
        for rec in self:
            sigaus_amount = 0.0
            if rec.product_id and rec.product_id.sigaus_has_amount:
                price = self.env["l10n.es.sigaus.amount"].get_sigaus_amount(
                    rec[rec._sigaus_secondary_unit_fields["parent_id"]][
                        rec._sigaus_secondary_unit_fields["date_field"]
                    ]
                )
                quantity = rec[
                    rec._sigaus_secondary_unit_fields["uom_field"]
                ]._compute_quantity(
                    rec[rec._sigaus_secondary_unit_fields["qty_field"]],
                    rec.product_id.uom_id,
                )
                weight = quantity * rec.product_id.weight
                sigaus_amount = weight * price
            rec.sigaus_amount = sigaus_amount
