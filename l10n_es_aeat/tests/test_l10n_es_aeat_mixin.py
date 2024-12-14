from unittest.mock import patch
from odoo.tests import common
from odoo_test_helper import FakeModelLoader
from odoo import fields, models
from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys
from odoo.exceptions import UserError

class TestAeatMixin(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        class AeatTestModel(models.Model):
            _name = "aeat.test.model"
            _inherit = "aeat.mixin"
            _description = "AEAT Test Model"
            name = fields.Char(string="Name", required=True)
            company_id = fields.Many2one("res.company", string="Company", required=True)

        cls.loader.update_registry((AeatTestModel,))
        cls.AeatTestModel = cls.env["aeat.test.model"]

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({
            "name": "Test Partner",
            "vat": "ES12345678Z",
            "aeat_simplified_invoice": False,
        })
        self.currency = self.env["res.currency"].search([("name", "=", "EUR")], limit=1)
        self.chart_template = self.env['account.chart.template'].create({
            "currency_id": self.currency.id,
            'name': 'Test Chart Template',
            "bank_account_code_prefix": "123",
            "cash_account_code_prefix": "456",
            "transfer_account_code_prefix": "789",
        })
        self.company = self.env["res.company"].create({
            "name": "Test Company",
            "chart_template_id": self.chart_template.id,
        })
        self.mixin = self.AeatTestModel.create({
            "name": "Test Mixin Record",
            "company_id": self.company.id,
        })

    def test_change_date_format(self):
        """Prueba para cambiar el formato de una fecha."""
        date = "2024-12-13"
        formatted_date = self.mixin._change_date_format(date)
        self.assertEqual(formatted_date, "13-12-2024")

    def test_get_document_fiscal_year(self):
        """Prueba para obtener el año fiscal."""
        with patch.object(type(self.mixin), "_get_document_fiscal_date", return_value="2024-12-13"):
            fiscal_year = self.mixin._get_document_fiscal_year()
            self.assertEqual(fiscal_year, 2024)

    def test_get_document_period(self):
        """Prueba para obtener el período fiscal."""
        with patch.object(type(self.mixin), "_get_document_fiscal_date", return_value="2024-12-13"):
            period = self.mixin._get_document_period()
            self.assertEqual(period, "12")

    def test_aeat_check_exceptions(self):
        """Prueba para verificar excepciones de validación."""
        with patch.object(type(self.mixin), "_aeat_get_partner", return_value=self.partner), \
             patch.object(type(self.mixin), "_get_aeat_country_code", return_value="ES"):
            self.partner.vat = "ES12345678Z"
            try:
                self.mixin._aeat_check_exceptions()
            except UserError:
                self.fail("Validación falló en un caso válido.")

            self.partner.vat = False
            with self.assertRaises(UserError) as cm:
                self.mixin._aeat_check_exceptions()
            self.assertIn("The partner has not a VAT configured", str(cm.exception))

    @patch("odoo.addons.l10n_es_aeat.models.aeat_mixin.AeatMixin._connect_params_aeat", return_value={
        "wsdl": "https://example.com/wsdl",
        "port_name": "TestPort",
        "address": "https://example.com/address",
    })
    @patch("odoo.addons.l10n_es_aeat.models.aeat_mixin.AeatMixin._bind_service", return_value=True)
    def test_connect_aeat(self, mock_bind_service, mock_connect_params_aeat):
        """Prueba de conexión a AEAT."""
        with patch("odoo.addons.l10n_es_aeat.models.aeat_mixin.AeatMixin._connect_aeat", return_value=True):
            result = self.mixin._connect_aeat("test_mapping_key")
            self.assertTrue(result)

    def test_round_by_keys(self):
        """Prueba para redondear valores específicos en una estructura."""
        data = {
            "key1": 3.7777,
            "nested": {
                "key2": 2.3333,
            },
            "list": [{"key1": 5.5555}],
        }
        round_by_keys(data, ["key1", "key2"], prec=2)
        self.assertEqual(data["key1"], 3.78)
        self.assertEqual(data["nested"]["key2"], 2.33)
        self.assertEqual(data["list"][0]["key1"], 5.56)
