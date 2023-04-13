# Copyright 2023 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import mimetypes

from lxml import etree

from odoo import _, api, fields, models
from odoo.tools import float_compare
from odoo.tools.misc import format_amount

mimetypes.add_type("application/xml", ".xsig")


class AccountMove(models.Model):

    _inherit = "account.move"

    facturae_received = fields.Boolean()

    @api.depends("facturae_received")
    def _compute_facturae(self):
        super()._compute_facturae()
        for record in self.filtered(lambda r: r.facturae_received):
            record.facturae = True

    def _get_create_invoice_from_attachment_decoders(self):
        res = super()._get_create_invoice_from_attachment_decoders()
        res.append(
            (
                9,
                self._create_invoice_from_attachment_facturae,
            )
        )
        return res

    def _get_update_invoice_from_attachment_decoders(self, invoice):
        res = super()._get_update_invoice_from_attachment_decoders(invoice)
        res.append(
            (
                9,
                self._update_invoice_from_attachment_facturae,
            )
        )
        return res

    def _process_facturae(self, attachment):
        content = base64.b64decode(attachment.with_context(bin_size=False).datas)
        is_text_plain_xml = attachment.mimetype == "application/xml" or (
            ("text/plain" in attachment.mimetype) and content.startswith(b"<?xml")
        )
        if not is_text_plain_xml:
            return None
        data = etree.fromstring(content)
        if data.tag not in [
            "{http://www.facturae.es/Facturae/2009/v3.2/Facturae}Facturae",
            "{http://www.facturae.es/Facturae/2014/v3.2.1/Facturae}Facturae",
            "{http://www.facturae.gob.es/formato/Versiones/Facturaev3_2_2.xml}Facturae",
        ]:
            return None
        return data

    def _prepare_vals_invoice_from_attachment_facturae(self, facturae_data):
        parties = facturae_data.find("Parties")
        seller_vat = (
            parties.find("SellerParty")
            .find("TaxIdentification")
            .find("TaxIdentificationNumber")
            .text
        )
        partner = self.env["res.partner"].search([("vat", "like", seller_vat)], limit=1)
        buyer_vat = (
            parties.find("BuyerParty")
            .find("TaxIdentification")
            .find("TaxIdentificationNumber")
            .text
        )
        company = self.env["res.company"].search([("vat", "like", buyer_vat)], limit=1)
        result = []
        for invoice_data in facturae_data.find("Invoices").findall("Invoice"):
            result.append(
                self._prepare_vals_invoice_from_attachment_facturae_invoice(
                    partner, company, invoice_data
                )
            )
        return result, company.id

    def _prepare_vals_invoice_from_attachment_facturae_invoice(
        self, partner, company, invoice_data
    ):
        context = {}
        data = {
            "amount_untaxed": float(
                invoice_data.find("InvoiceTotals")
                .find("TotalGrossAmountBeforeTaxes")
                .text
            ),
            "amount_total": float(
                invoice_data.find("InvoiceTotals").find("InvoiceTotal").text
            ),
            "messages": [],
            "attachments": [],
        }
        vals = {
            "facturae_received": True,
            "partner_id": partner.id,
            "ref": invoice_data.find("InvoiceHeader").find("InvoiceNumber").text,
            "payment_reference": invoice_data.find("InvoiceHeader")
            .find("InvoiceNumber")
            .text,
            "invoice_date": fields.Date.from_string(
                invoice_data.find("InvoiceIssueData").find("IssueDate").text
            ),
            "currency_id": self.env["res.currency"]
            .search(
                [
                    (
                        "name",
                        "=",
                        invoice_data.find("InvoiceIssueData")
                        .find("InvoiceCurrencyCode")
                        .text,
                    )
                ],
                limit=1,
            )
            .id,
        }
        if invoice_data.find("PaymentDetails") is not None:
            vals["invoice_date_due"] = fields.Date.from_string(
                invoice_data.find("PaymentDetails")
                .find("Installment")
                .find("InstallmentDueDate")
                .text
            )
        context["default_move_type"] = "in_invoice"
        if invoice_data.find("InvoiceHeader").find("InvoiceDocumentType").text in [
            "OR",
            "CR",
        ]:
            context["default_move_type"] = "in_refund"
        lines = []
        for line_data in invoice_data.find("Items").findall("InvoiceLine"):
            lines.append(
                (
                    0,
                    0,
                    self._prepare_vals_invoice_from_attachment_facturae_invoice_line(
                        partner, company, line_data, data
                    ),
                )
            )
        vals["invoice_line_ids"] = lines
        if (
            invoice_data.find("AdditionalData") is not None
            and invoice_data.find("AdditionalData").find("RelatedDocuments") is not None
        ):
            for attachment in (
                invoice_data.find("AdditionalData")
                .find("RelatedDocuments")
                .findall("Attachment")
            ):
                self._prepare_import_attachment_facturae(attachment, data)
        return vals, context, data

    def _prepare_import_attachment_facturae(self, attachment, data):
        algorithm = "NONE"
        if attachment.find("AttachmentCompressionAlgorithm") is not None:
            algorithm = attachment.find("AttachmentCompressionAlgorithm").text
        if algorithm != "NONE":
            return
        file_data = attachment.find("AttachmentData").text
        name = "attachment"
        if attachment.find("AttachmentDescription") is not None:
            name = attachment.find("AttachmentDescription").text
        name += "." + attachment.find("AttachmentFormat").text
        encoding = False
        if attachment.find("AttachmentEncoding") is not None:
            encoding = attachment.find("AttachmentEncoding").text
        if encoding == "BASE64":
            file_data = base64.b64decode(file_data)
        data["attachments"].append((name, file_data))

    def _prepare_from_attachment_facturae_invoice_line_tax(
        self, partner, company, tax, with_held=False
    ):
        rate = float(tax.find("TaxRate").text)
        if with_held:
            rate = -rate
        taxes = self.env["account.tax"].search(
            [
                ("facturae_code", "=", tax.find("TaxTypeCode").text),
                ("amount", "=", rate),
                ("company_id", "=", company.id),
            ]
        )
        if len(taxes) < 2:
            return taxes.id
        lines = self.env["account.move.line"].search(
            [
                ("partner_id", "=", partner.id),
                ("company_id", "=", company.id),
                ("parent_state", "=", "posted"),
                ("tax_line_id", "in", taxes.ids),
            ],
            limit=1,
            order="date DESC",
        )
        if lines:
            return lines.tax_line_id.id
        return taxes[0].id

    def _prepare_vals_invoice_from_attachment_facturae_invoice_line(
        self, partner, company, line_data, data
    ):
        price_unit = float(line_data.find("UnitPriceWithoutTax").text)
        if line_data.find("DiscountsAndRebates") is not None:
            for discount in line_data.find("DiscountsAndRebates").findall("Discount"):
                price_unit += float(discount.find("DiscountAmount"))
        if line_data.find("Charges") is not None:
            for discount in line_data.find("Charges").findall("Charge"):
                price_unit += float(discount.find("ChargeAmount"))
        taxes = []
        for tax_node in line_data.find("TaxesOutputs").findall("Tax"):
            tax = self._prepare_from_attachment_facturae_invoice_line_tax(
                partner, company, tax_node
            )
            if tax:
                taxes.append((4, tax))
        if line_data.find("TaxesWithheld"):
            for tax_node in line_data.find("TaxesWithheld").findall("Tax"):
                tax = self._prepare_from_attachment_facturae_invoice_line_tax(
                    partner, company, tax_node, with_held=True
                )
                if tax:
                    taxes.append((4, tax))
        vals = {
            "name": line_data.find("ItemDescription").text,
            "quantity": float(line_data.find("Quantity").text),
            "price_unit": price_unit,
            "tax_ids": taxes,
        }
        for key, value in [
            ("facturae_issuer_contract_reference", "IssuerContractReference"),
            ("facturae_issuer_transaction_reference", "IssuerTransactionReference"),
            ("facturae_receiver_contract_reference", "ReceiverContractReference"),
            ("facturae_receiver_transaction_reference", "ReceiverTransactionReference"),
            ("facturae_file_reference", "FileReference"),
            ("facturae_issuer_contract_date", "IssuerContractDate"),
            ("facturae_issuer_transaction_date", "IssuerTransactionDate"),
            ("facturae_receiver_contract_date", "ReceiverContractDate"),
            ("facturae_receiver_transaction_date", "ReceiverTransactionDate"),
            ("facturae_file_date", "FileDate"),
        ]:
            node = line_data.find(value)
            if node is not None:
                vals[key] = node.text
        return vals

    def _create_invoice_from_attachment_facturae(self, attachment):
        facturae_data = self._process_facturae(attachment)
        if facturae_data is None:
            return self.env["account.move"]
        (
            invoice_vals,
            company_id,
        ) = self._prepare_vals_invoice_from_attachment_facturae(facturae_data)
        invoice = self.env["account.move"]
        for vals, context, data in invoice_vals:
            invoice |= (
                self.with_company(company_id or self.env.company.id)
                .with_context(**context)
                ._create_invoice_facturae(vals, data)
            )
        return invoice

    def _create_invoice_facturae(self, vals, data):
        move = False
        if vals.get("partner_id") and data.get("amount_total"):
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
            move = self.search(
                [
                    (
                        "partner_id.commercial_partner_id",
                        "=",
                        partner.commercial_partner_id.id,
                    ),
                    ("amount_total", "=", data.get("amount_total")),
                    ("ref", "=", False),
                    ("state", "=", "draft"),
                ],
                limit=1,
            )
        if move:
            return move._update_invoice_facturae(vals, data)
        move = self.create(vals)
        messages = move._check_invoice_facturae(data)
        if messages or data["attachments"]:
            move.message_post(
                body="<br/>".join(messages), attachments=data["attachments"]
            )
        return move

    def _update_invoice_facturae_vals(self, vals, data):
        new_vals = {
            "ref": vals.get("ref"),
            "payment_reference": vals.get("payment_reference"),
            "invoice_date": vals.get("invoice_date"),
            "invoice_date_due": vals.get("invoice_date_due"),
            "facturae_received": vals.get("facturae_received"),
        }
        if not self.partner_id:
            new_vals["partner_id"] = vals.get("partner_id")
        if not self.invoice_line_ids:
            new_vals["invoice_line_ids"] = vals.get("invoice_line_ids", [])
        return new_vals

    def _update_invoice_facturae(self, vals, data):
        self.write(self._update_invoice_facturae_vals(vals, data))
        messages = self._check_invoice_facturae(data)
        if messages or data["attachments"]:
            self.message_post(
                body="<br/>".join(messages),
                attachments=data["attachments"],
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )
        return self

    def _check_invoice_facturae(self, data):
        messages = data.get("messages") or []
        for field in ["amount_total", "amount_untaxed"]:
            if (
                float_compare(
                    data[field],
                    self[field],
                    precision_rounding=self.currency_id.rounding,
                )
                != 0
            ):
                messages.append(
                    _("%s is not coincident (%s - %s)")
                    % (
                        self._fields[field].string,
                        format_amount(self.env, data[field], self.currency_id),
                        format_amount(self.env, self[field], self.currency_id),
                    )
                )
        return messages

    def _update_invoice_from_attachment_facturae(self, attachment, invoice):
        facturae_data = self._process_facturae(attachment)
        if facturae_data is None:
            return self.env["account.move"]
        (
            invoice_vals,
            company_id,
        ) = self._prepare_vals_invoice_from_attachment_facturae(facturae_data)
        if len(invoice_vals) != 1:
            return self.env["account.move"]
        vals, context, data = invoice_vals[0]
        return (
            invoice.with_company(company_id or self.env.company.id)
            .with_context(**context)
            ._update_invoice_facturae(vals, data)
        )
