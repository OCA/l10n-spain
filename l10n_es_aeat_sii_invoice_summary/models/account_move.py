# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2018 FactorLibre - Victor Rodrigo <victor.rodrigo@factorlibre.com>
# © 2022 ProcessControl - David Ramia <david.ramia@processcontrol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, exceptions, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_invoice_summary = fields.Boolean("Is SII simplified invoice Summary?")
    sii_invoice_summary_start = fields.Char("SII Invoice Summary: First Invoice")
    sii_invoice_summary_end = fields.Char("SII Invoice Summary: Last Invoice")

    def _get_sii_invoice_dict_out(self, cancel=False):
        inv_dict = super(AccountMove, self)._get_sii_invoice_dict_out(cancel=cancel)
        if self.is_invoice_summary and self.move_type in ("out_invoice", "out_refund"):
            tipo_factura = "F4"
            if self.sii_invoice_summary_start:
                if self.sii_invoice_summary_start == self.sii_invoice_summary_end:
                    tipo_factura = "F2" if self.move_type == "out_invoice" else "R5"
                else:
                    inv_dict["IDFactura"][
                        "NumSerieFacturaEmisor"
                    ] = self.sii_invoice_summary_start
                    inv_dict["IDFactura"][
                        "NumSerieFacturaEmisorResumenFin"
                    ] = self.sii_invoice_summary_end
            if "FacturaExpedida" in inv_dict:
                if "TipoFactura" in inv_dict["FacturaExpedida"]:
                    inv_dict["FacturaExpedida"]["TipoFactura"] = tipo_factura
                if "Contraparte" in inv_dict["FacturaExpedida"]:
                    del inv_dict["FacturaExpedida"]["Contraparte"]
                if (
                    "TipoRectificativa" in inv_dict["FacturaExpedida"]
                    and tipo_factura == "F4"
                ):
                    del inv_dict["FacturaExpedida"]["TipoRectificativa"]

        return inv_dict

    def _sii_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices."""
        try:
            super(AccountMove, self)._sii_check_exceptions()
        except exceptions.UserError as e:
            if (
                e.args[0] == _("The partner has not a VAT configured.")
                and self.is_invoice_summary
            ):
                pass
            else:
                raise

        if self.is_invoice_summary and self.move_type[:2] == "in":
            raise exceptions.UserError(_("You can't make a supplier summary invoice."))
