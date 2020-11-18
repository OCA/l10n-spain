# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountMoveIntegrationMethod(models.Model):
    _name = "account.move.integration.method"
    _description = "Integration method for moves"

    name = fields.Char()
    code = fields.Char(readonly=True)
    sequence_id = fields.Many2one(
        comodel_name="ir.sequence", readonly=True, required=True
    )

    # Default values for integration. It could be extended
    def integration_values(self, move):
        return {"method_id": self.id, "move_id": move.id}

    def create_integration(self, move):
        self.ensure_one()
        self.env["account.move.integration"].create(self.integration_values(move))
