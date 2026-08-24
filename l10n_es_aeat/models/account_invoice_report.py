# Copyright 2025 Netkia - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    l10n_es_aeat_real_estate_id = fields.Many2one(
        comodel_name="l10n.es.aeat.real_estate",
        string="Real Estate",
        readonly=True,
    )

    def _select(self):
        return super()._select() + ", line.l10n_es_aeat_real_estate_id"
