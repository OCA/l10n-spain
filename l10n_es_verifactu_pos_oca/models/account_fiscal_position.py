from odoo import api, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    @api.model
    def _load_pos_data_fields(self, config_id):
        # Needed on PoS to keep the QR code out of the tickets whose fiscal
        # position is not declared to the AEAT.
        return super()._load_pos_data_fields(config_id) + ["aeat_active"]
