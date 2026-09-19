# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from .common import TestL10nEsAtcSiiPayloadBase


class TestAtcSiiPayloadRectifications(TestL10nEsAtcSiiPayloadBase):
    """Rectificativas R1–R5 y bajas de registro."""

    def _create_refund(self, origin, refund_type="I", specific_type=None):
        vals = {"invoice_date": date(2026, 3, 20)}
        ctx = {"sii_refund_type": refund_type}
        if origin.move_type.startswith("in"):
            ctx["supplier_invoice_number"] = f"REF-{origin.ref or origin.name}"
        refund = origin.with_context(**ctx)._reverse_moves([vals])
        if specific_type:
            refund.sii_refund_specific_invoice_type = specific_type
        refund.action_post()
        return refund

    def test_refund_by_differences_tipo_i(self):
        """Rectificativa por diferencias: TipoRectificativa = I."""
        origin = self._create_atc_invoice(price_unit=100.0)
        refund = self._create_refund(origin, refund_type="I")
        payload = self._payload(refund)
        factura = self._factura_expedida(payload)
        self.assertEqual(factura["TipoRectificativa"], "I")
        self.assertNotIn("ImporteRectificacion", factura)
        self.assertTrue(factura["TipoFactura"].startswith("R"))

    def test_refund_by_substitution_tipo_s_not_supported(self):
        """Rectificativa por sustitución (S): rehabilitada en módulo ATC."""
        origin = self._create_atc_invoice(price_unit=100.0)
        refund = self._create_refund(origin, refund_type="S")
        payload = self._payload(refund)
        factura = self._factura_expedida(payload)
        self.assertEqual(factura["TipoRectificativa"], "S")
        self.assertIn("ImporteRectificacion", factura)

    def test_refund_types_r1_r4(self):
        """Tipos de factura rectificativa R1–R4 en payload."""
        origin = self._create_atc_invoice(price_unit=50.0)
        for rtype in ("R1", "R2", "R3", "R4"):
            with self.subTest(tipo=rtype):
                refund = self._create_refund(
                    origin,
                    refund_type="I",
                    specific_type=rtype,
                )
                payload = self._payload(refund)
                self.assertEqual(self._factura_expedida(payload)["TipoFactura"], rtype)

    def test_refund_type_r5_simplified(self):
        """R5 solo aplica a facturas simplificadas (F2)."""
        origin = self._create_atc_invoice(
            partner=self.partner_simplified,
            price_unit=40.0,
        )
        refund = self._create_refund(origin, refund_type="I")
        payload = self._payload(refund)
        self.assertEqual(self._factura_expedida(payload)["TipoFactura"], "R5")

    def test_cancellation_same_period_as_original(self):
        """Baja: Ejercicio y Periodo coinciden con la factura de alta."""
        move = self._create_atc_invoice(
            invoice_date=date(2026, 5, 12),
            price_unit=120.0,
        )
        alta_periodo = self._periodo_liquidacion(self._payload(move))
        cancel = move._get_aeat_invoice_dict_out(cancel=True)
        cancel_periodo = cancel["PeriodoLiquidacion"]
        self.assertEqual(alta_periodo["Ejercicio"], cancel_periodo["Ejercicio"])
        self.assertEqual(alta_periodo["Periodo"], cancel_periodo["Periodo"])

    def test_purchase_refund_rectificativa(self):
        """Rectificativa compra: TipoRectificativa en FacturaRecibida."""
        origin = self._create_atc_invoice(
            move_type="in_invoice",
            extra_vals={"ref": "ORIG-PUR"},
        )
        refund = self._create_refund(origin, refund_type="I")
        payload = self._payload(refund)
        factura = self._factura_recibida(payload)
        self.assertEqual(factura["TipoRectificativa"], "I")
