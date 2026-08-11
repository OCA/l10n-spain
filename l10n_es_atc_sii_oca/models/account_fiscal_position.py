# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    def _get_selection_sii_art25_tipo_bien(self):
        return self.env["product.template"].fields_get(
            allfields=["sii_art25_tipo_bien"]
        )["sii_art25_tipo_bien"]["selection"]

    sii_art25_tipo_bien = fields.Selection(
        string="Tipo de bien Art. 25 (L32)",
        selection="_get_selection_sii_art25_tipo_bien",
        help="Fallback ATC Lista L32 (TipoBienArt25) para exención Art. 25 REF "
        "de bienes de inversión, cuando el producto no tiene tipo asignado.",
    )
