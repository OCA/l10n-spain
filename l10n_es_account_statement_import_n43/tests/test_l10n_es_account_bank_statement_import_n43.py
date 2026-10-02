# Copyright 2016,2018,2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.modules.module import get_module_resource
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class L10nEsAccountStatementImportN43(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.company.chart_template_id:
            # Load a CoA if there's none in current company
            coa = cls.env.ref("l10n_generic_coa.configurable_chart_template", False)
            if not coa:
                # Load the first available CoA
                coa = cls.env["account.chart.template"].search(
                    [("visible", "=", True)], limit=1
                )
            coa.try_loading(company=cls.env.company, install_demo=False)
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test partner N43", "company_id": cls.env.company.id}
        )
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "000000000000000000000000",
                "company_id": cls.env.company.id,
                "partner_id": cls.env.company.partner_id.id,
            }
        )
        cls.partner_bank_01 = cls.env["res.partner.bank"].create(
            {
                "acc_number": "000000000000001000000000",
                "company_id": cls.env.company.id,
                "partner_id": cls.env.company.partner_id.id,
            }
        )
        eur_currency = cls.env.ref("base.EUR")
        cls.journal = cls.env["account.journal"].create(
            {
                "type": "bank",
                "name": "Test N43 bank",
                "code": "BN43",
                "company_id": cls.env.company.id,
                "bank_account_id": cls.partner_bank.id,
                "currency_id": eur_currency.id,
            }
        )
        cls.journal_01 = cls.env["account.journal"].create(
            {
                "type": "bank",
                "name": "Test N43 bank",
                "code": "BN432",
                "company_id": cls.env.company.id,
                "bank_account_id": cls.partner_bank_01.id,
                "currency_id": eur_currency.id,
            }
        )
        n43_file_path = get_module_resource(
            "l10n_es_account_statement_import_n43", "tests", "test.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        cls.import_wizard = (
            cls.env["account.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test"})
        )

    def test_import_n43_multi(self):
        n43_file_path = get_module_resource(
            "l10n_es_account_statement_import_n43", "tests", "testmulti.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        self.import_wizard.statement_file = n43_file
        action = self.import_wizard.with_context(journal_id=False).import_file_button()
        self.assertTrue(action)
        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)]
        )
        self.assertEqual(1, len(statements))
        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal_01.id)]
        )
        self.assertEqual(1, len(statements))

    def test_import_n43(self):
        action = self.import_wizard.import_file_button()
        self.assertTrue(action)
        statement_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        statement = statement_lines[2].statement_id
        self.assertEqual(len(statement_lines), 3)
        self.assertTrue(
            statement_lines.filtered(lambda st: str(st.date) == "2016-05-25")
        )
        self.assertTrue(
            statement_lines.filtered(lambda st: str(st.date) == "2016-05-16")
        )
        self.assertTrue(
            statement_lines.filtered(lambda st: str(st.date) == "2016-05-12")
        )
        self.assertEqual(statement_lines[0].date, fields.Date.to_date("2016-05-25"))
        self.assertAlmostEqual(statement.balance_start, 0, 2)
        self.assertAlmostEqual(statement.balance_end, 101.96, 2)
        self.assertEqual(statement_lines[2].partner_id, self.partner)
        self.assertEqual(statement_lines[2].ref, "000975737917")
        self.assertEqual(statement_lines[1].ref, "/")
        self.assertEqual(statement_lines[0].ref, "5540014210128010")

    def test_sabadell_incoming_partner_detection(self):
        """Test that Sabadell incoming transfers detect partner from
        'NOMBRE DEL ORDENANTE' prefix in concept 01."""
        partner = self.env["res.partner"].create(
            {"name": "TEST EMPRESA SL", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        # Simulate Sabadell incoming transfer concept record:
        # First 35 chars: "NOMBRE DEL ORDENANTE    TEST EMP"
        # Remaining:       "RESA,S.L."
        conceptos = {
            "01": ("NOMBRE DEL ORDENANTE    TEST EMP", "RESA,S.L."),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_incoming_partner_no_suffix(self):
        """Test Sabadell incoming detection for a person (no legal suffix)."""
        partner = self.env["res.partner"].create(
            {"name": "MARIA CARMEN SERRAT FREIXA", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        conceptos = {
            "01": ("NOMBRE DEL ORDENANTE    MARIA CARME", "N SERRAT FREIXA"),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_ordenante_prefix(self):
        """Test 'ORDENANTE DE LA TRANSFERENCIA' prefix with colon separator."""
        partner = self.env["res.partner"].create(
            {"name": "ACME DISTRIBUCIONES SL", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        conceptos = {
            "01": (
                "ORDENANTE DE LA TRANSFERENCIA :",
                " ACME DISTRIBUCIONES S.L.",
            ),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_transferenc_prefix(self):
        """Test 'TRANSFERENC. DE' prefix."""
        partner = self.env["res.partner"].create(
            {"name": "PEDRO MARTINEZ SANCHEZ", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        conceptos = {
            "01": ("TRANSFERENC. DE PEDRO MARTINEZ SAN", "CHEZ"),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_beneficiario_transferencia_prefix(self):
        """Test 'BENEFICIARIO DE LA TRANSFERENCIA' prefix (outgoing transfer)."""
        partner = self.env["res.partner"].create(
            {"name": "ANA GARCIA LOPEZ", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        conceptos = {
            "01": (
                "BENEFICIARIO DE LA TRANSFERENCIA :",
                "      ANA GARCIA LOPEZ",
            ),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_beneficiario_prefix(self):
        """Test 'BENEFICIARIO' prefix (short form, outgoing transfer)."""
        partner = self.env["res.partner"].create(
            {"name": "CARLOS RUIZ MARTINEZ", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        conceptos = {
            "01": ("BENEFICIARIO CARLOS RUIZ MARTINEZ", ""),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_core_sepa_prefix(self):
        """Test 'CORE' prefix (SEPA direct debit) — name glued without space."""
        partner = self.env["res.partner"].create(
            {"name": "Suministros Eolicos del Norte SL", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        conceptos = {
            "01": ("CORESuministros Eolicos del Norte", " SL"),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_word_boundary_match(self):
        """Test word boundary regex fallback finds partner by unique word."""
        partner = self.env["res.partner"].create(
            {
                "name": "FUNDACION GREENFIELD EDUCATIVA SL",
                "company_id": self.env.company.id,
            }
        )
        wizard = self.env["account.statement.import"]
        # Name truncated — ilike on full extracted text won't match
        conceptos = {
            "01": (
                "NOMBRE DEL ORDENANTE    FUNDACION G",
                "REENFIELD EDUCATIVA DE ESPA",
            ),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertEqual(result, partner)

    def test_sabadell_word_boundary_no_substring(self):
        """Test word boundary regex does NOT match substrings.

        MARTIN should not match MARTINEZA — word boundaries prevent it.
        """
        self.env["res.partner"].create(
            {"name": "MARTINEZA, S.L.", "company_id": self.env.company.id}
        )
        wizard = self.env["account.statement.import"]
        conceptos = {
            "01": (
                "NOMBRE DEL ORDENANTE    MARTIN ROM",
                "ERO LOPEZ",
            ),
        }
        result = wizard._get_n43_partner_from_sabadell(conceptos)
        self.assertFalse(result)

    def test_clean_partner_name_suffix(self):
        """Test legal suffix removal for partner name matching."""
        wizard = self.env["account.statement.import"]
        self.assertEqual(
            wizard._clean_partner_name_suffix("VILA FOPE,S.L."), "VILA FOPE"
        )
        self.assertEqual(wizard._clean_partner_name_suffix("EMPRESA S.A."), "EMPRESA")
        self.assertEqual(wizard._clean_partner_name_suffix("CORP SLU"), "CORP")
        self.assertEqual(
            wizard._clean_partner_name_suffix("MARIA CARMEN SERRAT"),
            "MARIA CARMEN SERRAT",
        )

    def test_import_n43_fecha_oper(self):
        self.journal.n43_date_type = "fecha_oper"
        action = self.import_wizard.import_file_button()
        self.assertTrue(action)
        statements = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(statements[0].date, fields.Date.to_date("2016-05-26"))
