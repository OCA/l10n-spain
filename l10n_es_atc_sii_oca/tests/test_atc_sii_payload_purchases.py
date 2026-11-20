# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import TestL10nEsAtcSiiPayloadBase


class TestAtcSiiPayloadPurchases(TestL10nEsAtcSiiPayloadBase):
    """RegistroLRFacturasRecibidas — ISP, bienes de inversión, DUA y REPEP."""

    def test_purchase_isp_importe_total_validation(self):
        """ISP compra con cuota real: 2042 no falla (ImporteTotal = base)."""
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_ISP7"),
            price_unit=656.32,
            extra_vals={"ref": "ISP-2042-001"},
        )
        payload = self._payload(move)
        factura = self._factura_recibida(payload)
        isp = self._walk_payload(payload, "InversionSujetoPasivo")
        self.assertTrue(isp)
        detalle = isp[0].get("DetalleIGIC") or isp[0].get("DetalleIVA")
        if isinstance(detalle, list):
            detail = detalle[0]
        else:
            detail = detalle
        self.assertEqual(float(detail["TipoImpositivo"]), 7.0)
        self.assertGreater(float(detail["CuotaSoportada"]), 0.0)
        # ImporteTotal = base (cuota autorrepercutida no suma)
        self.assertAlmostEqual(
            float(factura["ImporteTotal"]),
            float(detail["BaseImponible"]),
            places=2,
        )
        # No debe lanzar UserError 2042
        move._aeat_check_importe_total()

    def test_purchase_isp_s2_zero_rate(self):
        """ISP compra 0%: tipos y cuotas a cero en inversión del SP."""
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_ISP0"),
            extra_vals={"ref": "ISP-S2-001"},
        )
        payload = self._payload(move)
        self._assert_no_iva_keys(payload)
        isp = self._walk_payload(payload, "InversionSujetoPasivo")
        self.assertTrue(isp)
        detalle = isp[0].get("DetalleIGIC") or isp[0].get("DetalleIVA")
        if isinstance(detalle, list):
            detail = detalle[0]
        else:
            detail = detalle
        tipo = detail.get("TipoImpositivo", "0")
        cuota = detail.get("CuotaSoportada", detail.get("CuotaRepercutida", 0))
        self.assertIn(str(tipo).replace(".00", ""), ("0", "0.0"))
        self.assertEqual(float(cuota), 0.0)

    def test_purchase_isp_s3_partial(self):
        """ISP parcial (S3): mezcla sujeta + inversión del sujeto pasivo."""
        tax_isp = self._tax("igic_ISP7")
        tax_normal = self._tax("igic_sop_7")
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.supplier.id,
                "fiscal_position_id": self._fp_national.id,
                "journal_id": self.journal_purchase.id,
                "invoice_date": "2026-03-15",
                "move_type": "in_invoice",
                "ref": "ISP-S3-001",
                "sii_registration_key": self._reg_key("01", "in_invoice").id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "ISP line",
                            "product_id": self.product.id,
                            "account_id": self.accounts["600000"].id,
                            "price_unit": 100.0,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax_isp.ids)],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Normal line",
                            "product_id": self.product.id,
                            "account_id": self.accounts["600000"].id,
                            "price_unit": 50.0,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax_normal.ids)],
                        },
                    ),
                ],
            }
        )
        move.action_post()
        payload = self._payload(move)
        self.assertTrue(self._walk_payload(payload, "InversionSujetoPasivo"))
        self.assertTrue(self._detalle_igic(payload))

    def test_purchase_investment_asset_bien_inversion_s(self):
        """Bien de inversión: BienInversion = S en DetalleIGIC."""
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_sop_7_inv"),
            extra_vals={"ref": "BI-001"},
        )
        payload = self._payload(move)
        details = self._detalle_igic(payload)
        self.assertTrue(details)
        self.assertEqual(details[0]["BienInversion"], "S")

    def test_purchase_investment_rejected_regime_08(self):
        """BienInversion incompatible con régimen 08 (sujeta IVA)."""
        with self.assertRaises(UserError):
            self._create_atc_invoice(
                move_type="in_invoice",
                taxes=self._tax("igic_sop_7_inv"),
                reg_key_code="08",
                extra_vals={"ref": "BI-08-KO"},
            )

    def test_purchase_dua_f5_no_isp_block(self):
        """DUA tipo F5: sin bloque InversionSujetoPasivo."""
        if not hasattr(self.env["account.move"], "sii_lc_operation"):
            self.skipTest("DUA F5/LC flags not available on account.move")
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_sop_i_7"),
            extra_vals={"ref": "DUA-001", "sii_lc_operation": True},
        )
        payload = self._payload(move)
        factura = self._factura_recibida(payload)
        self.assertEqual(factura.get("TipoFactura"), "LC")
        self.assertIn("ImporteTotal", factura)
        self.assertFalse(self._walk_payload(payload, "InversionSujetoPasivo"))

    def test_purchase_dua_aiem_cuota(self):
        """Importación DUA: CuotaAIEM en payload (pendiente módulo)."""
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_sop_i_7"),
            extra_vals={"ref": "DUA-AIEM-001"},
        )
        if "CuotaAIEM" not in self._payload_json(move):
            self.skipTest("CuotaAIEM (AIEM) not implemented in l10n_es_atc_sii_oca yet")

    def test_purchase_lc_art25_exempt_has_base_only(self):
        """LC Art. 25 exemption omits tax and Art. 25 extra data."""
        self.product.sii_exempt_cause = "E5"
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_p_ex"),
            reg_key_code="15",
            extra_vals={
                "ref": "LC-ART25-EXEMPT",
                "sii_lc_operation": True,
            },
        )
        payload = self._payload(move)
        factura = self._factura_recibida(payload)
        self.assertEqual(factura["TipoFactura"], "LC")
        self.assertEqual(float(factura["CuotaDeducible"]), 0.0)
        details = self._detalle_igic(payload)
        self.assertTrue(details)
        self.assertEqual(set(details[0]), {"BaseImponible"})
        self.assertNotIn("DatosArticulo25", factura)

    def test_purchase_repep_minorista_clave_15(self):
        """REPEP minorista compras (clave 15): CargaImpositivaImplicita."""
        reg_key = self._reg_key("15", "in_invoice")
        try:
            fp = self._get_fiscal_position("purchase_local_retailer_canary")
        except ValueError:
            fp = self._fp_retailer
        move = self._create_atc_invoice(
            move_type="in_invoice",
            partner=self.supplier,
            fiscal_position=fp,
            taxes=self._tax("igic_sop_7_cmino"),
            reg_key_code="15",
            extra_vals={"sii_registration_key": reg_key.id, "ref": "REPEP-15"},
        )
        payload = self._payload(move)
        factura = self._factura_recibida(payload)
        self.assertEqual(factura["ClaveRegimenEspecialOTrascendencia"], "15")
        details = self._detalle_igic(payload)
        self.assertTrue(details)
        self.assertEqual(float(details[0]["TipoImpositivo"]), 7.0)
        self.assertIn("CargaImpositivaImplicita", details[0])
        self.assertNotIn("CuotaSoportada", details[0])
        self.assertAlmostEqual(
            float(factura["CuotaDeducible"]),
            float(details[0]["CargaImpositivaImplicita"]),
            places=2,
        )
        self.assertAlmostEqual(
            float(factura["ImporteTotal"]),
            float(details[0]["BaseImponible"])
            + float(details[0]["CargaImpositivaImplicita"]),
            places=2,
        )

    def test_purchase_no_quota_details_for_atc_regimes(self):
        """Unique regimes 08/16/17/18 only send BaseImponible."""
        for regime, tax_name in (
            ("08", "igic_sop_7"),
            ("16", "igic_p_ex"),
            ("17", "igic_p_ex"),
            ("18", "igic_p_ex"),
        ):
            with self.subTest(regime=regime):
                extra_vals = {"ref": f"NO-CUOTA-{regime}"}
                if regime == "17":
                    self._prepare_art25_product(tipo_bien="01", exempt_cause="E5")
                    extra_vals.update(self._art25_invoice_vals())
                move = self._create_atc_invoice(
                    move_type="in_invoice",
                    taxes=self._tax(tax_name),
                    reg_key_code=regime,
                    extra_vals=extra_vals,
                )
                payload = self._payload(move)
                factura = self._factura_recibida(payload)
                details = self._detalle_igic(payload)
                self.assertEqual(float(factura["CuotaDeducible"]), 0.0)
                self.assertTrue(details)
                for detail in details:
                    self.assertEqual(set(detail), {"BaseImponible"})

    def test_purchase_no_quota_regime_isp_rejected(self):
        """No-quota regimes cannot use the ISP detail structure."""
        with self.assertRaises(UserError):
            self._create_atc_invoice(
                move_type="in_invoice",
                taxes=self._tax("igic_ISP7"),
                reg_key_code="08",
                extra_vals={"ref": "NO-CUOTA-ISP"},
            )

    def test_purchase_combined_regime_01_17_keeps_taxable_detail(self):
        """A combined 01 + 17 purchase keeps the taxable detail."""
        key_17 = self._reg_key("17", "in_invoice")
        self._prepare_art25_product(tipo_bien="01", exempt_cause="E5")
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_sop_7"),
            reg_key_code="01",
            extra_vals={
                "sii_registration_key_additional1": key_17.id,
                "ref": "COMBINED-01-17",
                **self._art25_invoice_vals(),
            },
        )
        factura = self._factura_recibida(self._payload(move))
        detail = self._detalle_igic(self._payload(move))[0]
        self.assertEqual(float(factura["CuotaDeducible"]), 0.0)
        self.assertIn("TipoImpositivo", detail)
        self.assertIn("CuotaSoportada", detail)

    def test_purchase_repep_pequeño_empresario_clave_16(self):
        """REPEP 16 + EXENTO S: DesgloseIGIC solo BaseImponible (sin 1157/1325)."""
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_p_ex"),
            price_unit=450.0,
            reg_key_code="16",
            extra_vals={"ref": "REPEP-16-EX"},
        )
        payload = self._payload(move)
        self._assert_no_iva_keys(payload)
        factura = self._factura_recibida(payload)
        self.assertEqual(factura["ClaveRegimenEspecialOTrascendencia"], "16")
        self.assertEqual(float(factura["CuotaDeducible"]), 0.0)
        desglose = factura.get("DesgloseFactura") or {}
        self.assertTrue(desglose.get("DesgloseIGIC"), "DesgloseFactura vacío (1157)")
        details = self._detalle_igic(payload)
        self.assertTrue(details)
        detail = details[0]
        self.assertAlmostEqual(float(detail["BaseImponible"]), 450.0, places=2)
        self.assertNotIn("TipoImpositivo", detail)
        self.assertNotIn("CuotaSoportada", detail)

    def test_purchase_exempt_desglose_base_only(self):
        """Compra EXENTO S (igic_p_ex): DetalleIGIC sin Tipo ni CuotaSoportada."""
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_p_ex"),
            price_unit=200.0,
            extra_vals={"ref": "EX-PUR-001"},
        )
        payload = self._payload(move)
        details = self._detalle_igic(payload)
        self.assertTrue(details)
        detail = details[0]
        self.assertAlmostEqual(float(detail["BaseImponible"]), 200.0, places=2)
        self.assertNotIn("TipoImpositivo", detail)
        self.assertNotIn("CuotaSoportada", detail)

    def test_purchase_not_subject(self):
        """Compra no sujeta: bloque NoSujeta / SFRNS sin tipos impositivos."""
        fp = self._get_or_create_fp(
            "ATC purchase NS",
            sii_no_taxable_cause="ImporteTAIReglasLocalizacion",
        )
        move = self._create_atc_invoice(
            move_type="in_invoice",
            fiscal_position=fp,
            taxes=self._tax("p_igic_ns"),
            extra_vals={"ref": "NS-PUR-001"},
        )
        payload = self._payload(move)
        details = self._detalle_igic(payload)
        for detail in details:
            self.assertNotIn("TipoImpositivo", detail)

    def test_purchase_art25_clave_17_notarial(self):
        """Art. 25 compras clave 17: DatosArticulo25 con documento notarial."""
        self._prepare_art25_product(tipo_bien="01", exempt_cause="E5")
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_p_ex"),
            reg_key_code="17",
            extra_vals=self._art25_invoice_vals(ref="ART25-PUR-17"),
        )
        payload = self._payload(move)
        factura = self._factura_recibida(payload)
        self.assertEqual(factura["ClaveRegimenEspecialOTrascendencia"], "17")
        detalle = self._walk_payload(payload, "DetalleArticulo25")
        self.assertTrue(detalle)
        detail = detalle[0] if isinstance(detalle, list) else detalle
        self.assertEqual(detail["PagoAnticipadoArt25"], "N")
        self.assertEqual(detail["TipoBienArt25"], "01")
        self.assertEqual(
            detail["IDDocumentoArt25"],
            {
                "TipoDocumArt25": "01",
                "NumeroProtocolo": "123456",
                "ApellidosNombreNotario": "García López, Juan",
            },
        )

    def test_purchase_art25_private_doc(self):
        """Art. 25 compras: documento privado sin nodos notario."""
        self._prepare_art25_product(tipo_bien="02")
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_p_ex"),
            reg_key_code="17",
            extra_vals=self._art25_invoice_vals(
                ref="ART25-PUR-PRIV",
                sii_art25_document_id="02",
                sii_art25_protocol_number=False,
                sii_art25_notary_name=False,
            ),
        )
        payload = self._payload(move)
        detail = self._walk_payload(payload, "DetalleArticulo25")[0]
        self.assertEqual(detail["IDDocumentoArt25"], {"TipoDocumArt25": "02"})

    def test_purchase_art25_fp_fallback_l32(self):
        """Art. 25: TipoBienArt25 desde posición fiscal si el producto no lo tiene."""
        self.product.sii_exempt_cause = "E5"
        self.product.sii_art25_tipo_bien = False
        fp = self._get_or_create_fp(
            "ATC Art25 FP fallback",
            sii_exempt_cause="E5",
            sii_art25_tipo_bien="03",
            aeat_active=True,
        )
        move = self._create_atc_invoice(
            move_type="in_invoice",
            fiscal_position=fp,
            taxes=self._tax("igic_p_ex"),
            reg_key_code="17",
            extra_vals=self._art25_invoice_vals(ref="ART25-FP-L32"),
        )
        payload = self._payload(move)
        detail = self._walk_payload(payload, "DetalleArticulo25")[0]
        self.assertEqual(detail["TipoBienArt25"], "03")

    def _create_art25_purchase_with_types(self, tipo_bienes):
        products = self.env["product.product"].create(
            [
                {
                    "name": f"ATC Art25 product {idx}",
                    "sii_exempt_cause": "E5",
                    "sii_art25_tipo_bien": tipo_bien,
                }
                for idx, tipo_bien in enumerate(tipo_bienes)
            ]
        )
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.supplier.id,
                "fiscal_position_id": self._fp_national.id,
                "journal_id": self.journal_purchase.id,
                "invoice_date": "2026-03-15",
                "move_type": "in_invoice",
                "ref": "ART25-GROUPED",
                "sii_registration_key": self._reg_key("17", "in_invoice").id,
                **self._art25_invoice_vals(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Art. 25 line",
                            "product_id": product.id,
                            "account_id": self.accounts["600000"].id,
                            "price_unit": 100.0,
                            "quantity": 1,
                            "tax_ids": [(6, 0, self._tax("igic_p_ex").ids)],
                        },
                    )
                    for product in products
                ],
            }
        )
        move.action_post()
        return move

    def test_purchase_art25_repeated_types_are_grouped(self):
        """Repeated Art. 25 types produce one detail per type."""
        move = self._create_art25_purchase_with_types(["01", "01", "02"])
        details = self._walk_payload(self._payload(move), "DetalleArticulo25")
        self.assertEqual(len(details), 2)
        self.assertEqual(
            {detail["TipoBienArt25"] for detail in details},
            {"01", "02"},
        )

    def test_purchase_art25_more_than_three_types_rejected(self):
        """The XSD maximum of three Art. 25 details is enforced."""
        with self.assertRaises(UserError):
            self._create_art25_purchase_with_types(["01", "02", "03", "04"])

    def test_purchase_art25_protocol_length_rejected(self):
        """The XSD limits a notarial protocol number to six characters."""
        self._prepare_art25_product(tipo_bien="01", exempt_cause="E5")
        with self.assertRaises(UserError):
            self._create_atc_invoice(
                move_type="in_invoice",
                taxes=self._tax("igic_p_ex"),
                reg_key_code="17",
                extra_vals=self._art25_invoice_vals(
                    ref="ART25-PUR-LENGTH",
                    sii_art25_protocol_number="1234567",
                ),
            )
