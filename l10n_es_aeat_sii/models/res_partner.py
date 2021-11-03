# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sii_enabled = fields.Boolean(compute="_compute_sii_enabled")
    sii_simplified_invoice = fields.Boolean(
        string="Simplified invoices in SII?",
        help="Checking this mark, invoices done to this partner will be "
        "sent to SII as simplified invoices.",
    )
    sii_identification_type = fields.Selection(
        string="SII Identification type",
        help=(
            "Used to specify an identification type to send to SII. Normally for "
            "sending national and export invoices to SII where the customer country "
            "is not Spain, it would calculate an identification type of 04 if the VAT "
            "field is filled and 06 if it was not. This field is to specify "
            "types of 03 through 05, in the event that the customer doesn't identify "
            "with a foreign VAT and instead with their passport "
            "or residential certificate. If there is no value it will work as before."
        ),
        selection=[
            ("03", "Passport"),
            (
                "04",
                "Official identification document issues by the country or "
                "territory of residence",
            ),
            ("05", "Residential certificate"),
        ],
    )

    @api.multi
    def _compute_sii_enabled(self):
        sii_enabled = self.env.user.company_id.sii_enabled
        for partner in self:
            partner.sii_enabled = sii_enabled

    @api.constrains("vat", "country_id", "sii_identification_type")
    def check_vat(self):
        for partner in self:
            if (
                partner.sii_identification_type
                or partner.parent_id.sii_identification_type
            ):
                return True
            super(ResPartner, partner).check_vat()
