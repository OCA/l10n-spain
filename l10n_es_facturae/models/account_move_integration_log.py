# Copyright 2017-2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from odoo import _, api, exceptions, fields, models


class AccountMoveIntegrationLog(models.Model):
    _name = "account.move.integration.log"
    _description = "Result logs for integrations of moves"

    name = fields.Char(default="/", readonly=True)

    integration_id = fields.Many2one(
        comodel_name="account.move.integration", required=True, readonly=True
    )

    state = fields.Selection(
        selection=[("pending", "Pending"), ("sent", "Sent"), ("failed", "Failed")]
    )

    result_code = fields.Char()

    type = fields.Selection(
        selection=[("send", "Send"), ("update", "Update"), ("cancel", "Cancel")]
    )

    log = fields.Text()
    update_date = fields.Datetime()
    cancellation_motive = fields.Char()

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("account.move.integration.log")
                or "/"
            )
        return super(AccountMoveIntegrationLog, self).create(vals)

    def update(self):
        if self.integration_id.can_update:
            return self.update_method()
        raise exceptions.ValidationError(_("Integration cannot be update"))

    # To be overwritten
    def update_method(self):
        if self.integration_id.method_id.code == "demo":
            self.state = "sent"
            self.update_date = datetime.now()
            return
        raise exceptions.Warning(_("No update method has been created"))

    def cancel(self):
        if self.integration_id.can_update:
            return self.cancel_method()
        raise exceptions.ValidationError(_("Integration cannot be cancelled"))

    # To be overwritten
    def cancel_method(self):
        if self.integration_id.method_id.code == "demo":
            self.state = "sent"
            self.integration_id.state = "cancelled"
            self.integration_id.can_cancel = False
            return
        raise exceptions.Warning(_("No cancel method has been created"))

    def send(self):
        if self.integration_id.can_send:
            return self.send_method()
        raise exceptions.ValidationError(_("Integration cannot be sent"))

    # To be overwritten
    def send_method(self):
        if self.integration_id.method_id.code == "demo":
            self.state = "sent"
            self.integration_id.state = "sent"
            self.integration_id.can_cancel = True
            self.integration_id.can_update = True
            self.integration_id.can_send = False
            self.update_date = datetime.now()
            return
        self.state = "failed"
        raise exceptions.Warning(_("No sending method has been created"))
