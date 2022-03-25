# Copyright 2017 Creu Blanca
# Copyright 2020 NuoBiT Solutions - Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def get_datetime(self, dt):
        return fields.Datetime.context_timestamp(self, dt)
