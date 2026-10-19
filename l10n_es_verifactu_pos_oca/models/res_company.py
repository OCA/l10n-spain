from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _load_pos_data_fields(self, config_id):
        # Needed on PoS to print the QR code only on the tickets that the
        # backend registers.
        return super()._load_pos_data_fields(config_id) + [
            "verifactu_enabled",
            "verifactu_start_date",
        ]
