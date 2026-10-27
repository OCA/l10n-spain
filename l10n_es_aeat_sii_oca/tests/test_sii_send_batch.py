# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import json
from unittest.mock import patch

from zeep.exceptions import Fault

from .test_l10n_es_aeat_sii import TestL10nEsAeatSiiBase


class FakeSiiService:
    """Stand-in for the AEAT SOAP service. It answers each record with the
    result configured for its number, "Correcto" by default, and rejects the
    whole request when it includes a faulty number, as the AEAT does with a
    schema error."""

    def __init__(self, results=None, faulty=()):
        self.results = results or {}
        self.faulty = faulty
        self.calls = []
        self.operations = []

    def SuministroLRFacturasEmitidas(self, header, payload):
        return self._answer("SuministroLRFacturasEmitidas", header, payload)

    def SuministroLRFacturasRecibidas(self, header, payload):
        return self._answer("SuministroLRFacturasRecibidas", header, payload)

    def AnulacionLRFacturasEmitidas(self, header, payload):
        return self._answer("AnulacionLRFacturasEmitidas", header, payload)

    def AnulacionLRFacturasRecibidas(self, header, payload):
        return self._answer("AnulacionLRFacturasRecibidas", header, payload)

    def _answer(self, operation, header, payload):
        if isinstance(payload, dict):  # zeep also accepts a single record
            payload = [payload]
        self.calls.append(payload)
        self.operations.append(operation)
        numbers = [inv["IDFactura"]["NumSerieFacturaEmisor"] for inv in payload]
        if set(numbers) & set(self.faulty):
            raise Fault("Codigo[4102].El XML no cumple el esquema.")
        lines = []
        for inv in payload:
            issuer = inv["IDFactura"]["IDEmisorFactura"].get("NIF")
            number = inv["IDFactura"]["NumSerieFacturaEmisor"]
            line = {
                "IDFactura": inv["IDFactura"],
                "EstadoRegistro": "Correcto",
                "CodigoErrorRegistro": None,
                "DescripcionErrorRegistro": None,
                "CSV": None,
                "RegistroDuplicado": None,
            }
            line.update(self.results.get((issuer, number), {}))
            lines.append(line)
        states = {line["EstadoRegistro"] for line in lines}
        if states == {"Correcto"}:
            state = "Correcto"
        elif states == {"Incorrecto"}:
            state = "Incorrecto"
        else:
            state = "ParcialmenteCorrecto"
        return {
            "CSV": False if state == "Incorrecto" else f"CSV{len(self.calls)}",
            "DatosPresentacion": None,
            "Cabecera": header,
            "EstadoEnvio": state,
            "RespuestaLinea": lines,
        }


class TestSiiSendBatch(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "Test partner 2", "vat": "ESA12345674"}
        )
        cls.cron = cls.env.ref("l10n_es_aeat_sii_oca.invoice_send_to_sii")

    @classmethod
    def _create_posted_invoices(cls, move_type, count, partner=None, ref=None):
        invoices = cls.env["account.move"]
        for _i in range(count):
            invoice = cls._create_invoice(move_type)
            invoice.write({"partner_id": (partner or cls.partner).id, "ref": ref})
            invoices |= invoice
        invoices.action_post()
        return invoices

    def _send(self, invoices, service):
        invoices.send_sii_now()
        self._run_cron(service)

    def _run_cron(self, service):
        with patch.object(
            type(self.env["account.move"]),
            "_connect_aeat",
            lambda move, mapping_key: service,
        ):
            self.cron.method_direct_trigger()

    def _sent_numbers(self, service):
        return sorted(
            sorted(inv["IDFactura"]["NumSerieFacturaEmisor"] for inv in payload)
            for payload in service.calls
        )

    def test_send_batch_one_request_per_book(self):
        out_invoices = self._create_posted_invoices("out_invoice", 2)
        in_invoice = self._create_posted_invoices("in_invoice", 1, ref="SUP-1")
        service = FakeSiiService()
        self._send(out_invoices + in_invoice, service)
        self.assertEqual(
            self._sent_numbers(service),
            sorted([["SUP-1"], sorted(out_invoices.mapped("name"))]),
        )
        for invoice in out_invoices + in_invoice:
            self.assertEqual(invoice.aeat_state, "sent")
            self.assertFalse(invoice.aeat_send_failed)
            self.assertFalse(invoice.sii_send_date)
            self.assertTrue(invoice.sii_csv)
            sii_return = json.loads(invoice.sii_return)
            self.assertEqual(
                [
                    line["IDFactura"]["NumSerieFacturaEmisor"]
                    for line in sii_return["RespuestaLinea"]
                ],
                [
                    invoice._get_aeat_invoice_dict()["IDFactura"][
                        "NumSerieFacturaEmisor"
                    ]
                ],
            )
        self.assertTrue(in_invoice.sii_account_registration_date)

    def test_send_batch_partially_correct(self):
        invoices = self._create_posted_invoices("out_invoice", 3)
        company_nif = self.company.partner_id._parse_aeat_vat_info()[2]
        service = FakeSiiService(
            results={
                (company_nif, invoices[1].name): {
                    "EstadoRegistro": "AceptadoConErrores",
                    "CodigoErrorRegistro": 2011,
                    "DescripcionErrorRegistro": "Accepted with errors",
                },
                (company_nif, invoices[2].name): {
                    "EstadoRegistro": "Incorrecto",
                    "CodigoErrorRegistro": 1100,
                    "DescripcionErrorRegistro": "Wrong value",
                },
            }
        )
        self._send(invoices, service)
        self.assertEqual(len(service.calls), 1)
        self.assertEqual(
            invoices.mapped("aeat_state"), ["sent", "sent_w_errors", "not_sent"]
        )
        self.assertEqual(invoices.mapped("aeat_send_failed"), [False, True, True])
        self.assertEqual(invoices[2].aeat_send_error, "1100 | Wrong value")
        self.assertFalse(invoices[2].sii_csv)

    def test_send_batch_same_number_different_suppliers(self):
        invoice_1 = self._create_posted_invoices("in_invoice", 1, ref="A-1")
        invoice_2 = self._create_posted_invoices(
            "in_invoice", 1, partner=self.partner_2, ref="A-1"
        )
        nif_2 = self.partner_2._parse_aeat_vat_info()[2]
        service = FakeSiiService(
            results={(nif_2, "A-1"): {"EstadoRegistro": "Incorrecto"}}
        )
        self._send(invoice_1 + invoice_2, service)
        self.assertEqual(self._sent_numbers(service), [["A-1", "A-1"]])
        self.assertEqual(invoice_1.aeat_state, "sent")
        self.assertEqual(invoice_2.aeat_state, "not_sent")
        self.assertTrue(invoice_2.aeat_send_failed)

    def test_send_batch_already_registered(self):
        """A lost response makes the document to be sent again as a new one."""
        invoice, other_invoice = self._create_posted_invoices("out_invoice", 2)
        company_nif = self.company.partner_id._parse_aeat_vat_info()[2]
        service = FakeSiiService(
            results={
                (company_nif, invoice.name): {
                    "EstadoRegistro": "Incorrecto",
                    "CodigoErrorRegistro": 3000,
                    "DescripcionErrorRegistro": "Registro duplicado",
                    "RegistroDuplicado": {"EstadoRegistro": "Correcta"},
                },
            }
        )
        self._send(invoice + other_invoice, service)
        self.assertEqual(invoice.aeat_state, "sent")
        self.assertFalse(invoice.aeat_send_failed)
        # The CSV of this request doesn't belong to the first registration
        self.assertEqual(other_invoice.sii_csv, "CSV1")
        self.assertFalse(invoice.sii_csv)

    def test_send_batch_isolates_rejected_document(self):
        invoices = self._create_posted_invoices("out_invoice", 5)
        service = FakeSiiService(faulty=[invoices[3].name])
        self._send(invoices, service)
        self.assertEqual(
            invoices.mapped("aeat_state"),
            ["sent", "sent", "sent", "not_sent", "sent"],
        )
        self.assertTrue(invoices[3].aeat_send_failed)
        self.assertIn("4102", invoices[3].sii_return)

    def test_send_batch_request_rejected(self):
        """A rejection common to all the documents doesn't split the request
        down to each document."""
        invoices = self._create_posted_invoices("out_invoice", 8)
        service = FakeSiiService(faulty=invoices.mapped("name"))
        self._send(invoices, service)
        self.assertEqual(len(service.calls), 3)
        self.assertEqual(set(invoices.mapped("aeat_state")), {"not_sent"})
        self.assertTrue(all(invoices.mapped("aeat_send_failed")))
        self.assertFalse(any(invoices.mapped("sii_send_date")))

    def _cancel_in_sii(self, invoices, service):
        self._send(invoices, FakeSiiService())
        invoices.button_cancel()
        invoices.cancel_sii()
        invoices.send_sii_now()
        self._run_cron(service)

    def test_cancel_batch(self):
        invoices = self._create_posted_invoices("out_invoice", 3)
        service = FakeSiiService()
        self._cancel_in_sii(invoices, service)
        self.assertEqual(service.operations, ["AnulacionLRFacturasEmitidas"])
        self.assertEqual(self._sent_numbers(service), [sorted(invoices.mapped("name"))])
        self.assertEqual(set(invoices.mapped("aeat_state")), {"cancelled"})
        self.assertFalse(any(invoices.mapped("sii_needs_cancel")))
        self.assertFalse(any(invoices.mapped("aeat_send_failed")))

    def test_cancel_batch_partially_correct(self):
        invoices = self._create_posted_invoices("out_invoice", 3)
        company_nif = self.company.partner_id._parse_aeat_vat_info()[2]
        service = FakeSiiService(
            results={
                (company_nif, invoices[1].name): {
                    "EstadoRegistro": "Incorrecto",
                    "CodigoErrorRegistro": 3001,
                    "DescripcionErrorRegistro": "Registro no existe",
                },
                (company_nif, invoices[2].name): {
                    "EstadoRegistro": "Incorrecto",
                    "CodigoErrorRegistro": 1100,
                    "DescripcionErrorRegistro": "Wrong value",
                },
            }
        )
        self._cancel_in_sii(invoices, service)
        self.assertEqual(len(service.calls), 1)
        self.assertEqual(
            invoices.mapped("aeat_state"), ["cancelled", "cancelled", "sent_modified"]
        )
        self.assertEqual(invoices.mapped("sii_needs_cancel"), [False, False, True])
        self.assertTrue(invoices[2].aeat_send_failed)
        self.assertEqual(invoices[2].aeat_send_error, "1100 | Wrong value")
