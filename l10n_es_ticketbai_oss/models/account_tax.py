# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    tbai_tax_map_id = fields.Many2one(
        comodel_name="tbai.tax.map", string="Tbai Tax Map"
    )
    not_subject_to_cause = fields.Selection(
        selection=[
            ("OT", "OT - No sujeto por el artículo 7 de la Norma Foral de IVA Otros"
                   " supuestos de no sujeción. "),
            ("RL", "RL - No sujeto por reglas de localización."),
            ("IE", "IE - No sujeto en el TAI por reglas de localización, pero repercute"
                   " impuesto extranjero, IPS/IGIC o IVA de otro estado miembro UE."),
        ],
        string="Not Subject to Cause",
    )

    def tbai_is_subject_to_tax(self):
        if self.tbai_tax_map_id and self.tbai_tax_map_id.code in ("SNS", "BNS"):
            return False
        return super().tbai_is_subject_to_tax()
