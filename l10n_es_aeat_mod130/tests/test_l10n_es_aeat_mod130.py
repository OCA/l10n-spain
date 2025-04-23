# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging

from odoo import exceptions

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.130")


class TestL10nEsAeatMod130Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21B": (1000, 0),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IVA21_BC": (900, 0),
    }

    def test_model_130(self):
        self._invoice_sale_create("2019-01-01")
        self._invoice_purchase_create("2019-01-01")
        # Create model
        model130 = self.env["l10n.es.aeat.mod130.report"].create(
            {
                "name": "9990000000130",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2019,
                "period_type": "1T",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "journal_id": self.journal_misc.id,
                "counterpart_account_id": self.accounts["475000"].id,
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 130 1T 2015")
        model130.button_calculate()
        self.assertEqual(model130.tipo_declaracion, "I")
        self.assertAlmostEqual(model130.casilla_01, 1000, 2)
        self.assertAlmostEqual(model130.real_expenses, 900, 2)
        self.assertAlmostEqual(model130.non_justified_expenses, 5, 2)
        self.assertAlmostEqual(model130.casilla_02, 905, 2)
        self.assertAlmostEqual(model130.casilla_03, 95, 2)
        self.assertAlmostEqual(model130.casilla_04, 19, 2)
        self.assertAlmostEqual(model130.casilla_05, 0, 2)
        self.assertAlmostEqual(model130.casilla_06, 0, 2)
        self.assertAlmostEqual(model130.casilla_07, 19, 2)
        self.assertAlmostEqual(model130.casilla_12, 19, 2)
        self.assertAlmostEqual(model130.casilla_13, 0, 2)
        self.assertAlmostEqual(model130.casilla_14, 19, 2)
        self.assertAlmostEqual(model130.casilla_15, 0, 2)
        self.assertAlmostEqual(model130.casilla_16, 0, 2)  # Has no loan
        self.assertAlmostEqual(model130.casilla_17, 19, 2)
        self.assertAlmostEqual(model130.casilla_18, 0, 2)
        # Confirm for checking no errors
        model130.button_confirm()
        # Test second trimester
        model130_2t = model130.copy(
            {
                "name": "9990000001130",
                "period_type": "2T",
                "date_start": "2019-04-01",
                "date_end": "2019-06-30",
            }
        )
        self.taxes_sale["S_IVA21B"] = (300,)
        self._invoice_sale_create("2019-04-01")
        model130_2t.button_calculate()
        self.assertAlmostEqual(model130_2t.casilla_01, 1300, 2)
        self.assertAlmostEqual(model130_2t.real_expenses, 900, 2)
        self.assertAlmostEqual(model130_2t.non_justified_expenses, 20, 2)
        self.assertAlmostEqual(model130_2t.casilla_02, 920, 2)
        self.assertAlmostEqual(model130_2t.casilla_03, 380, 2)
        self.assertAlmostEqual(model130_2t.casilla_04, 76, 2)
        self.assertAlmostEqual(model130_2t.casilla_05, 19, 2)
        self.assertAlmostEqual(model130_2t.casilla_06, 0, 2)
        self.assertAlmostEqual(model130_2t.casilla_07, 57, 2)
        self.assertAlmostEqual(model130_2t.casilla_12, 57, 2)
        self.assertAlmostEqual(model130_2t.casilla_13, 0, 2)
        self.assertAlmostEqual(model130_2t.casilla_14, 57, 2)
        self.assertAlmostEqual(model130_2t.casilla_15, 0, 2)
        self.assertAlmostEqual(model130_2t.casilla_16, 0, 2)  # Has no loan
        self.assertAlmostEqual(model130_2t.casilla_17, 57, 2)
        self.assertAlmostEqual(model130_2t.casilla_18, 0, 2)
        # Test has loan
        model130_has_loan = model130.copy(
            {
                "name": "9990000002130",
                "has_prestamo": True,
                "activity_type": "other",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
            }
        )
        model130_has_loan.button_calculate()
        self.assertAlmostEqual(model130_has_loan.casilla_16, 1.9, 2)
        # Test has loan activity is primary
        model130_has_loan2 = model130.copy(
            {
                "name": "9990000003130",
                "has_prestamo": True,
                "activity_type": "primary",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
            }
        )
        with self.assertRaises(exceptions.UserError):
            model130_has_loan2.button_calculate()
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {
                "name": "test_export_to_boe.txt",
            }
        )
        export_config_xml_ids = ["l10n_es_aeat_mod130.aeat_mod130_export_config"]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(export_to_boe._export_config(model130, export_config))

        # Test partner account at AEAT
        model130_account_aeat = model130.copy(
            {
                "name": "9990000004130",
                "activity_type": "other",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "use_aeat_account": True,
            }
        )
        model130_account_aeat.button_calculate()
        self.assertEqual(model130_account_aeat.tipo_declaracion, "G")

        # Test Spanish bank account debit declaration
        model130_es_bank_account = model130.copy(
            {
                "name": "9990000005130",
                "activity_type": "other",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "use_aeat_account": False,
            }
        )
        model130_es_bank_account.partner_bank_id = self.customer_bank.id
        model130_es_bank_account.button_calculate()
        self.assertEqual(model130_es_bank_account.tipo_declaracion, "U")
        self.assertEqual(model130_es_bank_account.marca_sepa, "1")

        # Test European, but not Spanish, bank account debit declaration
        model130_eu_bank_account = model130.copy(
            {
                "name": "9990000006130",
                "activity_type": "other",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "use_aeat_account": False,
            }
        )
        Bank = self.env["res.bank"]
        bic = "PSSTFRPPXXX"
        bank = Bank.create(
            {
                "name": "LA BANQUE POSTALE",
                "country": self.env.ref("base.fr").id,
                "bic": bic,
            }
        )
        bank_acc = self.env["res.partner.bank"].create(
            {
                "acc_number": "FR20 1242 1242 1242 1242 1242 124",
                "partner_id": self.customer.id,
                "bank_id": bank.id,
            }
        )
        model130_eu_bank_account.partner_bank_id = bank_acc.id
        model130_eu_bank_account._compute_marca_sepa()
        model130_eu_bank_account.button_calculate()
        self.assertEqual(model130_eu_bank_account.tipo_declaracion, "U")
        self.assertEqual(model130_eu_bank_account.marca_sepa, "2")

        # Test non European bank account debit declaration
        model130_non_eu_bank_account = model130.copy(
            {
                "name": "9990000007130",
                "activity_type": "other",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "use_aeat_account": False,
            }
        )
        bic = "JPMGUS33XXX"
        bank = Bank.create(
            {
                "name": "JPMorgan Chase & Co",
                "country": self.env.ref("base.us").id,
                "bic": bic,
            }
        )
        bank_acc = self.env["res.partner.bank"].create(
            {
                "acc_number": "1234567890",
                "partner_id": self.customer.id,
                "bank_id": bank.id,
            }
        )
        model130_non_eu_bank_account.partner_bank_id = bank_acc.id
        model130_non_eu_bank_account.button_calculate()
        self.assertEqual(model130_non_eu_bank_account.tipo_declaracion, "I")
        self.assertEqual(model130_non_eu_bank_account.marca_sepa, "0")

        # Test compensate result
        model130_comp_result = model130.copy(
            {
                "name": "9990000008130",
                "activity_type": "other",
                "period_type": "1T",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "use_aeat_account": False,
            }
        )
        self.taxes_purchase["P_IVA21_BC"] = (1200,)
        self._invoice_purchase_create("2019-01-01")
        model130_comp_result.button_calculate()
        self.assertEqual(model130_comp_result.tipo_declaracion, "N")

        # Test negative result
        model130_neg_result = model130.copy(
            {
                "name": "9990000009130",
                "activity_type": "other",
                "period_type": "1T",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "use_aeat_account": False,
                "casilla_18": 2000.0,
            }
        )
        self.taxes_purchase["P_IVA21_BC"] = (1200,)
        self._invoice_purchase_create("2019-01-01")
        model130_neg_result.button_calculate()
        self.assertEqual(model130_neg_result.tipo_declaracion, "B")

        test_marca_sepa = model130.copy(
            {
                "name": "9990000010130",
                "activity_type": "other",
                "period_type": "1T",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "use_aeat_account": True,
            }
        )
        test_marca_sepa._compute_marca_sepa()
        self.assertEqual(test_marca_sepa.marca_sepa, "0")
