# Copyright 2024 Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

import pytz

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    verifactu_enabled = fields.Boolean(string="Enable veri*FACTU")
    verifactu_test = fields.Boolean(string="Is it the veri*FACTU test environment?")
    verifactu_description = fields.Text(
        default="/",
        size=500,
        help="The description for Verifactu invoices if not set",
    )
    verifactu_last_invoice_id = fields.Many2one(
        string="Last veri*FACTU Invoice sent",
        comodel_name="account.move",
        copy=False,
    )
    use_connector_verifactu = fields.Boolean(
        help="Check it to use connector instead of sending the invoice "
        "directly when it's validated",
    )
    send_mode_verifactu = fields.Selection(
        selection=[
            ("auto", "On validate"),
            ("fixed", "At fixed time"),
            ("delayed", "With delay"),
        ],
        default="auto",
    )
    sent_time_verifactu = fields.Float()
    delay_time_verifactu = fields.Float()

    def _get_verifactu_eta(self):
        if self.send_mode_verifactu == "fixed":
            tz = self.env.context.get("tz", self.env.user.partner_id.tz)
            offset = datetime.now(pytz.timezone(tz)).strftime("%z") if tz else "+00"
            hour_diff = int(offset[:3])
            hour, minute = divmod(self.sent_time_verifactu * 60, 60)
            hour = int(hour - hour_diff)
            minute = int(minute)
            now = datetime.now()
            if now.hour > hour or (now.hour == hour and now.minute > minute):
                now += timedelta(days=1)
            now = now.replace(hour=hour, minute=minute)
            return now
        elif self.send_mode_verifactu == "delayed":
            return datetime.now() + timedelta(seconds=self.delay_time_verifactu * 3600)
        else:
            return None
