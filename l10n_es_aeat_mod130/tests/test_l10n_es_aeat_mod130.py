# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging

from odoo import Command, exceptions

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
        invoice_sale = self._invoice_sale_create("2019-01-01")
        invoice_purchase = self._invoice_purchase_create("2019-01-01")
        # Unposted copies must not affect income or expenses.
        for invoice in (invoice_sale, invoice_purchase):
            self.assertEqual(invoice.payment_state, "not_paid")
            draft_invoice = invoice.copy(
                {"date": "2019-01-01", "invoice_date": "2019-01-01"}
            )
            cancelled_invoice = draft_invoice.copy(
                {"date": "2019-01-01", "invoice_date": "2019-01-01"}
            )
            cancelled_invoice.button_cancel()
            self.assertEqual(draft_invoice.state, "draft")
            self.assertEqual(cancelled_invoice.state, "cancel")
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

    def test_model_130_only_posted_withholdings(self):
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": self.journal_misc.id,
                "date": "2019-01-01",
                "line_ids": [
                    Command.create(
                        {"account_id": self.accounts["473000"].id, "debit": 100}
                    ),
                    Command.create(
                        {"account_id": self.accounts["475000"].id, "credit": 100}
                    ),
                ],
            }
        )
        draft_move = move.copy({"date": "2019-01-01"})
        cancelled_move = move.copy({"date": "2019-01-01"})
        cancelled_move.button_cancel()
        move.action_post()
        self.assertEqual(draft_move.state, "draft")
        self.assertEqual(cancelled_move.state, "cancel")
        model130 = self.env["l10n.es.aeat.mod130.report"].create(
            {
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2019,
                "period_type": "1T",
                "date_start": "2019-01-01",
                "date_end": "2019-03-31",
                "journal_id": self.journal_misc.id,
            }
        )
        model130.button_calculate()
        self.assertAlmostEqual(model130.casilla_06, 100, 2)
        draft_move.action_post()
        model130.button_recalculate()
        self.assertAlmostEqual(model130.casilla_06, 200, 2)
