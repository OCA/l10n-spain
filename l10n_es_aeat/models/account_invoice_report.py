# Copyright 2025 Netkia - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    l10n_es_aeat_real_estate_id = fields.Many2one(
        comodel_name="l10n.es.aeat.real_estate",
        string="Real Estate",
        readonly=True,
    )

    def _select(self) -> SQL:
        return SQL(
            "%s, line.l10n_es_aeat_real_estate_id",
            super()._select(),
        )
