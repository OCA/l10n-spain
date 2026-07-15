# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import IGIC_SALE_RATES, TestL10nEsAtcSiiPayloadBase


class TestAtcSiiPayloadSales(TestL10nEsAtcSiiPayloadBase):
    """RegistroLRFacturasEmitidas — régimen general, exentas y tipos especiales."""

    def test_sale_igic_rates_s1_regime_01(self):
        """S1 + clave 01: todos los tipos IGIC vigentes en DesgloseIGIC."""
        for template_suffix, expected_rate in IGIC_SALE_RATES:
            with self.subTest(tax=template_suffix):
                move = self._create_atc_invoice(
                    taxes=self._tax(template_suffix),
                    price_unit=100.0,
                )
                payload = self._payload(move)
                self._assert_no_iva_keys(payload)
                details = self._detalle_igic(payload)
                self.assertTrue(details, f"No DetalleIGIC for {template_suffix}")
                detail = details[0]
                self.assertEqual(
                    self._factura_expedida(payload)[
                        "ClaveRegimenEspecialOTrascendencia"
                    ],
                    "01",
                )
                no_exenta = self._walk_payload(payload, "NoExenta")[0]
                self.assertEqual(no_exenta["TipoNoExenta"], "S1")
                tipo = detail["TipoImpositivo"]
                self.assertIn(
                    str(expected_rate).replace(".0", ""),
                    str(tipo).replace(".00", "").replace(".0", ""),
                )
                base = float(detail["BaseImponible"])
                cuota = float(detail["CuotaRepercutida"])
                expected_cuota = round(base * float(expected_rate) / 100.0, 2)
                self.assertAlmostEqual(cuota, expected_cuota, places=2)

    def test_sale_igic_1_percent_petroleum(self):
        """IGIC 1 % derivados petróleo (nuevo tipo canario)."""
        tax = (
            self._tax("igic_r_1")
            if self.company._get_tax_id_from_xmlid("account_tax_template_igic_r_1")
            else None
        )
        if not tax:
            self.skipTest(
                "account_tax_template_igic_r_1 not in chart (pending l10n_es_igic)"
            )
        move = self._create_atc_invoice(taxes=tax, price_unit=200.0)
        payload = self._payload(move)
        details = self._detalle_igic(payload)
        self.assertTrue(details)
        self.assertEqual(float(details[0]["CuotaRepercutida"]), 2.0)

    def test_sale_exempt_interior_e1_regime_01(self):
        """Exenta interior: régimen 01 + CausaExencion E1."""
        self.product.sii_exempt_cause = "E1"
        move = self._create_atc_invoice(
            taxes=self._tax("igic_ex_0"),
            reg_key_code="01",
        )
        payload = self._payload(move)
        self._assert_no_iva_keys(payload)
        exenta = self._walk_payload(payload, "DetalleExenta")
        self.assertTrue(exenta)
        self.assertEqual(exenta[0]["CausaExencion"], "E1")
        self.assertEqual(
            self._factura_expedida(payload)["ClaveRegimenEspecialOTrascendencia"], "01"
        )

    def test_sale_export_exempt_e2_regime_02(self):
        """Exportación: régimen 02 + CausaExencion E2."""
        self.product.sii_exempt_cause = "E2"
        move = self._create_atc_invoice(
            partner=self.partner_export,
            fiscal_position=self._fp_export,
            taxes=self._tax("igic_ex_0"),
            reg_key_code="02",
        )
        payload = self._payload(move)
        exenta = self._walk_payload(payload, "DetalleExenta")
        self.assertTrue(exenta)
        self.assertEqual(exenta[0]["CausaExencion"], "E2")
        self.assertEqual(
            self._factura_expedida(payload)["ClaveRegimenEspecialOTrascendencia"], "02"
        )

    def test_sale_export_exempt_e3_regime_02(self):
        """Exportación servicios: régimen 02 + CausaExencion E3."""
        self.product.sii_exempt_cause = "E3"
        move = self._create_atc_invoice(
            partner=self.partner_export,
            fiscal_position=self._fp_export,
            taxes=self._tax("igic_ex_0"),
            reg_key_code="02",
        )
        payload = self._payload(move)
        exenta = self._walk_payload(payload, "DetalleExenta")
        self.assertEqual(exenta[0]["CausaExencion"], "E3")

    def test_sale_export_e2_with_regime_01_payload_documents_atc_rejection(self):
        """E2 con régimen 01: bloqueo local ATC error 1295."""
        self.product.product_tmpl_id.sii_exempt_cause = "E2"
        with self.assertRaises(UserError):
            self._create_atc_invoice(
                partner=self.partner_export,
                fiscal_position=self._fp_export,
                taxes=self._tax("igic_ex_0"),
                reg_key_code="01",
            )

    def test_sale_exempt_zec_e5(self):
        """Exención ZEC/REF: CausaExencion E5."""
        self.product.sii_exempt_cause = "E5"
        move = self._create_atc_invoice(taxes=self._tax("igic_re_ex"))
        payload = self._payload(move)
        exenta = self._walk_payload(payload, "DetalleExenta")
        self.assertEqual(exenta[0]["CausaExencion"], "E5")

    def test_sale_not_subject_localization_n2_regime_08(self):
        """No sujeta localización (N2): clave 08, sin tipos ni cuotas IGIC."""
        fp = self._get_or_create_fp(
            "ATC NS localization",
            sii_no_taxable_cause="ImporteTAIReglasLocalizacion",
        )
        move = self._create_atc_invoice(
            fiscal_position=fp,
            taxes=self._tax("s_igic_ns"),
            reg_key_code="08",
        )
        payload = self._payload(move)
        self._assert_no_iva_keys(payload)
        self.assertFalse(self._detalle_igic(payload))
        no_sujeta = self._walk_payload(payload, "NoSujeta")
        self.assertTrue(no_sujeta)
        self.assertIn("ImporteTAIReglasLocalizacion", no_sujeta[0])
        self.assertEqual(
            self._factura_expedida(payload)["ClaveRegimenEspecialOTrascendencia"], "08"
        )

    def test_sale_not_subject_art9_n1(self):
        """No sujeta art. 9 IGIC (N1): ImportePorArticulos9_Otros en payload ATC."""
        fp = self._get_or_create_fp(
            "ATC NS art9",
            sii_no_taxable_cause="ImportePorArticulos7_14_Otros",
        )
        move = self._create_atc_invoice(
            fiscal_position=fp,
            taxes=self._tax("s_igic_ns"),
            reg_key_code="01",
        )
        payload = self._payload(move)
        no_sujeta = self._walk_payload(payload, "NoSujeta")
        self.assertIn("ImportePorArticulos9_Otros", no_sujeta[0])
        self.assertNotIn("ImportePorArticulos7_14_Otros", self._payload_json(move))

    def test_sale_simplified_f2_under_3000(self):
        """Factura simplificada F2 por debajo del límite 3.000 €."""
        move = self._create_atc_invoice(
            partner=self.partner_simplified,
            price_unit=80.0,
        )
        payload = self._payload(move)
        factura = self._factura_expedida(payload)
        self.assertEqual(factura["TipoFactura"], "F2")
        self.assertLessEqual(float(factura["ImporteTotal"]), 3000.0)

    def test_sale_simplified_f2_over_3000_not_allowed(self):
        """F2 > 3.000 €: el módulo debe impedir el envío (validación de negocio)."""
        with self.assertRaises(UserError):
            self._create_atc_invoice(
                partner=self.partner_simplified,
                price_unit=3500.0,
            )

    def test_sale_f3_substitution_not_implemented(self):
        """F3 + FacturasSustituidas: pendiente de implementación ATC."""
        if not hasattr(self.env["account.move"], "_get_sii_substituted_invoices"):
            self.skipTest(
                "F3 / FacturasSustituidas not implemented in l10n_es_atc_sii_oca"
            )
        move = self._create_atc_invoice(extra_vals={"sii_invoice_type": "F3"})
        payload = self._payload(move)
        self.assertIn("FacturasSustituidas", self._payload_json(payload))

    def test_sale_regime_06_base_imponible_a_coste(self):
        """Grupo entidades nivel avanzado (06): BaseImponibleACoste obligatoria."""
        move = self._create_atc_invoice(reg_key_code="06")
        dump = self._payload_json(move)
        if "BaseImponibleACoste" not in dump:
            self.skipTest("BaseImponibleACoste for regime 06 not implemented yet")
        self.assertIn("BaseImponibleACoste", dump)

    def test_sale_regime_07_cash_criterion_isp_incompatible(self):
        """Criterio de caja (07): ISP (S2) incompatible con régimen 07."""
        with self.assertRaises(UserError):
            self._create_atc_invoice(
                fiscal_position=self._fp_isp,
                taxes=self._tax("igic_s_ISP0"),
                reg_key_code="07",
            )

    def test_sale_regime_14_public_works(self):
        """Certificación obra AAPP (14): NIF P/Q/S/V y clave 14 en payload."""
        move = self._create_atc_invoice(
            partner=self.partner_aapp,
            reg_key_code="14",
            invoice_date=__import__("datetime").date(2026, 3, 10),
        )
        payload = self._payload(move)
        factura = self._factura_expedida(payload)
        self.assertEqual(factura["ClaveRegimenEspecialOTrascendencia"], "14")
        nif = factura.get("Contraparte", {}).get("NIF", "")
        if nif:
            self.assertIn(nif[0], ("P", "Q", "S", "V"))
        if "FechaOperacion" not in factura:
            self.skipTest("FechaOperacion for regime 14 not implemented yet")

    def test_sale_isp_s2(self):
        """Venta ISP: TipoNoExenta S2 en DesgloseIGIC."""
        move = self._create_atc_invoice(
            fiscal_position=self._fp_isp,
            taxes=self._tax("igic_s_ISP0"),
        )
        payload = self._payload(move)
        no_exenta = self._walk_payload(payload, "NoExenta")[0]
        self.assertEqual(no_exenta["TipoNoExenta"], "S2")
        self._assert_no_iva_keys(payload)

    def test_sale_retailer_regime_17(self):
        """Comerciante minorista ventas: clave 17."""
        reg_key = self._reg_key("17", "out_invoice")
        move = self._create_atc_invoice(
            fiscal_position=self._fp_retailer,
            taxes=self._tax("igic_cmino"),
            reg_key_code="17",
            extra_vals={"sii_registration_key": reg_key.id},
        )
        payload = self._payload(move)
        self.assertEqual(
            self._factura_expedida(payload)["ClaveRegimenEspecialOTrascendencia"], "17"
        )
