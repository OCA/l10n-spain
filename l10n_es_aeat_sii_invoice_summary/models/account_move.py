# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2018 FactorLibre - Victor Rodrigo <victor.rodrigo@factorlibre.com>
# © 2022 ProcessControl - David Ramia <david.ramia@processcontrol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, exceptions, fields, models

# Limit of a summary of received invoices (art. 64.5 RD 1624/1992), untaxed
RECEIVED_SUMMARY_LIMIT = 6000


class AccountMove(models.Model):
    _inherit = "account.move"

    is_invoice_summary = fields.Boolean("Is SII simplified invoice Summary?")
    sii_invoice_summary_start = fields.Char("SII Invoice Summary: First Invoice")
    sii_invoice_summary_end = fields.Char("SII Invoice Summary: Last Invoice")

    def _get_invoice_summary_type(self):
        """Invoice type of a summary of simplified invoices: F4 for a range of
        them, F2 when it covers a single one and R5 for a summary of their
        credit notes, which the AEAT does not accept as a range. A summary of
        invoices received from a supplier (art. 64.5 RD 1624/1992) is an F4
        when it covers a range, and keeps its own type otherwise."""
        self.ensure_one()
        if not self.is_invoice_summary or self.move_type not in (
            "out_invoice",
            "out_refund",
            "in_invoice",
        ):
            return False
        if self.move_type == "out_refund":
            return "R5"
        if (
            self.sii_invoice_summary_start
            and self.sii_invoice_summary_start != self.sii_invoice_summary_end
        ):
            return "F4"
        return "F2" if self.move_type == "out_invoice" else False

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

    def _get_aeat_invoice_dict_in(self, cancel=False):
        """A summary of received invoices is identified by the range of the
        supplier's invoice numbers, also when it is cancelled."""
        inv_dict = super()._get_aeat_invoice_dict_in(cancel=cancel)
        if self.l10n_es_invoice_type == "F4":
            inv_dict["IDFactura"]["NumSerieFacturaEmisor"] = (
                self.sii_invoice_summary_start
            )
            inv_dict["IDFactura"]["NumSerieFacturaEmisorResumenFin"] = (
                self.sii_invoice_summary_end
            )
        return inv_dict

    def _aeat_check_exceptions(self):
        res = super()._aeat_check_exceptions()
        if self.is_invoice_summary and self.move_type == "in_refund":
            raise exceptions.UserError(
                self.env._("A supplier credit note can't be a summary invoice.")
            )
        if (
            self.l10n_es_invoice_type == "F4"
            and self.is_purchase_document()
            and self.company_currency_id.compare_amounts(
                abs(self.amount_untaxed_signed), RECEIVED_SUMMARY_LIMIT
            )
            > 0
        ):
            raise exceptions.UserError(
                self.env._(
                    "A summary of received invoices (art. 64.5 RD 1624/1992) "
                    "cannot exceed %(limit)s euros without VAT.",
                    limit=RECEIVED_SUMMARY_LIMIT,
                )
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
