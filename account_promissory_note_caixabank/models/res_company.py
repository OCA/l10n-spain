# Copyright 2022 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

REPORTS_DEFINED = [
    (
        "account_promissory_note_caixabank.action_report_promissory_footer_cb",
        "Promissory note CaixaBank",
    ),
]
REPORTS_DEFINED_ONDELETE = {r[0]: "set default" for r in REPORTS_DEFINED}


class ResCompany(models.Model):
    _inherit = "res.company"

    account_check_printing_layout = fields.Selection(
        selection_add=REPORTS_DEFINED, ondelete=REPORTS_DEFINED_ONDELETE
    )
