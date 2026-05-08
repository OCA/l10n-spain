# Copyright 2026 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SiiMatchReport(models.Model):
    _inherit = "l10n.es.aeat.sii.match.report"

    def _get_aeat_odoo_invoices_by_csv(self, sii_response):
        # Try to match with PoS orders the remaining invoices by CSV
        matched_invoices, left_invoices = super()._get_aeat_odoo_invoices_by_csv(
            sii_response
        )
        if self.invoice_type == "in":
            return matched_invoices, left_invoices
        left_results = []
        for invoice in left_invoices:
            csv = invoice["DatosPresentacion"]["CSV"]
            odoo_order = self.env["pos.order"].search([("sii_csv", "=", csv)])
            if odoo_order:
                matched_invoices[odoo_order] = invoice
            else:
                left_results.append(invoice)
        return matched_invoices, left_results

    def _get_aeat_odoo_invoices_by_num(self, left_invoices, matched_invoices):
        # Try to match with PoS orders the remaining invoices by number
        matched_invoices, left_invoices = super()._get_aeat_odoo_invoices_by_num(
            left_invoices, matched_invoices
        )
        if self.invoice_type == "in":
            return matched_invoices, left_invoices
        PosOrder = self.env["pos.order"]
        left_results = []
        for invoice in left_invoices:
            name = invoice["IDFactura"]["NumSerieFacturaEmisor"]
            odoo_order = PosOrder.search(
                [
                    ("l10n_es_unique_id", "=", name),
                    ("state", "in", PosOrder._get_valid_document_states()),
                ],
            )
            if odoo_order:
                matched_invoices[odoo_order] = invoice
            else:
                left_results.append(invoice)
        return matched_invoices, left_results

    def _get_not_in_sii_invoices(self, invoices):
        # Add the PoS orders not in SII
        res = super()._get_not_in_sii_invoices(invoices)
        if self.invoice_type == "in":
            return res
        date_start, date_end = self._get_date_interval()
        prev_order_ids = [x.id for x in invoices.keys() if x._name == "pos.order"]
        domain = [
            ("id", "not in", prev_order_ids),
            ("date_order", ">=", date_start),
            ("date_order", "<", date_end),
            ("company_id", "=", self.company_id.id),
            ("sii_enabled", "=", True),
        ]
        for order in self.env["pos.order"].search(domain):
            res.append(order._get_match_report_values(False))
        return res
