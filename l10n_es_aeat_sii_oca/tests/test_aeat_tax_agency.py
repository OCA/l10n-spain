# Copyright 2026 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged

NAVARRA_WSDL_OUT = "https://sii.navarra.example/out"
NAVARRA_WSDL_IN = "https://sii.navarra.example/in"
NAVARRA_WSDL_OUT_TEST = "https://sii-test.navarra.example/out"
NAVARRA_WSDL_IN_TEST = "https://sii-test.navarra.example/in"

MAPPING_CASES = (
    ("out_invoice", "sii_wsdl_out", "SuministroFactEmitidas"),
    ("out_refund", "sii_wsdl_out", "SuministroFactEmitidas"),
    ("in_invoice", "sii_wsdl_in", "SuministroFactRecibidas"),
    ("in_refund", "sii_wsdl_in", "SuministroFactRecibidas"),
)


@tagged("post_install", "-at_install")
class TestAeatTaxAgency(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.agency_navarra = cls.env.ref("l10n_es_aeat.aeat_tax_agency_navarra")
        cls.agency_spain = cls.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        cls.agency_navarra.write(
            {
                "sii_wsdl_out": NAVARRA_WSDL_OUT,
                "sii_wsdl_in": NAVARRA_WSDL_IN,
                "sii_wsdl_out_test_address": False,
                "sii_wsdl_in_test_address": False,
            }
        )

    def _connect_params(self, agency, mapping_key, sii_test):
        self.company.sii_test = sii_test
        return agency._connect_params_sii(mapping_key, self.company)

    def test_navarra_production_uses_spain_wsdl_and_navarra_address(self):
        for mapping_key, wsdl_field, port_name in MAPPING_CASES:
            with self.subTest(mapping_key=mapping_key):
                params = self._connect_params(
                    self.agency_navarra, mapping_key, sii_test=False
                )
                self.assertEqual(params["wsdl"], getattr(self.agency_spain, wsdl_field))
                self.assertEqual(
                    params["address"], getattr(self.agency_navarra, wsdl_field)
                )
                self.assertNotEqual(params["wsdl"], params["address"])
                self.assertEqual(params["port_name"], port_name)

    def test_navarra_test_without_test_address_appends_pruebas(self):
        for mapping_key, wsdl_field, port_name in MAPPING_CASES:
            with self.subTest(mapping_key=mapping_key):
                params = self._connect_params(
                    self.agency_navarra, mapping_key, sii_test=True
                )
                self.assertEqual(params["wsdl"], getattr(self.agency_spain, wsdl_field))
                self.assertEqual(
                    params["address"], getattr(self.agency_navarra, wsdl_field)
                )
                self.assertEqual(params["port_name"], port_name + "Pruebas")

    def test_navarra_test_with_test_address_keeps_port_name(self):
        self.agency_navarra.write(
            {
                "sii_wsdl_out_test_address": NAVARRA_WSDL_OUT_TEST,
                "sii_wsdl_in_test_address": NAVARRA_WSDL_IN_TEST,
            }
        )
        for mapping_key, wsdl_field, port_name in MAPPING_CASES:
            with self.subTest(mapping_key=mapping_key):
                params = self._connect_params(
                    self.agency_navarra, mapping_key, sii_test=True
                )
                self.assertEqual(params["wsdl"], getattr(self.agency_spain, wsdl_field))
                self.assertEqual(
                    params["address"], getattr(self.agency_navarra, wsdl_field)
                )
                self.assertEqual(params["port_name"], port_name)

    def test_other_agency_keeps_standard_sii_params(self):
        params = self._connect_params(self.agency_spain, "out_invoice", sii_test=False)
        self.assertEqual(params["wsdl"], self.agency_spain.sii_wsdl_out)
        self.assertFalse(params["address"])
        self.assertEqual(params["port_name"], "SuministroFactEmitidas")
