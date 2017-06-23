# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def get_qty_delivered(self):
        return sum(
            [order_line.qty_delivered for order_line in self.sale_line_ids])

    def get_datetime(self, date):
        return datetime.strptime(date, DATETIME_FORMAT)
