# Copyright 2017 ForgeFlow <contact@forgeflow.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging

from odoo import _
from odoo.tests.common import tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.349")


@tagged("post_install", "-at_install")
class TestL10nEsAeatMod349Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {
        "S_IVA0_IC": (2400, 0),
    }
    taxes_purchase = {
        "P_IVA21_IC_BC": (150, 0),
        "P_IVA21_IC_BC//2": (150, 0),
    }

    @classmethod
    def _invoice_refund(cls, invoice, dt, price_unit=None):
        _logger.debug(
            "Refund {} invoice: date = {}: price_unit = {}".format(
                invoice.move_type, dt, price_unit or 150.0
            )
        )
        default_values_list = [
            {"date": dt, "invoice_date": dt, "invoice_payment_term_id": None}
        ]
        inv = invoice.with_user(cls.billing_user)._reverse_moves(default_values_list)
        if price_unit is not None:
            for line in inv.invoice_line_ids:
                line.price_unit = price_unit
        inv.action_post()
        if cls.debug:
            cls._print_move_lines(inv.line_ids)
        return inv

    def test_model_349(self):
        # Add some test data
        self.customer.write(
            {"vat": "BE0411905847", "country_id": self.env.ref("base.be").id}
        )
        self.supplier.write(
            {"vat": "BG0000100159", "country_id": self.env.ref("base.bg").id}
        )
        # Data for 1T 2017
        # Purchase invoices
        p1 = self._invoice_purchase_create("2017-01-01")
        p2 = self._invoice_purchase_create("2017-01-02")
        self._invoice_refund(p2, "2017-01-02")
        # Sale invoices
        s1 = self._invoice_sale_create("2017-01-01")
        s2 = self._invoice_sale_create("2017-01-02")
        self._invoice_refund(s2, "2017-01-02")
        # Create model
        model349_model = self.env["l10n.es.aeat.mod349.report"].with_user(
            self.account_manager
        )
        model349 = model349_model.create(
            {
                "name": "3490000000001",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "1T",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 1T 2017")
        model349.button_calculate()
        self.assertEqual(model349.total_partner_records, 2)
        # p1 + p2 -p3 + s1 + s2 - s3 = 2400 + 2400 - 2400 + 300 + 300 - 300
        self.assertEqual(model349.total_partner_records_amount, 2700.00)
        self.assertEqual(model349.total_partner_refunds, 0)
        self.assertEqual(model349.total_partner_refunds_amount, 0.0)
        a_record = model349.partner_record_ids.filtered(
            lambda x: x.operation_key == "A"
        )
        self.assertEqual(len(a_record), 1)
        self.assertEqual(len(a_record.record_detail_ids), 6)
        self.assertEqual(a_record.partner_vat, self.supplier.vat)
        self.assertEqual(a_record.country_id, self.supplier.country_id)
        # p1 + p2 - p3 = 300 + 300 - 300
        self.assertEqual(a_record.total_operation_amount, 300)
        e_record = model349.partner_record_ids.filtered(
            lambda x: x.operation_key == "E"
        )
        self.assertEqual(len(e_record), 1)
        self.assertEqual(len(e_record.record_detail_ids), 3)
        self.assertEqual(e_record.partner_vat, self.customer.vat)
        self.assertEqual(e_record.country_id, self.customer.country_id)
        # s1 + s2 - s3 = 2400 + 2400 - 2400
        self.assertEqual(e_record.total_operation_amount, 2400)
        # Now we delete detailed records to see if totals are recomputed
        model349.partner_record_detail_ids.filtered(lambda x: x.move_id == p1).unlink()
        self.assertEqual(a_record.total_operation_amount, 0)
        model349.partner_record_detail_ids.filtered(lambda x: x.move_id == s1).unlink()
        self.assertEqual(e_record.total_operation_amount, 0)
        # Create a complementary presentation for 1T 2017. We expect the
        #  application to propose the records that were not included in the
        # first presentation.
        model349_c = model349_model.create(
            {
                "name": "3490000000002",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "C",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "1T",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
                "previous_number": model349.name,
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 1T 2017 - complementary")
        model349_c.button_calculate()
        e_record = model349_c.partner_record_ids.filtered(
            lambda x: x.operation_key == "E"
        )
        self.assertEqual(len(e_record), 1)
        self.assertEqual(e_record.total_operation_amount, 2400)
        a_record = model349_c.partner_record_ids.filtered(
            lambda x: x.operation_key == "A"
        )
        self.assertEqual(len(a_record), 1)
        self.assertEqual(a_record.total_operation_amount, 300)
        # Create a substitutive presentation for 1T 2017. We expect that all
        # records for 1T are proposed.
        model349_s = model349_model.create(
            {
                "name": "3490000000003",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "S",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "1T",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
                "previous_number": model349.name,
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 1T 2017 - substitutive")
        model349_s.button_calculate()
        e_record = model349_s.partner_record_ids.filtered(
            lambda x: x.operation_key == "E"
        )
        self.assertEqual(e_record.total_operation_amount, 2400)
        a_record = model349_s.partner_record_ids.filtered(
            lambda x: x.operation_key == "A"
        )
        self.assertEqual(a_record.total_operation_amount, 300)
        # Create a substitutive presentation for 2T 2017.
        # We create a refund of p1, and a new sale
        self._invoice_refund(p1, "2017-04-01")
        self._invoice_sale_create("2017-04-01")
        model349_2t = model349_model.create(
            {
                "name": "3490000000004",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "2T",
                "date_start": "2017-04-01",
                "date_end": "2017-06-30",
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 2T 2017")
        model349_2t.button_calculate()
        self.assertEqual(model349_2t.total_partner_records, 1)
        self.assertEqual(model349_2t.total_partner_refunds, 1)
        self.assertEqual(model349_2t.total_partner_refunds_amount, 300)
        e_record = model349_2t.partner_record_ids.filtered(
            lambda x: x.operation_key == "E"
        )
        self.assertEqual(e_record.total_operation_amount, 2400)
        a_records = model349_2t.partner_record_ids.filtered(
            lambda x: x.operation_key == "A"
        )
        self.assertEqual(len(a_records), 0)
        e_refunds = model349_2t.partner_refund_ids.filtered(
            lambda x: x.operation_key == "E"
        )
        self.assertEqual(len(e_refunds), 0)
        a_refund = model349_2t.partner_refund_ids.filtered(
            lambda x: x.operation_key == "A"
        )
        self.assertEqual(len(a_refund), 1)
        self.assertEqual(len(a_refund.refund_detail_ids), 2)
        self.assertEqual(a_refund.total_origin_amount, 300)
        self.assertEqual(a_refund.total_operation_amount, 0)
        self.assertEqual(a_refund.period_type, model349_s.period_type)
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_config_xml_ids = [
            "l10n_es_aeat_mod349.aeat_mod349_main_export_config",
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(export_to_boe._export_config(model349, export_config))
        # Test report printing
        self.env.ref("l10n_es_aeat_mod349.act_report_aeat_mod349_pdf")._render(
            "l10n_es_aeat_mod349.report_l10n_es_mod349_pdf", model349.ids, {}
        )

    def test_model_349_with_intermediate_periods(self):
        # Create vendor bill and 2 refunds in different periods
        inv = self._invoice_purchase_create("2017-01-01")
        self._invoice_refund(inv, "2017-02-01", price_unit=50.0)
        self._invoice_refund(inv, "2017-03-01", price_unit=50.0)
        # Create model
        model349_model = self.env["l10n.es.aeat.mod349.report"].with_user(
            self.account_manager
        )
        model349_1 = model349_model.create(
            {
                "name": "3490000000001",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "01",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 January 2017")
        model349_1.button_calculate()
        self.assertEqual(model349_1.total_partner_records, 1)
        self.assertEqual(model349_1.partner_record_ids.total_operation_amount, 300)

        model349_2 = model349_model.create(
            {
                "name": "3490000000002",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "02",
                "date_start": "2017-02-01",
                "date_end": "2017-02-28",
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 February 2017")
        model349_2.button_calculate()
        self.assertEqual(model349_2.total_partner_records, 0)
        self.assertEqual(model349_2.total_partner_refunds, 1)
        self.assertEqual(model349_2.partner_refund_ids.total_origin_amount, 300)
        self.assertEqual(model349_2.partner_refund_ids.total_operation_amount, 200)

        model349_3 = model349_model.create(
            {
                "name": "3490000000003",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "03",
                "date_start": "2017-03-01",
                "date_end": "2017-03-31",
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 March 2017")
        model349_3.button_calculate()
        self.assertEqual(model349_3.total_partner_records, 0)
        self.assertEqual(model349_3.total_partner_refunds, 1)
        self.assertEqual(model349_3.partner_refund_ids.total_origin_amount, 200)
        self.assertEqual(model349_3.partner_refund_ids.total_operation_amount, 100)

    def test_mod349_errors(self):
        # Add some test data
        self.customer.write(
            {"vat": "BE0411905847", "country_id": self.env.ref("base.be").id}
        )
        self.supplier.write(
            {"vat": "BG0000100159", "country_id": self.env.ref("base.bg").id}
        )
        # Data for 1T 2023
        # Purchase invoices
        self._invoice_purchase_create("2023-01-01")
        p2 = self._invoice_purchase_create("2023-01-02")
        self._invoice_refund(p2, "2023-01-02")
        # Sale invoices
        self._invoice_sale_create("2023-01-01")
        s2 = self._invoice_sale_create("2023-01-02")
        self._invoice_refund(s2, "2023-01-02")
        # Create model
        model349_model = self.env["l10n.es.aeat.mod349.report"].with_user(
            self.account_manager
        )
        model349_errors = model349_model.create(
            {
                "name": "3490000000001",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2023,
                "period_type": "1T",
                "date_start": "2023-01-01",
                "date_end": "2023-03-31",
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 349 1T 2023")
        model349_errors.button_calculate()
        partner_record = model349_errors.partner_record_ids.filtered(
            lambda x: x.partner_vat == self.customer.vat
        )
        self.assertTrue(partner_record.partner_record_ok)

        # EL vat
        self.customer.write(
            {"vat": "EL12345670", "country_id": self.env.ref("base.gr").id}
        )
        model349_errors.button_recalculate()
        partner_record = model349_errors.partner_record_ids.filtered(
            lambda x: x.partner_vat == self.customer.vat
        )
        self.assertTrue(partner_record.partner_record_ok)

        # No vat
        self.customer.write({"vat": False, "country_id": self.env.ref("base.be").id})
        model349_errors.button_recalculate()
        partner_record = model349_errors.partner_record_ids.filtered(
            lambda x: x.partner_vat == self.customer.vat
        )
        self.assertFalse(partner_record.partner_record_ok)
        expected_note = _("Without VAT")
        self.assertIn(expected_note, partner_record.error_text)

        # No country code in vat and no country
        self.customer.write({"vat": "12345670", "country_id": False})
        model349_errors.button_recalculate()
        partner_record = model349_errors.partner_record_ids.filtered(
            lambda x: x.partner_vat == self.customer.vat
        )
        self.assertFalse(partner_record.partner_record_ok)
        expected_notes = [
            _("Without Country"),
            _("VAT without country code"),
        ]
        for expected_note in expected_notes:
            self.assertIn(expected_note, partner_record.error_text)

        # No country code in vat and BE country
        self.customer.write(
            {"vat": "0477472701", "country_id": self.env.ref("base.be").id}
        )
        model349_errors.button_recalculate()
        partner_record = model349_errors.partner_record_ids.filtered(
            lambda x: x.partner_vat == "BE0477472701"
        )
        self.assertTrue(partner_record.partner_record_ok)

        # No country code in vat and GR country
        self.customer.write(
            {"vat": "12345670", "country_id": self.env.ref("base.gr").id}
        )
        model349_errors.button_recalculate()
        partner_record = model349_errors.partner_record_ids.filtered(
            lambda x: x.partner_vat == "EL12345670"
        )
        self.assertTrue(partner_record.partner_record_ok)

        # Reset vat and country
        self.customer.write(
            {"vat": "BE0411905847", "country_id": self.env.ref("base.be").id}
        )
        model349_errors.button_recalculate()
        partner_record = model349_errors.partner_record_ids.filtered(
            lambda x: x.partner_vat == self.customer.vat
        )
        self.assertTrue(partner_record.partner_record_ok)
