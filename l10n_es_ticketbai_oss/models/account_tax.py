# Copyright 2022 Binovo IT Human Project SL
# Copyright 2024 Avanzosc
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    tbai_tax_map_id = fields.Many2one(
        comodel_name="tbai.tax.map", string="Tbai Tax Map"
    )
    not_subject_to_cause = fields.Selection(
        selection=[
            (
                "OT",
                "OT - No sujeto por el artículo 7 de la Norma Foral de IVA Otros"
                " supuestos de no sujeción.",
            ),
            ("RL", "RL - No sujeto por reglas de localización."),
            (
                "IE",
                "IE - No sujeto en el TAI por reglas de localización, pero repercute"
                " impuesto extranjero, IPS/IGIC o IVA de otro estado miembro UE.",
            ),
        ],
        string="Not Subject to Cause",
    )

    def tbai_is_subject_to_tax(self):
        if self.tbai_tax_map_id and self.tbai_tax_map_id.code in ("SNS", "BNS"):
            return False
        return super().tbai_is_subject_to_tax()

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

    def tbai_es_prestacion_servicios(self):
        if self.tbai_tax_map_id:
            return self.tbai_tax_map_id.code in ("SNS", "SIE", "S", "SER")
        return False

    def tbai_get_value_causa(self, invoice_id):
        if self.not_subject_to_cause:
            return self.not_subject_to_cause
        return super().tbai_get_value_causa(invoice_id)
