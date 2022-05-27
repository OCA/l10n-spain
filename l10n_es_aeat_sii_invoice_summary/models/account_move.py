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
        if self.is_invoice_summary and self.move_type == "out_invoice":
            tipo_factura = "F4"
            if self.sii_invoice_summary_start:
                if self.sii_invoice_summary_start == self.sii_invoice_summary_end:
                    tipo_factura = "F2"
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

        return inv_dict

    def _sii_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices."""
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        partner = self._sii_get_partner()
        country_code = self._get_sii_country_code()
        is_simplified_invoice = self._is_sii_simplified_invoice()

        if is_simplified_invoice and self.move_type[:2] == "in":
            raise exceptions.UserError(
                _("You can't make a supplier simplified invoice.")
            )
        if (
            (gen_type != 3 or country_code == "ES")
            and not partner.vat
            and not is_simplified_invoice
            and not self.is_invoice_summary
        ):
            raise exceptions.UserError(_("The partner has not a VAT configured."))

        if not self.company_id.chart_template_id:
            raise exceptions.UserError(
                _("You have to select what account chart template use this" " company.")
            )
        if not self.company_id.sii_enabled:
            raise exceptions.UserError(_("This company doesn't have SII enabled."))
        if not self.sii_enabled:
            raise exceptions.UserError(_("This invoice is not SII enabled."))
        if not self.ref and self.move_type in ["in_invoice", "in_refund"]:
            raise exceptions.UserError(_("The supplier number invoice is required"))
