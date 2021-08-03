# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2017 Eficent Business & IT Consult. Services <contact@eficent.com>
# Copyright 2018-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    eu_triangular_deal = fields.Boolean(
        string="EU Triangular deal",
        help="This invoice constitutes a triangular operation for the "
        "purposes of intra-community operations.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )


class AccountMoveLine(models.Model):
    """Inheritance of account move line to add some fields:
    - AEAT_349_operation_key: Operation key of invoice line
    """

    _inherit = "account.move.line"

    l10n_es_aeat_349_operation_key = fields.Selection(
        selection=[
            ("A", "A - Intra-Community acquisition"),
            ("E", "E - Intra-Community supplies"),
            ("I", "I - Intra-Community services acquisitions"),
            ("S", "S - Intra-Community services"),
            ("T", "T - Triangular operations"),
        ],
        string="AEAT 349 Operation key",
        compute="_compute_l10n_es_aeat_349_operation_key",
    )

    @api.depends("tax_ids", "move_id.eu_triangular_deal")
    def _compute_l10n_es_aeat_349_operation_key(self):
        for rec in self:
            if rec.move_id.eu_triangular_deal:
                rec.l10n_es_aeat_349_operation_key = "T"
            else:
                rec.l10n_es_aeat_349_operation_key = False
                for tax in rec.tax_ids:
                    if tax.l10n_es_aeat_349_operation_key:
                        rec.l10n_es_aeat_349_operation_key = (
                            tax.l10n_es_aeat_349_operation_key
                        )
                        break
