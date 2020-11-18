# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveIntegrationCancel(models.TransientModel):
    _name = "account.move.integration.cancel"
    _description = "Cancels a created integration"

    integration_id = fields.Many2one(comodel_name="account.move.integration")

    def cancel_values(self):
        return {"integration_id": self.integration_id.id, "type": "cancel"}

    def cancel_integration(self):
        self.ensure_one()
        self.env["account.move.integration.log"].create(self.cancel_values()).cancel()
