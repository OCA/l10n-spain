# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    @api.model
    def _get_selection_sii_exempt_cause(self):
        return self.env["product.template"].fields_get(allfields=["sii_exempt_cause"])[
            "sii_exempt_cause"
        ]["selection"]

    @api.model
    def default_sii_exempt_cause(self):
        default_dict = self.env["product.template"].default_get(["sii_exempt_cause"])
        return default_dict.get("sii_exempt_cause")

    sii_enabled = fields.Boolean(
        related="company_id.sii_enabled",
        readonly=True,
    )
    sii_registration_key_sale = fields.Many2one(
        "aeat.sii.mapping.registration.keys",
        "Default SII Registration Key for Sales",
        domain=[("type", "=", "sale")],
    )
    sii_registration_key_purchase = fields.Many2one(
        "aeat.sii.mapping.registration.keys",
        "Default SII Registration Key for Purchases",
        domain=[("type", "=", "purchase")],
    )
    sii_no_taxable_cause = fields.Selection(
        selection=[
            (
                "ImportePorArticulos7_14_Otros",
                "No sujeta - No sujeción artículo 7, 14, otros",
            ),
            (
                "ImporteTAIReglasLocalizacion",
                "Operaciones no sujetas en el TAI por reglas de localización",
            ),
        ],
        string="SII No taxable cause",
        default="ImporteTAIReglasLocalizacion",
    )
    sii_exempt_cause = fields.Selection(
        string="SII Exempt Cause",
        selection="_get_selection_sii_exempt_cause",
        default=default_sii_exempt_cause,
    )
    sii_partner_identification_type = fields.Selection(
        selection=[("1", "National"), ("2", "Intracom"), ("3", "Export")],
        string="SII partner Identification Type",
    )
