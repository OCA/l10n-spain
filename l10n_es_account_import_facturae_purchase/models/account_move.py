# Copyright 2023 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.tests import Form


class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_vals_invoice_from_attachment_facturae_invoice_line(
        self, partner, company, line_data, data
    ):
        vals = super()._prepare_vals_invoice_from_attachment_facturae_invoice_line(
            partner, company, line_data, data
        )
        data.setdefault("transaction_reference", set())
        if vals.get("facturae_receiver_transaction_reference"):
            data["transaction_reference"].add(
                vals.get("facturae_receiver_transaction_reference")
            )
        return vals

    def _purchase_order_facturae_domain(self, purchase_order, vals):
        domain = [
            ("name", "=", purchase_order),
            ("state", "in", ["purchase", "done"]),
            ("invoice_status", "=", "to invoice"),
        ]
        if vals.get("partner_id"):
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
            domain.append(
                (
                    "partner_id.commercial_partner_id",
                    "=",
                    partner.commercial_partner_id.id,
                )
            )
        return domain

    def _prepare_vals_invoice_from_attachment_facturae_invoice(
        self, partner, company, invoice_data
    ):
        (
            vals,
            context,
            data,
        ) = super()._prepare_vals_invoice_from_attachment_facturae_invoice(
            partner, company, invoice_data
        )
        if data.get("transaction_reference"):
            purchases = self.env["purchase.order"]
            for purchase_order in data.get("transaction_reference"):
                new_po = self.env["purchase.order"].search(
                    self._purchase_order_facturae_domain(purchase_order, vals)
                )
                if not new_po:
                    data["messages"].append(
                        _("Purchase Order %s cannot be processed") % purchase_order
                    )
                purchases |= new_po
            data["purchases"] = purchases
            if purchases:
                vals["invoice_line_ids"] = []
        return vals, context, data

    def _check_invoice_facturae(self, data):
        if data.get("purchases") and not self.line_ids:
            with Form(self) as f:
                for purchase_order in data["purchases"]:
                    f.purchase_id = purchase_order
        return super()._check_invoice_facturae(data)
