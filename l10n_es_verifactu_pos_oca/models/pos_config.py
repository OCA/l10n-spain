from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    verifactu_base_url = fields.Char(
        string="Verifactu Base URL",
        compute="_compute_verifactu_base_url",
        store=True,
        help="Base URL for Verifactu QR code generation. Needed on PoS.",
    )

    @api.depends("company_id.verifactu_test")
    def _compute_verifactu_base_url(self):
        for record in self:
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
            record.verifactu_base_url = (
                agency.verifactu_qr_base_url_test_address
                if record.company_id.verifactu_test
                else agency.verifactu_qr_base_url
            )
