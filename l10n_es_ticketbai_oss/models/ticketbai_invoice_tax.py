# Copyright 2022 Landoo Sistemas de Informacion SL
from odoo import fields, models

from odoo.addons.l10n_es_ticketbai_api.utils import utils as tbai_utils


class VATRegimeKey(tbai_utils.EnumValues):
    K17 = "17"


class NotSubjectToCause(tbai_utils.EnumValues):
    IE = "IE"


class TicketBaiTax(models.Model):
    _inherit = "tbai.invoice.tax"

    not_subject_to_cause = fields.Selection(
        selection_add=[
            (NotSubjectToCause.IE.value, "IE"),
        ],
        help="""
        OT:
          - No sujeto por el artículo 7 de la Norma Foral de IVA Otros supuestos de no
          sujeción.
        RL:
          - No sujeto por reglas de localización.
        IE:
          - No sujeto en el TAI por reglas de localización, pero repercute"
          impuesto extranjero, IPS/IGIC o IVA de otro estado miembro UE.
        """,
    )


class AccountTax(models.Model):
    _inherit = "account.tax"

    def tbai_is_subject_to_tax(self):
        return super(AccountTax, self).tbai_is_subject_to_tax() and (
            self
            not in self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        )

    def tbai_es_entrega(self):
        return super(AccountTax, self).tbai_es_entrega() or (
            self
            in self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        )

    def tbai_get_value_causa(self, invoice_id):
        res = super().tbai_get_value_causa(invoice_id)
        if invoice_id.fiscal_position_id.oss_oca:
            res = NotSubjectToCause.IE.value
        return res
