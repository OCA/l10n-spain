# Copyright 2022 Moduon - Eduardo de Miguel
# Copyright 2025 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    thirdparty_invoice = fields.Boolean(
        string="Third-party invoice",
        copy=False,
    )
    # You can define distinct agencies in some journals.
    # For example, a company can send invoices to AEAT SII platform and send it to
    # ATC SII (Canary Islands) too. So user can make the invoices in different journals
    # to send it.
    tax_agency_id = fields.Many2one(
        comodel_name="aeat.tax.agency",
        string="Tax Agency",
        copy=False,
        help="You can select a tax agency other than the one defined in the company,"
        "so you can pay taxes at different agencies.",
    )
