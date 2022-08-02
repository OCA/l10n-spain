# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

import pytz

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    use_connector = fields.Boolean(
        string="Use connector",
        help="Check it to use connector instead of sending the invoice "
        "directly when it's validated",
    )
    send_mode = fields.Selection(
        string="Send mode",
        selection=[
            ("auto", "On validate"),
            ("fixed", "At fixed time"),
            ("delayed", "With delay"),
            ("end_quarter", "At the end of the quarter"),
        ],
        default="auto",
    )
    sent_time = fields.Float(string="Sent time", help="In hours")
    delay_time = fields.Float(string="Delay time", help="In hours")

    def _get_lroe_eta(self):
        if self.send_mode == "fixed":
            tz = self.env.context.get("tz", self.env.user.partner_id.tz)
            offset = datetime.now(pytz.timezone(tz)).strftime("%z") if tz else "+00"
            hour_diff = int(offset[:3])
            hour, minute = divmod(self.sent_time * 60, 60)
            hour = int(hour - hour_diff)
            minute = int(minute)
            now = datetime.now()
            if now.hour > hour or (now.hour == hour and now.minute > minute):
                now += timedelta(days=1)
            now = now.replace(hour=hour, minute=minute)
            return now
        elif self.send_mode == "delayed":
            return datetime.now() + timedelta(seconds=self.delay_time * 3600)
        elif self.send_mode == "end_quarter":
            # El plazo maximo es 25 del mes siguiente a fin de trimestre
            today = datetime.now()
            quarter = int((datetime.now().month - 1) / 3 + 1)
            return datetime(today.year, quarter * 3 + 1, 1) - timedelta(days=1)
        else:
            return None
