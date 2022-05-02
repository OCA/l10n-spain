# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models

from ..utils import utils as tbai_utils


class VATRegimeKey(tbai_utils.EnumValues):
    K01 = "01"
    K02 = "02"
    K03 = "03"
    K04 = "04"
    K05 = "05"
    K06 = "06"
    K07 = "07"
    K08 = "08"
    K09 = "09"
    K10 = "10"
    K11 = "11"
    K12 = "12"
    K13 = "13"
    K14 = "14"
    K15 = "15"
    K51 = "51"
    K52 = "52"
    K53 = "53"


class NotSubjectToCause(tbai_utils.EnumValues):
    OT = "OT"
    RL = "RL"


class ExemptedCause(tbai_utils.EnumValues):
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"


class NotExemptedType(tbai_utils.EnumValues):
    S1 = "S1"
    S2 = "S2"


class SurchargeOrSimplifiedRegimeType(tbai_utils.EnumValues):
    S = "S"
    N = "N"


class TicketBaiTaxType(tbai_utils.EnumValues):
    service = "service"
    provision_of_goods = "goods"


class TicketBaiTax(models.Model):
    _name = "tbai.invoice.tax"
    _description = "TicketBAI Invoice taxes"

    tbai_invoice_id = fields.Many2one(
        comodel_name="tbai.invoice", required=True, ondelete="cascade"
    )
    base = fields.Char(
        default="", help="String of float with 12 digits and 3 decimal points."
    )
    is_subject_to = fields.Boolean("Is Subject to")
    not_subject_to_cause = fields.Selection(
        selection=[
            (NotSubjectToCause.OT.value, "OT"),
            (NotSubjectToCause.RL.value, "RL"),
        ],
        string="Not Subject to Cause",
        help="""
    OT:
      - No sujeto por el artículo 7 de la Norma Foral de IVA Otros supuestos de no
      sujeción.
    RL:
      - No sujeto por reglas de localización.
    """,
    )
    is_exempted = fields.Boolean()
    exempted_cause = fields.Selection(
        selection=[
            (ExemptedCause.E1.value, "E1"),
            (ExemptedCause.E2.value, "E2"),
            (ExemptedCause.E3.value, "E3"),
            (ExemptedCause.E4.value, "E4"),
            (ExemptedCause.E5.value, "E5"),
            (ExemptedCause.E6.value, "E6"),
        ],
        help="""
    E1: Exenta por el artículo 20 de la Norma Foral del IVA.
    E2: Exenta por el artículo 21 de la Norma Foral del IVA.
    E3: Exenta por el artículo 22 de la Norma Foral del IVA.
    E4: Exenta por el artículo 23 y 24 de la Norma Foral del IVA.
    E5: Exenta por el artículo 25 de la Norma Foral del IVA.
    E6: Exenta por otra causa.
    """,
    )
    not_exempted_type = fields.Selection(
        selection=[(NotExemptedType.S1.value, "S1"), (NotExemptedType.S2.value, "S2")],
        help="""
    S1: Sin inversión del sujeto pasivo.
    S2: Con inversión del sujeto pasivo.
    """,
    )
    amount = fields.Char(
        "Amount (%)",
        default="",
        help="String of float with 3 digits and 2 decimal points.",
    )
    amount_total = fields.Char(
        default="",
        help="String of float with 12 digits and 2 decimal points.",
    )
    re_amount = fields.Char(
        "Surcharge Amount (%)",
        default="",
        help="String of float with 3 digits and 2 decimal points.",
    )
    re_amount_total = fields.Char(
        "Surcharge Amount Total",
        default="",
        help="String of float with 12 digits and 2 decimal points.",
    )
    surcharge_or_simplified_regime = fields.Selection(
        selection=[
            (SurchargeOrSimplifiedRegimeType.N.value, "N"),
            (SurchargeOrSimplifiedRegimeType.S.value, "S"),
        ],
        string="Surcharge or Simplified Regime",
        default=SurchargeOrSimplifiedRegimeType.N.value,
    )
    type = fields.Selection(
        selection=[
            (TicketBaiTaxType.service.value, "Service"),
            (TicketBaiTaxType.provision_of_goods.value, "Provision of goods"),
        ]
    )

    @api.constrains("base")
    def _check_base(self):
        for record in self:
            if record.is_subject_to:
                tbai_utils.check_str_decimal(
                    _("TicketBAI Invoice %s: Tax Base") % record.tbai_invoice_id.name,
                    record.base,
                )

    @api.constrains("not_subject_to_cause")
    def _check_not_subject_to_cause(self):
        for record in self:
            if not record.is_subject_to and not record.not_subject_to_cause:
                raise exceptions.ValidationError(
                    _("TicketBAI Invoice %s: Tax Not subject to cause is required.")
                    % record.tbai_invoice_id.name
                )

    @api.constrains("is_exempted")
    def _check_is_exempted(self):
        for record in self:
            if record.is_exempted and not record.is_subject_to:
                raise exceptions.ValidationError(
                    _("TicketBAI Invoice %s: Exempted taxes are Subject to taxes.")
                    % record.tbai_invoice_id.name
                )

    @api.constrains("exempted_cause")
    def _check_exempted_cause(self):
        for record in self:
            if (
                record.is_subject_to
                and record.is_exempted
                and not record.exempted_cause
            ):
                raise exceptions.ValidationError(
                    _("TicketBAI Invoice %s: Tax Exempted cause is required.")
                    % record.tbai_invoice_id.name
                )

    @api.constrains("not_exempted_type")
    def _check_not_exempted_type(self):
        for record in self:
            if (
                record.is_subject_to
                and not record.is_exempted
                and not record.not_exempted_type
            ):
                raise exceptions.ValidationError(
                    _("TicketBAI Invoice %s: Tax Not exempted type is required.")
                    % record.tbai_invoice_id.name
                )

    @api.constrains("amount")
    def _check_amount(self):
        for record in self:
            if record.is_subject_to and not record.is_exempted and record.amount:
                tbai_utils.check_str_percentage(
                    _("TicketBAI Invoice %s: Tax Amount (%%)")
                    % record.tbai_invoice_id.name,
                    record.amount,
                )

    @api.constrains("amount_total")
    def _check_amount_total(self):
        for record in self:
            if not record.is_subject_to or (
                not record.is_exempted and record.amount_total
            ):
                tbai_utils.check_str_decimal(
                    _("TicketBAI Invoice %s: Tax Amount Total")
                    % record.tbai_invoice_id.name,
                    record.amount_total,
                )

    @api.constrains("re_amount")
    def _check_re_amount(self):
        for record in self:
            if (
                record.is_subject_to
                and not record.is_exempted
                and record.surcharge_or_simplified_regime
                == SurchargeOrSimplifiedRegimeType.S.value
                and record.re_amount
            ):
                tbai_utils.check_str_percentage(
                    _("TicketBAI Invoice %s: Tax Surcharge Amount (%%)")
                    % record.tbai_invoice_id.name,
                    record.re_amount,
                )

    @api.constrains("re_amount_total")
    def _check_re_amount_total(self):
        for record in self:
            if (
                record.is_subject_to
                and not record.is_exempted
                and record.surcharge_or_simplified_regime
                == SurchargeOrSimplifiedRegimeType.S.value
                and record.re_amount_total
            ):
                tbai_utils.check_str_decimal(
                    _("TicketBAI Invoice %s: Tax Surcharge Amount Total")
                    % record.tbai_invoice_id.name,
                    record.re_amount_total,
                )

    @api.constrains("surcharge_or_simplified_regime")
    def _check_surcharge_or_simplified_regime(self):
        for record in self:
            if (
                record.is_subject_to
                and not record.is_exempted
                and record.re_amount
                and record.re_amount_total
                and (
                    not record.surcharge_or_simplified_regime
                    or record.surcharge_or_simplified_regime
                    != SurchargeOrSimplifiedRegimeType.S.value
                )
            ):
                raise exceptions.ValidationError(
                    _(
                        "TicketBAI Invoice %(name)s:\n"
                        "Tax Surcharge or Simplified Regime value should be "
                        "'%(val)s'."
                    )
                    % {
                        "name": record.tbai_invoice_id.name,
                        "val": SurchargeOrSimplifiedRegimeType.S.value,
                    }
                )
