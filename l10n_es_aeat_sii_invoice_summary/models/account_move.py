# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2018 FactorLibre - Victor Rodrigo <victor.rodrigo@factorlibre.com>
# © 2022 ProcessControl - David Ramia <david.ramia@processcontrol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, exceptions, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_invoice_summary = fields.Boolean("Is SII simplified invoice Summary?")
    sii_invoice_summary_start = fields.Char("SII Invoice Summary: First Invoice")
    sii_invoice_summary_end = fields.Char("SII Invoice Summary: Last Invoice")

    def _get_invoice_summary_type(self):
        """Invoice type of a summary of simplified invoices: F4 for a range of
        them, F2 when it covers a single one and R5 for a summary of their
        credit notes, which the AEAT does not accept as a range."""
        self.ensure_one()
        if not self.is_invoice_summary or not self.is_sale_document():
            return False
        if self.move_type == "out_refund":
            return "R5"
        if (
            self.sii_invoice_summary_start
            and self.sii_invoice_summary_start != self.sii_invoice_summary_end
        ):
            return "F4"
        return "F2"

    @api.depends(
        "is_invoice_summary", "sii_invoice_summary_start", "sii_invoice_summary_end"
    )
    def _compute_l10n_es_invoice_type(self):
        previous = {move: move.l10n_es_invoice_type for move in self}
        res = super()._compute_l10n_es_invoice_type()
        for move in self:
            if (move.state == "posted" and previous[move]) or (
                move.country_code != "ES"
            ):
                continue
            invoice_type = move._get_invoice_summary_type()
            if invoice_type:
                move.l10n_es_invoice_type = invoice_type
        return res

    def _post(self, soft=True):
        # The type given on creation (e.g. by an importer) is not computed again
        for move in self.filtered(lambda move: move.country_code == "ES"):
            invoice_type = move._get_invoice_summary_type()
            if invoice_type and move.l10n_es_invoice_type != invoice_type:
                move.l10n_es_invoice_type = invoice_type
        return super()._post(soft=soft)

    def _get_aeat_invoice_dict_out(self, cancel=False):
        """An F4 is identified by its range, also when it is cancelled."""
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if self.l10n_es_invoice_type == "F4":
            inv_dict["IDFactura"]["NumSerieFacturaEmisor"] = (
                self.sii_invoice_summary_start
            )
            inv_dict["IDFactura"]["NumSerieFacturaEmisorResumenFin"] = (
                self.sii_invoice_summary_end
            )
            exp_dict = inv_dict.get("FacturaExpedida", {})
            exp_dict.pop("TipoRectificativa", None)
            exp_dict.pop("ImporteRectificacion", None)
        return inv_dict

    def _aeat_check_exceptions(self):
        res = super()._aeat_check_exceptions()
        if self.is_invoice_summary and self.is_purchase_document():
            raise exceptions.UserError(
                self.env._("You can't make a supplier summary invoice.")
            )
        if self.l10n_es_invoice_type == "F4" and not (
            self.is_invoice_summary
            and self.sii_invoice_summary_start
            and self.sii_invoice_summary_start != self.sii_invoice_summary_end
        ):
            raise exceptions.UserError(
                self.env._(
                    "A summary invoice (F4) needs the first and the last invoice "
                    "of the range it summarizes."
                )
            )
        return res

    def write(self, vals):
        """Cannot let change sii_invoice_summary fields
        values in a SII registered supplier invoice"""
        for invoice in self.filtered(
            lambda x: x.is_invoice_summary and x.aeat_state != "not_sent"
        ):
            if "sii_invoice_summary_start" in vals:
                invoice._raise_exception_sii(
                    self.env._("SII Invoice Summary: First Invoice")
                )
            if "sii_invoice_summary_end" in vals:
                invoice._raise_exception_sii(
                    self.env._("SII Invoice Summary: Last Invoice")
                )
        return super().write(vals)
