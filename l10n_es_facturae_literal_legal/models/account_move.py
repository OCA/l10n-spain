# Copyright 2025 (APSL-Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    literal_legal_ids = fields.One2many(
        "l10n.es.facturae.literal.legal",
        "move_id",
        string="Literal Legal",
        copy=True,
    )


class LiteralLegal(models.Model):
    _name = "l10n.es.facturae.literal.legal"
    _description = "Facturae Literal Legal"
    _order = "sequence, id"

    description = fields.Text(required=True)
    description_length = fields.Integer(
        compute="_compute_description_length",
        store=True,
    )
    move_id = fields.Many2one(comodel_name="account.move", string="Move", readonly=True)
    sequence = fields.Integer()

    @api.depends("description")
    def _compute_description_length(self):
        for record in self:
            record.description_length = len(record.description or "")

    @api.model_create_multi
    def create(self, vals_list):
        new_records = self.env[self._name]
        for vals in vals_list:
            description = vals.get("description", "")
            # Divide the description into chunks of 250 characters
            # if it exceeds that length
            if description and len(description) > 250:
                chunks = [
                    description[i : i + 250] for i in range(0, len(description), 250)
                ]
                for chunk in chunks:
                    new_records |= super().create({**vals, "description": chunk})
            else:
                new_records |= super().create(vals)

        return new_records

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            if record.description and len(record.description) > 250:
                raise ValidationError(
                    _("Literal legal description cannot be longer than 250 characters")
                )
        return res
