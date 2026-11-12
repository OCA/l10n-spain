# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import copy
from unittest.mock import patch

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)
from odoo.addons.l10n_es_aeat_sii_oca.tests.test_sii_send_batch import (
    FakeSiiService,
)


class FakeSiiMatchService(FakeSiiService):
    """AEAT service that keeps the records it accepts and answers the queries
    with them, as the AEAT does."""

    def __init__(self, results=None, faulty=()):
        super().__init__(results=results, faulty=faulty)
        self.registered = []
        self.queries = []

    def _answer(self, operation, header, payload):
        res = super()._answer(operation, header, payload)
        if operation.startswith("Suministro"):
            records = [payload] if isinstance(payload, dict) else payload
            for record, line in zip(records, res["RespuestaLinea"], strict=True):
                if line["EstadoRegistro"] == "Correcto":
                    self.register(record, res["CSV"])
        return res

    def register(self, record, csv):
        """Store a record as the AEAT returns it in the queries."""
        if "FacturaExpedida" in record:
            data_key, sent_key = "DatosFacturaEmitida", "FacturaExpedida"
        else:
            data_key, sent_key = "DatosFacturaRecibida", "FacturaRecibida"
        registered = {
            "IDFactura": copy.deepcopy(record["IDFactura"]),
            "PeriodoLiquidacion": {
                key: str(value) for key, value in record["PeriodoLiquidacion"].items()
            },
            data_key: copy.deepcopy(record[sent_key]),
            "DatosPresentacion": {"CSV": csv},
            "EstadoFactura": {"EstadoRegistro": "Correcta", "EstadoCuadre": "2"},
        }
        self.registered.append(registered)
        return registered

    def ConsultaLRFacturasEmitidas(self, header, query):
        return {
            "RegistroRespuestaConsultaLRFacturasEmitidas": self._query(
                "DatosFacturaEmitida", query
            )
        }

    def ConsultaLRFacturasRecibidas(self, header, query):
        return {
            "RegistroRespuestaConsultaLRFacturasRecibidas": self._query(
                "DatosFacturaRecibida", query
            )
        }

    def _query(self, data_key, query):
        self.queries.append(query)
        period = {key: str(value) for key, value in query["PeriodoLiquidacion"].items()}
        records = [
            rec
            for rec in self.registered
            if data_key in rec and rec["PeriodoLiquidacion"] == period
        ]
        if "IDFactura" in query:
            id_invoice = query["IDFactura"]
            records = [
                rec
                for rec in records
                if rec["IDFactura"]["NumSerieFacturaEmisor"]
                == id_invoice["NumSerieFacturaEmisor"]
                and rec["IDFactura"]["IDEmisorFactura"].get("NIF")
                == id_invoice["IDEmisorFactura"].get("NIF")
            ]
        return copy.deepcopy(records)


class TestSiiMatchContrast(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cron = cls.env.ref("l10n_es_aeat_sii_oca.invoice_send_to_sii")
        cls.tax_21 = cls.company._get_taxes_from_xmlids(
            ["account_tax_template_s_iva21b"]
        )

    @classmethod
    def _create_posted_invoice(cls, move_type="out_invoice", **vals):
        invoice = cls._create_invoice(move_type)
        invoice.write(vals)
        invoice.action_post()
        return invoice

    def _patch_aeat(self, service):
        return patch.object(
            type(self.env["account.move"]),
            "_connect_aeat",
            lambda move, mapping_key: service,
        )

    def _send(self, invoices, service):
        invoices.send_sii_now()
        with self._patch_aeat(service), self.enter_registry_test_mode():
            # As the cron worker, which runs it with its own user
            self.cron.sudo().method_direct_trigger()
        self.assertEqual(set(invoices.mapped("aeat_state")), {"sent"})

    def _contrast(self, invoices, service):
        with self._patch_aeat(service):
            invoices.contrast_aeat()

    def test_contrast_correct(self):
        invoice = self._create_posted_invoice()
        service = FakeSiiMatchService()
        self._send(invoice, service)
        self._contrast(invoice, service)
        self.assertEqual(invoice.sii_contrast_state, "correct")
        self.assertEqual(invoice.sii_match_state, "2")
        self.assertFalse(invoice.sii_match_difference_ids)
        query = service.queries[0]["IDFactura"]
        self.assertEqual(query["NumSerieFacturaEmisor"], invoice.name)
        self.assertEqual(query["IDEmisorFactura"]["NIF"], "U2687761C")

    def test_contrast_different_amount(self):
        invoice = self._create_posted_invoice()
        service = FakeSiiMatchService()
        self._send(invoice, service)
        service.registered[0]["DatosFacturaEmitida"]["ImporteTotal"] = 99.0
        self._contrast(invoice, service)
        self.assertEqual(invoice.sii_contrast_state, "partially")
        difference = invoice.sii_match_difference_ids
        self.assertEqual(difference.sii_field, "ImporteTotal")
        self.assertEqual(float(difference.sii_return_field_value), 99.0)
        self.assertEqual(float(difference.sii_sent_field_value), invoice.amount_total)

    def test_contrast_supplier_invoice(self):
        invoice = self._create_posted_invoice("in_invoice", ref="SUP-001")
        service = FakeSiiMatchService()
        self._send(invoice, service)
        self._contrast(invoice, service)
        self.assertEqual(invoice.sii_contrast_state, "correct")
        query = service.queries[0]["IDFactura"]
        self.assertEqual(query["NumSerieFacturaEmisor"], "SUP-001")
        self.assertEqual(query["IDEmisorFactura"]["NIF"], "F35999705")
