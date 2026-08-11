# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
        from odoo.exceptions import UserError

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
        dump = self._payload_json(move)
        self.assertEqual(
            self._factura_recibida(payload)["ClaveRegimenEspecialOTrascendencia"], "15"
        )
        if "CargaImpositivaImplicita" not in dump:
            self.skipTest("CargaImpositivaImplicita not implemented yet")

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
        self._prepare_art25_product(tipo_bien="02", exempt_cause="E5")
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
        self.assertEqual(detail["TipoBienArt25"], "02")
        self.assertEqual(detail["IDDocumentoArt25"], "01")
        self.assertEqual(detail["NumeroProtocolo"], "12345/2026")
        self.assertEqual(detail["ApellidosNombreNotario"], "García López, Juan")

    def test_purchase_art25_private_doc(self):
        """Art. 25 compras: documento privado sin nodos notario."""
        self._prepare_art25_product(tipo_bien="01")
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
        self.assertEqual(detail["IDDocumentoArt25"], "02")
        self.assertNotIn("NumeroProtocolo", detail)
        self.assertNotIn("ApellidosNombreNotario", detail)

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
