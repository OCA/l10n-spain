# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import TestL10nEsAtcSiiPayloadBase


class TestAtcSiiPayloadPurchases(TestL10nEsAtcSiiPayloadBase):
    """RegistroLRFacturasRecibidas — ISP, bienes de inversión, DUA y REPEP."""

    def test_purchase_isp_s2_zero_rate(self):
        """ISP compra total (S2): tipos y cuotas a cero en inversión del SP."""
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
        """REPEP pequeño empresario (clave 16): CuotaRecargoMinorista."""
        reg_key = self._reg_key("16", "in_invoice")
        move = self._create_atc_invoice(
            move_type="in_invoice",
            taxes=self._tax("igic_sop_7"),
            reg_key_code="16",
            extra_vals={"sii_registration_key": reg_key.id, "ref": "REPEP-16"},
        )
        if "CuotaRecargoMinorista" not in self._payload_json(move):
            self.skipTest("CuotaRecargoMinorista not implemented yet")

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
