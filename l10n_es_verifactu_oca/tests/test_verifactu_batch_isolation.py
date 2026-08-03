# Copyright 2026 MDSX - Manuel Diez Silva
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest.mock import MagicMock, patch

from odoo import Command

from .common import TestVerifactuCommon

CONNECT_METHOD = (
    "odoo.addons.l10n_es_verifactu_oca.models.verifactu_invoice_entry."
    "VerifactuInvoiceEntry._connect_verifactu"
)


class TestVerifactuBatchIsolation(TestVerifactuCommon):
    """A document that cannot be built must not block the rest of the batch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_21 = cls.env.ref(
            f"account.{cls.company.id}_account_tax_template_s_iva21b"
        )
        cls.tax_10 = cls.env.ref(
            f"account.{cls.company.id}_account_tax_template_s_iva10b"
        )
        cls.map_line_s1 = cls.env.ref("l10n_es_verifactu_oca.verifactu_map_line_S1")
        cls.map_tax_10 = cls.env.ref("l10n_es_verifactu_oca.s_iva10b")

    def _create_posted_invoice(self, tax, amount=100):
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "account_id": self.account_expense.id,
                            "name": "Test line",
                            "price_unit": amount,
                            "quantity": 1,
                            "tax_ids": [Command.set(tax.ids)],
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _unmap_tax_10(self):
        """Leave the 10% VAT out of the VERI*FACTU map.

        Reproduces the reported case: a tax that was mapped when the invoice was
        posted stops being mapped afterwards, so the data of that invoice can no
        longer be built when the queue is sent.
        """
        self.map_line_s1.tax_xmlid_ids = [Command.unlink(self.map_tax_10.id)]

    def _map_tax_10(self):
        self.map_line_s1.tax_xmlid_ids = [Command.link(self.map_tax_10.id)]

    def _chain_snapshot(self):
        """The links and hashes that make up the chain, to check they survive."""
        entries = self.env["verifactu.invoice.entry"].search(
            [("company_id", "=", self.company.id)]
        )
        return {
            entry.id: (entry.previous_invoice_entry_id.id, entry.document_hash)
            for entry in entries
        }

    def _mock_connection(self, mock_connect):
        """Accept whatever documents are actually sent, and record them."""
        sent_batches = []

        def _send(header, registro_factura_list):
            sent_batches.append(
                [
                    registro["RegistroAlta"]["IDFactura"]["NumSerieFactura"]
                    for registro in registro_factura_list
                ]
            )
            return {
                "CSV": "TEST-CSV",
                "EstadoEnvio": "Correcto",
                "RespuestaLinea": [
                    {
                        "IDFactura": {
                            "NumSerieFactura": registro["RegistroAlta"]["IDFactura"][
                                "NumSerieFactura"
                            ]
                        },
                        "EstadoRegistro": "Correcto",
                    }
                    for registro in registro_factura_list
                ],
            }

        mock_service = MagicMock()
        mock_service.RegFactuSistemaFacturacion.side_effect = _send
        mock_connect.return_value = mock_service
        return sent_batches

    def _run_cron(self):
        # Every real run of the cron gets its own transaction. Flush so that its
        # raw SQL sees the state left behind by the previous one.
        self.env.flush_all()
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()

    def test_faulty_document_does_not_block_the_batch(self):
        """The rest of the batch is sent, and the faulty one says why it is not."""
        self._activate_certificate(self.certificate_password)
        good_1 = self._create_posted_invoice(self.tax_21)
        faulty = self._create_posted_invoice(self.tax_10)
        good_2 = self._create_posted_invoice(self.tax_21)
        chain_before = self._chain_snapshot()
        self._unmap_tax_10()
        with patch(CONNECT_METHOD) as mock_connect:
            sent_batches = self._mock_connection(mock_connect)
            self._run_cron()
        self.assertEqual(
            sent_batches,
            [[good_1.name, good_2.name]],
            "Only the documents that could be built are sent, in chain order",
        )
        self.assertEqual(good_1.aeat_state, "sent")
        self.assertEqual(good_2.aeat_state, "sent")
        self.assertEqual(
            faulty.aeat_state,
            "not_sent",
            "The faulty document is still pending, it has not been sent",
        )
        entry = faulty.last_verifactu_invoice_entry_id
        self.assertEqual(
            entry.send_state,
            "not_sent",
            "The entry keeps its slot in the chain and is retried later",
        )
        self.assertIn(
            "not mapped to VERI*FACTU",
            entry.payload_error,
            "The entry states the real cause, not a connection error",
        )
        self.assertTrue(faulty.aeat_send_failed)
        self.assertEqual(
            faulty.aeat_send_error,
            entry.payload_error,
            "The cause is also visible on the document itself",
        )
        for invoice in (good_1, good_2):
            self.assertFalse(invoice.last_verifactu_invoice_entry_id.payload_error)
        self.assertEqual(
            self._chain_snapshot(),
            chain_before,
            "No link or hash of the chain may change because of a failed send",
        )
        self.assertEqual(
            [1, 1, 1],
            [
                invoice.last_verifactu_invoice_entry_id.send_attempt
                for invoice in (good_1, faulty, good_2)
            ],
            "The attempt is counted for every entry, including the faulty one",
        )

    def test_faulty_document_is_not_reported_as_connection_error(self):
        """The response of the batch must not be labelled as a connection error."""
        self._activate_certificate(self.certificate_password)
        self._create_posted_invoice(self.tax_21)
        self._create_posted_invoice(self.tax_10)
        self._unmap_tax_10()
        with patch(CONNECT_METHOD) as mock_connect:
            self._mock_connection(mock_connect)
            self._run_cron()
        response = self.env["verifactu.invoice.entry.response"].search([], limit=1)
        self.assertEqual(response.name, "Documents not sent to VERI*FACTU")
        exception_activity = self.env["mail.activity"].search(
            [
                (
                    "activity_type_id",
                    "=",
                    self.env.ref(
                        "l10n_es_verifactu_oca.mail_activity_data_exception"
                    ).id,
                ),
                ("res_model", "=", "verifactu.invoice.entry.response"),
            ]
        )
        self.assertFalse(
            exception_activity,
            "A faulty document is not a connection problem with the AEAT",
        )
        warning_activity = self.env["mail.activity"].search(
            [
                ("res_model", "=", "verifactu.invoice.entry.response"),
                (
                    "summary",
                    "=",
                    "Check documents that could not be sent to VERI*FACTU",
                ),
            ]
        )
        self.assertEqual(
            len(warning_activity), 1, "The responsible user is warned about it"
        )

    def test_whole_batch_faulty_is_not_sent_to_the_aeat(self):
        """With nothing that can be built there is nothing to send."""
        self._activate_certificate(self.certificate_password)
        faulty = self._create_posted_invoice(self.tax_10)
        self._unmap_tax_10()
        with patch(CONNECT_METHOD) as mock_connect:
            self._mock_connection(mock_connect)
            self._run_cron()
            mock_connect.assert_not_called()
        self.assertEqual(faulty.aeat_state, "not_sent")
        self.assertIn(
            "not mapped to VERI*FACTU",
            faulty.last_verifactu_invoice_entry_id.payload_error,
        )

    def test_missing_document_does_not_break_the_batch(self):
        """An entry whose document is gone is reported, it does not stop the rest."""
        self._activate_certificate(self.certificate_password)
        good = self._create_posted_invoice(self.tax_21)
        orphan = self._create_posted_invoice(self.tax_21)
        orphan_entry = orphan.last_verifactu_invoice_entry_id
        orphan_entry.document_id = 0
        with patch(CONNECT_METHOD) as mock_connect:
            sent_batches = self._mock_connection(mock_connect)
            self._run_cron()
        self.assertEqual(sent_batches, [[good.name]])
        self.assertEqual(good.aeat_state, "sent")
        self.assertEqual(orphan_entry.send_state, "not_sent")
        self.assertIn("does not exist anymore", orphan_entry.payload_error)

    def test_pending_document_is_sent_once_the_cause_is_fixed(self):
        """The entry keeps its slot, so it is sent as soon as it can be built."""
        self._activate_certificate(self.certificate_password)
        good = self._create_posted_invoice(self.tax_21)
        faulty = self._create_posted_invoice(self.tax_10)
        chain_before = self._chain_snapshot()
        self._unmap_tax_10()
        with patch(CONNECT_METHOD) as mock_connect:
            sent_batches = self._mock_connection(mock_connect)
            self._run_cron()
            self.assertEqual(sent_batches, [[good.name]])
            self._map_tax_10()
            self._run_cron()
        self.assertEqual(
            sent_batches,
            [[good.name], [faulty.name]],
            "The document left behind is sent on the next run, on its own",
        )
        entry = faulty.last_verifactu_invoice_entry_id
        self.assertEqual(faulty.aeat_state, "sent")
        self.assertFalse(entry.payload_error, "The reported cause is cleared")
        self.assertEqual(entry.send_attempt, 2)
        self.assertEqual(
            self._chain_snapshot(),
            chain_before,
            "The chain is the same one built when the documents were posted",
        )

    def test_connection_error_is_still_a_connection_error(self):
        """Documents that can be built but not sent are not payload errors."""
        self._activate_certificate(self.certificate_password)
        invoices = [
            self._create_posted_invoice(self.tax_21),
            self._create_posted_invoice(self.tax_21),
        ]
        with patch(CONNECT_METHOD) as mock_connect:
            mock_connect.side_effect = ConnectionError("AEAT is down")
            self._run_cron()
        response = self.env["verifactu.invoice.entry.response"].search([], limit=1)
        self.assertEqual(response.name, "Connection error with VERI*FACTU")
        for invoice in invoices:
            self.assertEqual(invoice.aeat_state, "not_sent")
            self.assertFalse(
                invoice.last_verifactu_invoice_entry_id.payload_error,
                "Their data was built correctly, the problem was the connection",
            )
