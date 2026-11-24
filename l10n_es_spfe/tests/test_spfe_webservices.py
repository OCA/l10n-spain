# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tools import mute_logger

from .common import SpfeTestCommon

SAMPLE_SEND_OK_DS = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b"<DocumentStatus xmlns="
    b'"urn:oasis:names:specification:ubl:schema:xsd:DocumentStatus-2"\n'
    b"    xmlns:cac="
    b'"urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"\n'
    b"    xmlns:cbc="
    b'"urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">\n'
    b"    <cbc:ID>A-SPFETEST0001</cbc:ID>\n"
    b"    <cbc:IssueDate>2026-10-20</cbc:IssueDate>\n"
    b"    <cac:DocumentResponse>\n"
    b"        <cac:Response>\n"
    b"            <cbc:ResponseCode>200</cbc:ResponseCode>\n"
    b"            <cbc:Description>Todas las facturas correctas</cbc:Description>\n"
    b"        </cac:Response>\n"
    b"        <cac:DocumentReference>\n"
    b"            <cbc:ID>%(inv_name)s</cbc:ID>\n"
    b"            <cbc:IssueDate>2026-10-20</cbc:IssueDate>\n"
    b"            <cbc:ReferencedDocumentInternalAddress>"
    b"LOCGENV1:O:TESTLOCATOR123=="
    b"</cbc:ReferencedDocumentInternalAddress>\n"
    b"            <cbc:DocumentStatusCode>200</cbc:DocumentStatusCode>\n"
    b"            <cbc:DocumentDescription>Factura Ok</cbc:DocumentDescription>\n"
    b"            <cac:IssuerParty>\n"
    b"                <cac:PartyTaxScheme>\n"
    b"                    <cbc:CompanyID>B12345674</cbc:CompanyID>\n"
    b"                    <cac:TaxScheme/>\n"
    b"                </cac:PartyTaxScheme>\n"
    b"            </cac:IssuerParty>\n"
    b"        </cac:DocumentReference>\n"
    b"    </cac:DocumentResponse>\n"
    b"</DocumentStatus>"
)


def _build_mock_multipart_response(inner_xml_bytes, cid="respuesta0.xml"):
    return _build_mock_multipart_response_multi([(cid, inner_xml_bytes)])


def _build_mock_multipart_response_multi(parts):
    boundary = "mock_spfe_boundary"
    soap = (
        b'<soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope">'
        b"<soapenv:Header/><soapenv:Body/></soapenv:Envelope>"
    )
    chunks = [
        (
            f"--{boundary}\r\n"
            f"Content-Type: application/soap+xml; charset=UTF-8\r\n"
            f"Content-ID: <root@aeat>\r\n\r\n"
        ).encode(),
        soap,
    ]
    for cid, xml_bytes in parts:
        chunks.extend(
            [
                (
                    f"\r\n--{boundary}\r\n"
                    f"Content-Type: application/xml; charset=UTF-8\r\n"
                    f"Content-ID: <{cid}>\r\n\r\n"
                ).encode(),
                xml_bytes,
            ]
        )
    chunks.append(f"\r\n--{boundary}--\r\n".encode())
    headers = {
        "Content-Type": (
            f'multipart/related; type="application/soap+xml"; boundary="{boundary}"'
        )
    }
    return 200, headers, b"".join(chunks)


class TestSpfeWebservices(SpfeTestCommon):
    def test_01_pre_validation_send_events_and_cancel(self):
        """Lifecycle: PRE validate -> SendInvoice -> SETTLEMENT -> Cancel."""
        inv = self._create_spfe_invoice()
        inv.action_post()

        ds_xml = SAMPLE_SEND_OK_DS % {b"inv_name": inv.name.encode()}
        ds_body = ds_xml.split(b"?>", 1)[-1].strip()
        soap_val_resp = (
            b'<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">'
            b"<env:Header/><env:Body>" + ds_body + b"</env:Body></env:Envelope>"
        )
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=(
                200,
                {"Content-Type": "application/soap+xml"},
                soap_val_resp,
            ),
        ):
            inv.action_spfe_validate_pre()
        self.assertEqual(inv.spfe_state, "validated_pre")

        # SendInvoiceSOAP (ebMS 3.0 multipart)
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_xml),
        ):
            inv.action_spfe_send_invoice()
        self.assertEqual(inv.spfe_state, "sent")
        self.assertEqual(inv.spfe_locator, "LOCGENV1:O:TESTLOCATOR123==")

        # Supplier event: SETTLEMENT
        ev_wiz = self.env["l10n.es.spfe.event.wizard"].create(
            {
                "move_id": inv.id,
                "response_code": "SETTLEMENT",
                "effective_date": "2026-10-25",
                "due_date": "2026-11-20",
                "financing_arrangement": True,
            }
        )
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_xml),
        ):
            ev_wiz.with_context(today="2026-10-26").action_send_event()
        self.assertEqual(inv.spfe_supplier_status, "settled")

        # CancelInvoiceSOAP
        cancel_wiz = self.env["l10n.es.spfe.cancel.wizard"].create(
            {
                "move_id": inv.id,
                "effective_date": "2026-10-26",
                "reason": "Error material de emisión",
            }
        )
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_xml),
        ):
            cancel_wiz.action_confirm_cancel()
        self.assertEqual(inv.spfe_state, "cancelled")

    def test_02_sync_download_vendor_bill_and_customer_payment_event(self):
        """Query filter + Download by LOC imports vendor bill + PAYMENT / REJECTION."""
        sample_out = self._create_spfe_invoice()
        sample_out.action_post()
        sample_ubl_xml = self.env["base.ubl"].spfe_generate_invoice_ubl_xml(sample_out)
        # Simulate another supplier issuing an invoice to our company
        sample_ubl_xml = (
            sample_ubl_xml.replace(sample_out.name.encode(), b"PROV/2026/0099")
            .replace(b"B12345674", b"G87846952")
            .replace(b"Acysos SPFE Test S.L.", b"Proveedor Externo S.L.")
        )

        query_ds = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b"<DocumentStatus xmlns="
            b'"urn:oasis:names:specification:ubl:schema:xsd:DocumentStatus-2"\n'
            b"    xmlns:cac="
            b'"urn:oasis:names:specification:ubl:schema:xsd:'
            b'CommonAggregateComponents-2"\n'
            b"    xmlns:cbc="
            b'"urn:oasis:names:specification:ubl:schema:xsd:'
            b'CommonBasicComponents-2">\n'
            b"    <cbc:ID>QUERY-001</cbc:ID>\n"
            b"    <cbc:IssueDate>2026-10-25</cbc:IssueDate>\n"
            b"    <cac:DocumentResponse>\n"
            b"        <cac:Response>\n"
            b"            <cac:Status>\n"
            b"                <cbc:StatusReasonCode>200</cbc:StatusReasonCode>\n"
            b"                <cbc:StatusReason>OK</cbc:StatusReason>\n"
            b"            </cac:Status>\n"
            b"        </cac:Response>\n"
            b"        <cac:DocumentReference><cbc:ID/></cac:DocumentReference>\n"
            b"    </cac:DocumentResponse>\n"
            b"    <cac:AdditionalDocumentResponse>\n"
            b"        <cac:Response>"
            b"<cbc:ResponseCode>ACCEPTED</cbc:ResponseCode>"
            b"</cac:Response>\n"
            b"        <cac:DocumentReference>\n"
            b"            <cbc:ID>PROV/2026/0099</cbc:ID>\n"
            b"            <cbc:IssueDate>2026-10-20</cbc:IssueDate>\n"
            b"            <cbc:ReferencedDocumentInternalAddress>"
            b"LOCGENV1:C:INCOMINGLOC99=="
            b"</cbc:ReferencedDocumentInternalAddress>\n"
            b"            <cac:IssuerParty>\n"
            b"                <cac:PartyTaxScheme>"
            b"<cbc:CompanyID>G87846952</cbc:CompanyID>"
            b"<cac:TaxScheme/></cac:PartyTaxScheme>\n"
            b"            </cac:IssuerParty>\n"
            b"        </cac:DocumentReference>\n"
            b"    </cac:AdditionalDocumentResponse>\n"
            b"</DocumentStatus>"
        )

        responses = [
            _build_mock_multipart_response(query_ds),
            _build_mock_multipart_response_multi(
                [("respuesta0.xml", query_ds), ("factura1.xml", sample_ubl_xml)]
            ),
        ]
        sync_wiz = self.env["l10n.es.spfe.sync.wizard"].create(
            {
                "company_id": self.company.id,
                "role": "AccountingCustomerParty",
                "date_filter": "IssueDate",
                "date_start": "2026-10-06",
                "date_end": "2026-10-31",
                "download_and_import_bills": True,
            }
        )
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            side_effect=responses,
        ):
            action = sync_wiz.action_sync_spfe_invoices()

        bill = self.env["account.move"].search(
            [("spfe_locator", "=", "LOCGENV1:C:INCOMINGLOC99==")], limit=1
        )
        self.assertTrue(bill)
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(action["res_model"], "account.move")
        dl_sub = self.env["l10n.es.spfe.submission"].search(
            [("operation_type", "=", "download_loc")], limit=1
        )
        self.assertIn('name="Role"', dl_sub.request_soap_xml)

        # Communicate customer PAYMENT event on imported bill
        ok_ds = (SAMPLE_SEND_OK_DS % {b"inv_name": (bill.ref or "").encode()}).replace(
            b"B12345674", b"G87846952"
        )
        pay_wiz = self.env["l10n.es.spfe.event.wizard"].create(
            {
                "move_id": bill.id,
                "response_code": "PAYMENT",
                "effective_date": "2026-10-25",
                "due_date": "2026-11-20",
            }
        )
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ok_ds),
        ):
            pay_wiz.with_context(today="2026-10-26").action_send_event()
        self.assertEqual(bill.spfe_customer_status, "paid")

    def test_03_soap_fault_raises_user_error(self):
        """SOAP 1.2 Fault from AEAT raises descriptive UserError."""
        inv = self._create_spfe_invoice()
        inv.action_post()
        fault_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">\n'
            b"    <env:Body>\n"
            b"        <env:Fault>\n"
            b"            <env:Code><env:Value>env:Sender</env:Value></env:Code>\n"
            b"            <env:Reason>\n"
            b'                <env:Text xml:lang="es">'
            b"Estructura XML no valida</env:Text>\n"
            b"            </env:Reason>\n"
            b"        </env:Fault>\n"
            b"    </env:Body>\n"
            b"</env:Envelope>"
        )
        with (
            patch.object(
                type(self.env["l10n.es.spfe.soap"]),
                "_post_spfe_http",
                return_value=(
                    400,
                    {"Content-Type": "application/soap+xml"},
                    fault_xml,
                ),
            ),
            self.assertRaises(UserError),
        ):
            inv.action_spfe_send_invoice()

    def _reconcile_invoice_with_entry(self, inv):
        rec_line = inv.line_ids.filtered(
            lambda ln: ln.account_id.account_type == "asset_receivable"
        )
        liq_acc = self.env["account.account"].search(
            [
                ("company_ids", "in", self.company.id),
                ("account_type", "in", ("asset_cash", "asset_current")),
            ],
            limit=1,
        )
        misc_journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")],
            limit=1,
        )
        entry = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": misc_journal.id,
                    "date": "2026-10-25",
                    "line_ids": [
                        Command.create(
                            {
                                "name": "Cobro banco",
                                "account_id": liq_acc.id,
                                "debit": inv.amount_total,
                                "credit": 0.0,
                            }
                        ),
                        Command.create(
                            {
                                "name": "Cobro cliente",
                                "account_id": rec_line[0].account_id.id,
                                "partner_id": inv.partner_id.id,
                                "debit": 0.0,
                                "credit": inv.amount_total,
                            }
                        ),
                    ],
                }
            )
        )
        entry.action_post()
        cpart = entry.line_ids.filtered(
            lambda ln: ln.account_id == rec_line[0].account_id
        )
        (rec_line | cpart).reconcile()
        return rec_line

    def test_04_auto_and_manual_full_payment_reconciliation(self):
        """Auto SETTLEMENT/CANCELSETTLEMENT on reconcile + manual banner mode."""
        inv = self._create_spfe_invoice()
        inv.action_post()
        ds_xml = SAMPLE_SEND_OK_DS % {b"inv_name": inv.name.encode()}
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_xml),
        ):
            inv.action_spfe_send_invoice()

        # Registered SPFE invoice cannot be reset to draft
        with self.assertRaises(UserError):
            inv.button_draft()

        # 1. Automatic mode (default True): reconcile queues pending -> cron sends
        rec_line = self._reconcile_invoice_with_entry(inv)
        self.assertEqual(inv.payment_state, "paid")
        self.assertTrue(inv.spfe_payment_pending)
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_xml),
        ):
            self.env["l10n.es.spfe.submission"]._cron_send_pending_spfe_invoices()
        self.assertEqual(inv.spfe_supplier_status, "settled")
        self.assertFalse(inv.spfe_payment_pending)

        # Unreconcile -> cron sends CANCELSETTLEMENT
        rec_line.remove_move_reconcile()
        self.assertTrue(inv.spfe_payment_pending)
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_xml),
        ):
            self.env["l10n.es.spfe.submission"]._cron_send_pending_spfe_invoices()
        self.assertEqual(inv.spfe_supplier_status, "none")
        self.assertFalse(inv.spfe_payment_pending)

        # 2. Manual mode (spfe_auto_send_payment=False): banner pending -> manual send
        self.company.spfe_auto_send_payment = False
        self._reconcile_invoice_with_entry(inv)
        self.assertTrue(inv.spfe_payment_pending)
        self.assertEqual(inv.spfe_supplier_status, "none")
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_xml),
        ):
            inv.action_spfe_send_payment_status()
        self.assertEqual(inv.spfe_supplier_status, "settled")
        self.assertFalse(inv.spfe_payment_pending)

    def _reconcile_bill_with_entry(self, bill):
        pay_line = bill.line_ids.filtered(
            lambda ln: ln.account_id.account_type == "liability_payable"
        )
        liq_acc = self.env["account.account"].search(
            [
                ("company_ids", "in", self.company.id),
                ("account_type", "in", ("asset_cash", "asset_current")),
            ],
            limit=1,
        )
        misc_journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")],
            limit=1,
        )
        entry = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": misc_journal.id,
                    "date": "2026-10-25",
                    "line_ids": [
                        Command.create(
                            {
                                "name": "Pago proveedor",
                                "account_id": pay_line[0].account_id.id,
                                "partner_id": bill.partner_id.id,
                                "debit": bill.amount_total,
                                "credit": 0.0,
                            }
                        ),
                        Command.create(
                            {
                                "name": "Banco",
                                "account_id": liq_acc.id,
                                "debit": 0.0,
                                "credit": bill.amount_total,
                            }
                        ),
                    ],
                }
            )
        )
        entry.action_post()
        cpart = entry.line_ids.filtered(
            lambda ln: ln.account_id == pay_line[0].account_id
        )
        (pay_line | cpart).reconcile()
        return pay_line

    def test_05_cron_query_vendor_payments_and_prepaid_send(self):
        """Test vendor PAYMENT/CANCELPAYMENT, prepaid send, cron retry & QUERYBYID."""
        tax_in = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
                ("type_tax_use", "=", "purchase"),
                ("amount", "=", 21.0),
            ],
            limit=1,
        )
        # Manual vendor bill not registered in SPFE must NOT queue PAYMENT
        manual_bill = self._create_spfe_invoice(
            move_type="in_invoice",
            ref="MANUAL-2026-01",
            partner_bank_id=False,
            lines=[
                {
                    "product_id": self.product.id,
                    "name": "Compra manual fuera de SPFE",
                    "quantity": 1.0,
                    "price_unit": 25.0,
                    "tax_ids": [Command.set(tax_in.ids)],
                }
            ],
        )
        manual_bill.action_post()
        self._reconcile_bill_with_entry(manual_bill)
        self.assertFalse(manual_bill.spfe_payment_pending)

        # A. SPFE vendor bill auto PAYMENT + CANCELPAYMENT via cron
        bill = self._create_spfe_invoice(
            move_type="in_invoice",
            ref="SUP-2026-88",
            spfe_state="sent",
            partner_bank_id=False,
            lines=[
                {
                    "product_id": self.product.id,
                    "name": "Compra SPFE",
                    "quantity": 1.0,
                    "price_unit": 50.0,
                    "tax_ids": [Command.set(tax_in.ids)],
                }
            ],
        )
        bill.action_post()
        ok_bill_ds = (SAMPLE_SEND_OK_DS % {b"inv_name": b"SUP-2026-88"}).replace(
            b"B12345674", b"A12345674"
        )
        pay_line = self._reconcile_bill_with_entry(bill)
        self.assertTrue(bill.spfe_payment_pending)
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ok_bill_ds),
        ):
            self.env["l10n.es.spfe.submission"]._cron_send_pending_spfe_invoices()
        self.assertEqual(bill.spfe_customer_status, "paid")

        pay_line.remove_move_reconcile()
        self.assertTrue(bill.spfe_payment_pending)
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ok_bill_ds),
        ):
            self.env["l10n.es.spfe.submission"]._cron_send_pending_spfe_invoices()
        self.assertEqual(bill.spfe_customer_status, "none")

        # Vendor bill missing supplier reference raises UserError if forced
        bill.ref = False
        self.assertFalse(bill.spfe_payment_pending)
        with self.assertRaises(UserError):
            bill._build_auto_spfe_event_dict("PAYMENT")
        bill.ref = "SUP-2026-88"

        # Posted credit note via reversal_move_ids marks CorrectedInvoice
        bill_refund = self._create_spfe_invoice(
            move_type="in_refund",
            ref="SUP-2026-88-R",
            reversed_entry_id=bill.id,
            partner_bank_id=False,
            lines=[
                {
                    "product_id": self.product.id,
                    "name": "Abono parcial SPFE",
                    "quantity": 1.0,
                    "price_unit": 10.0,
                    "tax_ids": [Command.set(tax_in.ids)],
                }
            ],
        )
        bill_refund.action_post()
        self.assertTrue(bill._has_spfe_posted_refunds())
        self.assertTrue(
            bill._build_auto_spfe_event_dict("PAYMENT")["is_corrected_invoice"]
        )

        # B. Prepaid invoice sent -> queues SETTLEMENT -> cron failure & retry
        inv = self._create_spfe_invoice()
        inv.action_post()
        self._reconcile_invoice_with_entry(inv)
        ds_inv = SAMPLE_SEND_OK_DS % {b"inv_name": inv.name.encode()}
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(ds_inv),
        ):
            inv.action_spfe_send_invoice()
        self.assertEqual(inv.spfe_state, "sent")
        self.assertTrue(inv.spfe_payment_pending)

        with (
            mute_logger("odoo.addons.l10n_es_spfe.models.account_move"),
            patch.object(
                type(self.env["l10n.es.spfe.soap"]),
                "_post_spfe_http",
                side_effect=UserError("Temporary network glitch"),
            ),
        ):
            self.env["l10n.es.spfe.submission"]._cron_send_pending_spfe_invoices()
        self.assertTrue(inv.spfe_payment_pending)
        self.assertIn("Temporary network glitch", inv.spfe_last_error)

        # action_post with spfe_auto_send=True does NOT block HTTP synchronously
        self.company.spfe_auto_send = True
        inv_cron = self._create_spfe_invoice()
        inv_cron.action_post()
        self.assertEqual(inv_cron.spfe_state, "not_sent")

        ds_cron = SAMPLE_SEND_OK_DS % {b"inv_name": inv_cron.name.encode()}
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            side_effect=[
                _build_mock_multipart_response(ds_cron),
                _build_mock_multipart_response(ds_inv),
            ],
        ):
            self.env["l10n.es.spfe.submission"]._cron_send_pending_spfe_invoices()
        self.assertEqual(inv_cron.spfe_state, "sent")
        self.assertEqual(inv.spfe_supplier_status, "settled")
        self.company.spfe_auto_send = False

        # C. Query status (QUERYBYID) & Download by ID (DOWNLOADBYID)
        inv_q = self._create_spfe_invoice()
        inv_q.action_post()
        ds_q = SAMPLE_SEND_OK_DS % {b"inv_name": inv_q.name.encode()}
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            side_effect=[
                _build_mock_multipart_response(ds_q),
                _build_mock_multipart_response(ok_bill_ds),
            ],
        ):
            (inv_q | bill).action_spfe_query_status()
        self.assertEqual(inv_q.spfe_state, "sent")

        ubl_q = self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv_q)
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response_multi(
                [("respuesta0.xml", ds_q), ("factura0.xml", ubl_q)]
            ),
        ):
            inv_q.action_spfe_download_by_id()
        self.assertTrue(inv_q.spfe_ubl_attachment_id)

    def test_06_wizard_agency_and_error_branches(self):
        """Cover error branches in wizards, tax agency URLs, and submission codes."""
        agency = self.company._get_spfe_tax_agency()
        self.company.spfe_use_seal_certificate = True
        conn_pre_seal = agency._get_spfe_connection_info(self.company, "send")
        self.assertIn("prewww10.aeat.es", conn_pre_seal["url"])
        self.company.spfe_test = False
        conn_prod_seal = agency._get_spfe_connection_info(self.company, "send")
        self.assertIn("www10.agenciatributaria.gob.es", conn_prod_seal["url"])
        self.company.spfe_use_seal_certificate = False
        conn_prod_cert = agency._get_spfe_connection_info(self.company, "send")
        self.assertIn("www1.agenciatributaria.gob.es", conn_prod_cert["url"])
        with self.assertRaises(UserError):
            agency._get_spfe_connection_info(self.company, "validate_pre")
        with self.assertRaises(UserError):
            agency._get_spfe_connection_info(self.company, "unknown_key")
        self.company.spfe_test = True

        sub_model = self.env["l10n.es.spfe.submission"]
        self.assertEqual(sub_model._map_response_code_to_state("406"), "partial")
        self.assertEqual(sub_model._map_response_code_to_state("400"), "rejected")
        self.assertEqual(sub_model._map_response_code_to_state("500"), "error")

        draft_inv = self._create_spfe_invoice()
        with self.assertRaises(UserError):
            draft_inv.action_spfe_query_status()
        with self.assertRaises(UserError):
            draft_inv.action_spfe_download_by_id()
        with self.assertRaises(UserError):
            draft_inv.action_open_spfe_event_wizard()
        with self.assertRaises(UserError):
            draft_inv.action_open_spfe_cancel_wizard()
        with self.assertRaises(UserError):
            draft_inv.action_spfe_send_payment_status()

        # Cron isolates invalid/failing moves via savepoint and marks rejected
        no_zip_partner = self.env["res.partner"].create(
            {
                "name": "Cliente Sin CP S.L.",
                "vat": "ESA12345674",
                "street": "Calle 3",
                "city": "Madrid",
                "country_id": self.country_es.id,
            }
        )
        bad_inv = self._create_spfe_invoice(partner=no_zip_partner)
        bad_inv.action_post()
        good_inv = self._create_spfe_invoice()
        good_inv.action_post()
        self.company.spfe_auto_send = True
        ds_good = SAMPLE_SEND_OK_DS % {b"inv_name": good_inv.name.encode()}
        with (
            mute_logger("odoo.addons.l10n_es_spfe.models.spfe_submission"),
            patch.object(
                type(self.env["l10n.es.spfe.soap"]),
                "_post_spfe_http",
                return_value=_build_mock_multipart_response(ds_good),
            ),
        ):
            sub_model._cron_send_pending_spfe_invoices()
        self.assertEqual(good_inv.spfe_state, "sent")
        self.assertEqual(bad_inv.spfe_state, "rejected")
        self.assertTrue(bad_inv.spfe_last_error)
        self.company.spfe_auto_send = False

        draft_inv.action_post()
        act_url = draft_inv.action_spfe_generate_ubl_xml()
        self.assertEqual(act_url["type"], "ir.actions.act_url")

        # Rejection response (400) from SendInvoiceSOAP
        rej_ds = SAMPLE_SEND_OK_DS.replace(
            b"<cbc:ResponseCode>200</cbc:ResponseCode>",
            b"<cbc:ResponseCode>400</cbc:ResponseCode>",
        ).replace(
            b"<cbc:DocumentStatusCode>200</cbc:DocumentStatusCode>",
            b"<cbc:DocumentStatusCode>400</cbc:DocumentStatusCode>",
        ) % {b"inv_name": draft_inv.name.encode()}
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(rej_ds),
        ):
            draft_inv.action_spfe_send_invoice()
        self.assertEqual(draft_inv.spfe_state, "rejected")

        # Cancel & Event wizard 400 rejections return display_notification & keep audit
        rej_good_ds = SAMPLE_SEND_OK_DS.replace(
            b"<cbc:ResponseCode>200</cbc:ResponseCode>",
            b"<cbc:ResponseCode>400</cbc:ResponseCode>",
        ).replace(
            b"<cbc:DocumentStatusCode>200</cbc:DocumentStatusCode>",
            b"<cbc:DocumentStatusCode>400</cbc:DocumentStatusCode>",
        ) % {b"inv_name": good_inv.name.encode()}
        cancel_wiz = self.env["l10n.es.spfe.cancel.wizard"].create(
            {
                "move_id": good_inv.id,
                "effective_date": "2026-10-26",
                "reason": "Intento rechazo",
            }
        )
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(rej_good_ds),
        ):
            res_cancel = cancel_wiz.action_confirm_cancel()
        self.assertEqual(res_cancel["tag"], "display_notification")
        self.assertEqual(good_inv.spfe_state, "sent")

        # Event wizard validations + 400 rejection notification
        ev_wiz = self.env["l10n.es.spfe.event.wizard"].create(
            {
                "move_id": draft_inv.id,
                "response_code": "PAYMENT",
                "effective_date": "2026-10-25",
            }
        )
        ev_wiz._onchange_move_id_defaults()
        self.assertEqual(ev_wiz.response_code, "SETTLEMENT")
        with patch.object(
            type(self.env["l10n.es.spfe.soap"]),
            "_post_spfe_http",
            return_value=_build_mock_multipart_response(rej_ds),
        ):
            res_ev = ev_wiz.with_context(today="2026-10-26").action_send_event()
        self.assertEqual(res_ev["tag"], "display_notification")
        ev_wiz.response_code = "PAYMENT"
        with self.assertRaises(UserError):
            ev_wiz.action_send_event()
        ev_wiz.response_code = "DEFAULT"
        ev_wiz.effective_date = "2099-01-01"
        with self.assertRaises(UserError):
            ev_wiz.with_context(today="2026-10-26").action_send_event()
        ev_wiz.effective_date = "2026-10-25"
        ev_wiz.reception_date = "2026-10-01"
        with self.assertRaises(UserError):
            ev_wiz.with_context(today="2026-10-26").action_send_event()
