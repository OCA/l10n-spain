# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from odoo.exceptions import UserError

from .common import ATC_AGENCY_XMLID, TestL10nEsAtcSiiPayloadBase


class TestAtcSiiPayloadAdditionalBooks(TestL10nEsAtcSiiPayloadBase):
    """Libros RECC (cobros/pagos) y bien de inversión anual — cobertura futura."""

    def test_recc_cobros_regime_07_not_implemented(self):
        """RECC cobros SiiFactCOBV1SOAP: pendiente implementación."""
        if not hasattr(self.env["account.move"], "_get_aeat_cobros_dict"):
            self.skipTest("SiiFactCOBV1SOAP / RECC cobros not implemented yet")
        self._create_atc_invoice(reg_key_code="07")
        cobro = self.env["account.payment"].create({})
        payload = cobro._get_aeat_cobros_dict()
        self.assertTrue(payload)

    def test_recc_pagos_regime_07_not_implemented(self):
        """RECC pagos SiiFactPAGV1SOAP: pendiente implementación."""
        if not hasattr(self.env["account.move"], "_get_aeat_pagos_dict"):
            self.skipTest("SiiFactPAGV1SOAP / RECC pagos not implemented yet")

    def test_investment_goods_annual_book_0a_not_implemented(self):
        """Libro anual BI: periodo 0A, ProrrataAnualDefinitiva."""
        model = self.env.get("l10n.es.atc.sii.investment.book")
        if not model:
            self.skipTest("Annual investment goods SII book not implemented yet")
        record = model.create({"year": 2026})
        payload = record._get_aeat_book_dict()
        self.assertEqual(
            payload.get("PeriodoLiquidacion", {}).get("Periodo"),
            "0A",
        )


class TestAtcSiiPayloadNegative(TestL10nEsAtcSiiPayloadBase):
    """Pruebas negativas: cabecera IDVersionSii y coherencia aritmética."""

    def test_header_idversion_10_in_test_mode(self):
        """Entorno cautela: IDVersionSii debe ser 1.0 (evita error ATC 4100)."""
        move = self._create_atc_invoice()
        header = move._get_aeat_header()
        self.assertEqual(header["IDVersionSii"], "1.0")

    def test_header_idversion_11_in_test_mode_not_used_by_default(self):
        """En cautela el módulo no debe enviar 1.1 por defecto (ATC error 4100)."""
        move = self._create_atc_invoice()
        self.company.sii_test = True
        self.assertEqual(move._get_aeat_header()["IDVersionSii"], "1.0")
        self.company.sii_test = False
        self.assertEqual(move._get_aeat_header()["IDVersionSii"], "1.1")

    def test_importe_total_matches_breakdown(self):
        """ImporteTotal coherente con bases y cuotas (tolerancia ±10 € ATC)."""
        move = self._create_atc_invoice(price_unit=123.45)
        payload = self._payload(move)
        factura = self._factura_expedida(payload)
        importe_total = float(factura["ImporteTotal"])
        details = self._detalle_igic(payload)
        if details:
            base = sum(float(d["BaseImponible"]) for d in details)
            cuota = sum(float(d.get("CuotaRepercutida", 0)) for d in details)
            expected = base + cuota
            self.assertLessEqual(abs(importe_total - expected), 10.0)

    def test_importe_total_mismatch_validation(self):
        """Descuadre > 10 €: validación local antes de envío (error 2042)."""
        move = self._create_atc_invoice(price_unit=100.0)
        with patch(
            "odoo.addons.l10n_es_aeat_sii_oca.models.account_move.AccountMove._get_document_amount_total",
            return_value=500.0,
        ):
            with self.assertRaises(UserError):
                move._aeat_check_importe_total()

    def test_payload_uses_igic_keys_not_iva(self):
        """Todo el árbol JSON debe usar claves IGIC tras el mapeo ATC."""
        move = self._create_atc_invoice()
        dump = json.dumps(self._payload(move))
        self.assertNotIn("DesgloseIVA", dump)
        self.assertIn("DesgloseIGIC", dump)
        atc_agency = self.env.ref(ATC_AGENCY_XMLID)
        self.assertEqual(move.company_id.tax_agency_id, atc_agency)
