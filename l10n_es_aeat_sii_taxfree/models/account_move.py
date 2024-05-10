# © 2019 - FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if self.fiscal_position_id.sii_refund_as_regular:
            if inv_dict["FacturaExpedida"].get("TipoRectificativa", False):
                del inv_dict["FacturaExpedida"]["TipoRectificativa"]
            inv_dict["FacturaExpedida"]["TipoFactura"] = (
                "F2"
                if self.partner_id.commercial_partner_id.aeat_simplified_invoice
                else "F1"
            )
            del inv_dict["FacturaExpedida"]["ImporteTotal"]
        return inv_dict
