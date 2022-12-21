# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

import logging
from odoo import models, fields, api, exceptions, _

PRORATE_TAX_LINE_MAPPING = [
    62,  # 639
    191,  # 190
    197,  # 202
    604,  # 603
    606,  # 605
    612,  # 611
    614  # 613
]

_logger = logging.getLogger(__name__)


class L10nEsAeatMod390Report(models.Model):
    _inherit = "l10n.es.aeat.mod390.report"

    prorate_ids = fields.One2many(
        string="Line prorate",
        comodel_name="l10n.es.aeat.mod390.report.line.prorate",
        inverse_name="report_id",
        limit=5
    )
    vat_prorate_type = fields.Selection(
        [
            ("none", "None"),
            ("G", "General prorrate")
        ],
        readonly=True,
        states={"draft": [("readonly", False)]},
        string="VAT prorate type",
        default="none",
        required=True
    )
    vat_prorate_percent = fields.Float(
        string="VAT prorate percentage",
        default=0,
        readonly=True,
        states={"draft": [("readonly", False)]}
    )

    def check_prorate_ids_amount_valid(self):
        for item in self.filtered(lambda x: x.vat_prorate_type != "none"):
            if item.prorate_ids:
                amount = sum(x["amount"] for x in item.prorate_ids)
                if amount == 0:
                    raise exceptions.ValidationError(
                        _("Total amount of the operations cannot be 0")
                    )

    def check_prorate_ids_total_deduction_valid(self):
        for item in self.filtered("prorate_ids"):
            amount = sum(item.mapped("prorate_ids.amount"))
            key = "amount_deductable"
            amount_deduction = sum(item.mapped("prorate_ids." + key))
            if amount_deduction == 0:
                raise exceptions.ValidationError(
                    _(
                        "Total amount of the operations with the "
                        "right to deduction cannot be 0"
                    )
                )
            elif amount_deduction > amount:
                raise exceptions.ValidationError(
                    _(
                        "Total amount of the operations with the "
                        "right to deduct cannot exceed the amount of "
                        "the operations"
                    )
                )

    def button_confirm(self):
        for item in self.filtered(lambda x: x.vat_prorate_type != "none"):
            if not item.prorate_ids:
                raise exceptions.ValidationError(
                    _("Prorrate is needed (almost 1)")
                )
            else:
                item.check_prorate_ids_total_deduction_valid()
                item.check_prorate_ids_amount_valid()
        return super().button_confirm()

    def auto_define_prorrate_ids(self):
        for item in self.filtered(lambda x: x.vat_prorate_type != "none"):
            amount = 0
            amount_deductable = 0
            for tax_line in item.tax_line_ids.filtered(
                lambda x: x.map_line_id.field_number in PRORATE_TAX_LINE_MAPPING
            ):
                amount += tax_line.amount
                reduction = round(tax_line.amount * self.vat_prorate_percent / 100, 2)
                tax_line.amount -= reduction
                amount_deductable += tax_line.amount
            item.prorate_ids = [
                (0, 0, {
                    "activity": "activity",
                    "cnae": "CNAE",
                    "amount": amount,
                    "amount_deductable": amount_deductable,
                    "prorate_type": item.vat_prorate_type,
                    "percent": item.vat_prorate_percent,
                })
            ]

    def button_calculate(self):
        res = super().button_calculate()
        self.auto_define_prorrate_ids()
        return res

    def button_recalculate(self):
        res = super().button_recalculate()
        self.auto_define_prorrate_ids()
        return res

    @api.onchange("vat_prorate_type")
    def _onchange_vat_prorate_types(self):
        if self.vat_prorate_type == "none":
            self.vat_prorate_percent = 0

    @api.constrains("vat_prorate_percent")
    def check_vat_prorate_percent(self):
        for item in self.filtered(lambda x: x.vat_prorate_type != "none"):
            if not (0 < item.vat_prorate_percent <= 100):
                raise exceptions.ValidationError(
                    _("VAT prorrate percent must be between 0.01 and 100")
                )
