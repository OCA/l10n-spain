# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.l10n_es_aeat_sii_oca.models.sii_mixin import SiiMixin


@tagged("post_install", "-at_install")
class TestL10nEsAtcSii(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner ATC",
                "vat": "DE123456788",  # NIF extranjero: IDType 02 → 04 en ATC
                "country_id": cls.env.ref("base.de").id,
            }
        )
        cls.atc_agency = cls.env.ref("l10n_es_aeat.aeat_tax_agency_canarias")
        # Factura mínima para pruebas unitarias
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
            }
        )
        cls.invoice.company_id.vat = "ESA12345674"
        # Clase del modelo para parchear métodos a nivel de modelo
        cls.account_move_model = type(cls.invoice)
        # Clase del mapa SII para parchear search
        cls.sii_map_model = type(cls.env["aeat.sii.map"])

    def test_01_parse_aeat_vat_info_id_type(self):
        """IDType '02' de NIF extranjero se convierte a '04' para la ATC."""
        # Contexto AEAT estándar
        country_code, identifier_type, identifier = self.partner._parse_aeat_vat_info()
        self.assertEqual(identifier_type, "02", "For AEAT, EU VAT should be 02")

        # Contexto ATC
        country_code, identifier_type, identifier = self.partner.with_context(
            is_canary_tax_agency=True
        )._parse_aeat_vat_info()
        self.assertEqual(identifier_type, "04", "For ATC, EU VAT must be 04")

    def test_02_get_aeat_header_version(self):
        """IDVersionSii: 1.1 en producción y 1.0 en modo prueba SII (ATC)."""
        with patch.object(
            self.account_move_model, "_get_sii_tax_agency"
        ) as mock_get_agency:
            mock_get_agency.return_value = self.atc_agency
            self.invoice.company_id.sii_test = False
            header = self.invoice._get_aeat_header()
            self.assertEqual(header.get("IDVersionSii"), "1.1")

            self.invoice.company_id.sii_test = True
            header_test = self.invoice._get_aeat_header()
            self.assertEqual(header_test.get("IDVersionSii"), "1.0")

    def test_03_sii_atc_replace_tax_keys_iva_to_igic(self):
        """Sustitución IVA → IGIC en DesgloseIVA y DetalleIVA."""
        invoice_dict = {
            "SuministroLRFacturasEmitidas": {
                "Cabecera": {"IDVersionSii": "1.0"},
                "RegistroLRFacturasEmitidas": {
                    "FacturaExpedida": {
                        "TipoDesglose": {
                            "DesgloseFactura": {
                                "Sujeta": {
                                    "NoExenta": {
                                        "TipoNoExenta": "S1",
                                        "DesgloseIVA": {
                                            "DetalleIVA": [
                                                {
                                                    "TipoImpositivo": "7.00",
                                                    "BaseImponible": "100.00",
                                                    "CuotaRepercutida": "7.00",
                                                }
                                            ]
                                        },
                                    }
                                }
                            }
                        }
                    }
                },
            }
        }

        replaced_dict = self.env["account.move"]._sii_atc_replace_tax_keys(invoice_dict)

        # Claves antiguas eliminadas
        factura_expedida = replaced_dict["SuministroLRFacturasEmitidas"][
            "RegistroLRFacturasEmitidas"
        ]["FacturaExpedida"]
        no_exenta = factura_expedida["TipoDesglose"]["DesgloseFactura"]["Sujeta"][
            "NoExenta"
        ]

        self.assertNotIn("DesgloseIVA", no_exenta)
        self.assertIn("DesgloseIGIC", no_exenta)

        desglose = no_exenta["DesgloseIGIC"]
        self.assertNotIn("DetalleIVA", desglose)
        self.assertIn("DetalleIGIC", desglose)

        # Valores conservados
        self.assertEqual(desglose["DetalleIGIC"][0]["TipoImpositivo"], "7.00")

    def test_03b_sii_atc_replace_tax_keys_articulo_9(self):
        """ImportePorArticulos7_14_Otros → ImportePorArticulos9_Otros."""
        invoice_dict = {
            "DesgloseFactura": {
                "NoSujeta": {
                    "ImportePorArticulos7_14_Otros": "200.00",
                    "ImporteTransmisionInmueblesSujetoAIVA": "0.00",
                }
            }
        }
        replaced = self.env["account.move"]._sii_atc_replace_tax_keys(invoice_dict)
        no_sujeta = replaced["DesgloseFactura"]["NoSujeta"]

        self.assertNotIn("ImportePorArticulos7_14_Otros", no_sujeta)
        self.assertIn("ImportePorArticulos9_Otros", no_sujeta)
        self.assertEqual(no_sujeta["ImportePorArticulos9_Otros"], "200.00")

    def test_03c_sii_atc_replace_tax_keys_inmuebles(self):
        """ImporteTransmisionInmueblesSujetoAIVA → AIGIC."""
        invoice_dict = {
            "DesgloseFactura": {
                "Sujeta": {
                    "ImporteTransmisionInmueblesSujetoAIVA": "150.00",
                }
            }
        }
        replaced = self.env["account.move"]._sii_atc_replace_tax_keys(invoice_dict)
        sujeta = replaced["DesgloseFactura"]["Sujeta"]

        self.assertNotIn("ImporteTransmisionInmueblesSujetoAIVA", sujeta)
        self.assertIn("ImporteTransmisionInmueblesSujetoAIGIC", sujeta)
        self.assertEqual(sujeta["ImporteTransmisionInmueblesSujetoAIGIC"], "150.00")

    def test_03d_sii_atc_replace_tax_keys_re_purge(self):
        """Nodos RecargoEquivalencia eliminados del esquema ATC."""
        invoice_dict = {
            "DesgloseFactura": {
                "Sujeta": {
                    "NoExenta": {
                        "TipoRecargoEquivalencia": "5.20",
                        "CuotaRecargoEquivalencia": "10.40",
                        "DesgloseIVA": {
                            "DetalleIVA": [
                                {
                                    "TipoImpositivo": "7.00",
                                    "BaseImponible": "200.00",
                                    "CuotaRepercutida": "14.00",
                                }
                            ]
                        },
                    }
                }
            }
        }
        replaced = self.env["account.move"]._sii_atc_replace_tax_keys(invoice_dict)
        no_exenta = replaced["DesgloseFactura"]["Sujeta"]["NoExenta"]

        self.assertNotIn("TipoRecargoEquivalencia", no_exenta)
        self.assertNotIn("CuotaRecargoEquivalencia", no_exenta)
        # Datos IGIC conservados
        self.assertIn("DesgloseIGIC", no_exenta)

    def test_03e_sii_atc_replace_tax_keys_list_and_tuple(self):
        """Listas y tuplas procesadas de forma recursiva."""
        invoice_dict = {
            "DesgloseIVA": [
                {"DetalleIVA": {"BaseImponible": "100.00"}},
                {"DetalleIVA": {"BaseImponible": "200.00"}},
            ]
        }
        replaced = self.env["account.move"]._sii_atc_replace_tax_keys(invoice_dict)
        self.assertIn("DesgloseIGIC", replaced)
        self.assertEqual(len(replaced["DesgloseIGIC"]), 2)
        self.assertIn("DetalleIGIC", replaced["DesgloseIGIC"][0])

    def test_03f_sii_atc_replace_tax_keys_no_change(self):
        """Claves no mapeadas pasan sin cambios."""
        input_dict = {
            "Cabecera": {"IDVersionSii": "1.0"},
            "RegistroLRFacturasEmitidas": {"some_field": "value"},
        }
        replaced = self.env["account.move"]._sii_atc_replace_tax_keys(input_dict)
        self.assertEqual(replaced, input_dict)

    def test_04_get_sii_identifier_context(self):
        """_get_sii_identifier inyecta contexto ATC para parseo de NIF."""
        with patch.object(
            self.account_move_model, "_get_sii_tax_agency"
        ) as mock_get_agency:
            mock_get_agency.return_value = self.atc_agency
            identifier = self.invoice._get_sii_identifier()
            self.assertTrue(identifier)

    # Nota: _get_aeat_invoice_dict_out/_in no se prueban aquí directamente
    # porque super() depende de datos contables complejos (diario, líneas…).
    # La transformación central (_sii_atc_replace_tax_keys) ya está cubierta
    # en tests 03a–03f. Las condiciones de despacho (agencia ATC + cancel)
    # siguen el mismo patrón validado en tests 02 y 04.

    def test_06_get_aeat_taxes_map_search_domain(self):
        """_get_aeat_taxes_map busca con dominio filtrado por agencia ATC."""
        with (
            patch.object(
                self.account_move_model, "_get_sii_tax_agency"
            ) as mock_get_agency,
            patch.object(self.sii_map_model, "search") as mock_search,
        ):
            mock_get_agency.return_value = self.atc_agency
            # MagicMock truthy (mapa encontrado)
            fake_map = MagicMock()
            fake_map.__bool__ = lambda self: True
            fake_map.__len__ = lambda self: 1
            fake_map.ids = [1]
            fake_map.map_lines.filtered.return_value = fake_map.map_lines
            fake_map.map_lines.tax_xmlid_ids = []
            mock_search.return_value = fake_map

            self.invoice._get_aeat_taxes_map(["SFESB"], "2025-01-01")

            # Dominio de búsqueda incluye agencia ATC
            self.assertTrue(mock_search.called, "search() must have been called")
            search_domain = mock_search.call_args[0][0]
            self.assertIn(
                ("tax_agency_id", "=", self.atc_agency.id),
                search_domain,
                "Search domain must filter by ATC agency",
            )

    def test_06b_get_aeat_taxes_map_fallback(self):
        """_get_aeat_taxes_map recurre al genérico si no hay mapa ATC."""
        with (
            patch.object(
                self.account_move_model, "_get_sii_tax_agency"
            ) as mock_get_agency,
            patch.object(self.sii_map_model, "search") as mock_search,
            patch.object(SiiMixin, "_get_aeat_taxes_map") as mock_super,
        ):
            mock_get_agency.return_value = self.atc_agency
            # Recordset vacío = sin mapa ATC
            mock_search.return_value = self.env["aeat.sii.map"]
            mock_super.return_value = self.env["account.tax"]

            self.invoice._get_aeat_taxes_map(["SFESB"], "2025-01-01")

            mock_super.assert_called_once_with(["SFESB"], "2025-01-01")

    def test_06c_get_aeat_taxes_map_non_atc(self):
        """_get_aeat_taxes_map delega en super para agencias no ATC."""
        with (
            patch.object(
                self.account_move_model, "_get_sii_tax_agency"
            ) as mock_get_agency,
            patch.object(SiiMixin, "_get_aeat_taxes_map") as mock_super,
        ):
            mock_get_agency.return_value = self.env["aeat.tax.agency"].browse()

            self.invoice._get_aeat_taxes_map(["SFESB"], "2025-01-01")

            mock_super.assert_called_once()

    def test_07_connect_params_sii_test_mode(self):
        """_connect_params_sii usa endpoint cautela en modo prueba (ATC)."""
        company = self.invoice.company_id
        company.sii_test = True

        result = self.atc_agency._connect_params_sii("out_invoice", company)

        self.assertIn("wsdl", result, "WSDL must be present in result")
        self.assertTrue(
            result["wsdl"].endswith("?wsdl"),
            "zeep WSDL URL must include ?wsdl suffix for ATC CXF",
        )
        self.assertNotIn(
            "?wsdl",
            result["address"],
            "SOAP address must not include ?wsdl suffix",
        )
        self.assertIn(
            "middlewarecaut",
            result["wsdl"],
            "ATC test mode WSDL should use cautela endpoint",
        )
        self.assertEqual(result["address"] + "?wsdl", result["wsdl"])

    def test_07b_connect_params_sii_production_mode(self):
        """_connect_params_sii mantiene WSDL de producción fuera de prueba."""
        company = self.invoice.company_id
        company.sii_test = False

        result = self.atc_agency._connect_params_sii("out_invoice", company)

        self.assertIn("wsdl", result)
        self.assertTrue(result["wsdl"].endswith("?wsdl"))
        self.assertIn("sede.gobiernodecanarias.org", result["wsdl"])
        self.assertIn("/middleware/services/sii/", result["wsdl"])
        self.assertNotIn("middlewarecaut", result["wsdl"])
        self.assertEqual(
            result["wsdl"],
            self.atc_agency.sii_wsdl_out + "?wsdl",
        )
        address = result.get("address") or ""
        self.assertNotIn(
            "middlewarecaut",
            address,
            "Production mode should NOT use cautela endpoint",
        )

    def test_07c_connect_params_sii_atc_domain(self):
        """_connect_params_sii devuelve dominio WSDL propio de la ATC."""
        company = self.invoice.company_id
        result = self.atc_agency._connect_params_sii("out_invoice", company)

        self.assertIn("wsdl", result)
        # WSDL ATC apunta al dominio del Gobierno de Canarias
        self.assertIn(
            "gobiernodecanarias",
            result["wsdl"],
            "ATC WSDL must point to gobiernodecanarias.org",
        )

    def test_08_sfrbi_purchase_breakdown(self):
        """Impuestos SFRBI en compras rellenan DesgloseIVA con BienInversion."""
        tax = self.env["account.tax"].create(
            {
                "name": "Test IGIC investment",
                "amount_type": "percent",
                "amount": 7.0,
                "type_tax_use": "purchase",
            }
        )
        invoice = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "company_id": self.invoice.company_id.id,
            }
        )
        invoice.company_id.tax_agency_id = self.atc_agency

        def fake_get_aeat_taxes_map(codes, date):
            if "SFRBI" in codes:
                return tax
            return self.env["account.tax"]

        with (
            patch.object(
                type(invoice),
                "_get_aeat_tax_info",
                return_value={
                    1: {
                        "tax": tax,
                        "amount": 7.0,
                        "base": 100.0,
                        "deductible_amount": 7.0,
                    }
                },
            ),
            patch.object(
                type(invoice),
                "_get_aeat_taxes_map",
                side_effect=fake_get_aeat_taxes_map,
            ),
        ):
            desglose, tax_amount, _not_in = invoice._get_sii_in_taxes()
        self.assertIn("DesgloseIVA", desglose)
        detalle = desglose["DesgloseIVA"]["DetalleIVA"]
        self.assertEqual(len(detalle), 1)
        self.assertEqual(detalle[0]["BienInversion"], "S")
        self.assertEqual(tax_amount, 7.0)
