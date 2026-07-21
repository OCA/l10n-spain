# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions
from odoo.tests import Form

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsAeatMod347(TestL10nEsAeatModBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.state_es_m = cls.env.ref("base.state_es_m")
        cls.country_es = cls.env.ref("base.es")
        cls.customer.with_context(no_vat_validation=True).write(
            {
                "state_id": cls.state_es_m.id,
                "country_id": cls.country_es.id,
                "vat": "12345678Z",
            }
        )
        cls.supplier.with_context(no_vat_validation=True).write(
            {
                "state_id": cls.state_es_m.id,
                "country_id": cls.country_es.id,
                "vat": "87654321Z",
            }
        )
        # Create model
        cls.model347 = cls.env["l10n.es.aeat.mod347.report"].create(
            {
                "name": "9990000000347",
                "company_id": cls.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2019,
                "date_start": "2019-01-01",
                "date_end": "2019-12-31",
            }
        )
        cls.customer_2 = cls.customer.copy(
            {"name": "Test customer 2", "vat": "ES12345678Z"}
        )
        cls.customer_3 = cls.customer.copy(
            {"name": "Test customer 3", "vat": "12345678Z"}
        )
        cls.customer_4 = cls.customer.copy(
            {"name": "Test customer 4", "vat": "ESB29805314"}
        )
        # TODO: Zip set is not necessary https://github.com/odoo/odoo/pull/94333
        cls.customer_5 = cls.customer.copy(
            {
                "name": "Test customer 5",
                # For testing spanish states mapping
                "country_id": cls.env.ref("base.es").id,
                "vat": "12345678Z",
                "zip": 28001,
            }
        )
        cls.customer_6 = cls.customer.copy(
            {
                "name": "Test customer 6",
                "country_id": cls.env.ref("base.es").id,
                "vat": "B29805314",
                "zip": 28001,
            }
        )
        cls.supplier_2 = cls.supplier.with_context(no_vat_validation=True).copy(
            {
                "name": "Test supplier 2",
                # partner_vat_unique compatibility: It is necessary to define the vat
                # field because if partner_vat_unique is installed, the vat field
                # will have copy=False
                "vat": cls.supplier.vat,
            }
        )
        # Invoice lower than the limit
        cls.taxes_sale = {
            "S_IVA10B": (2000, 200),
        }
        cls.invoice_1 = cls._invoice_sale_create("2019-01-01")
        # Cancelled invoice - Shouldn't count for partner `customer`
        cls.invoice_cancel = cls._invoice_sale_create("2019-01-01")
        cls.invoice_cancel.button_cancel()
        # Invoice higher than limit with IRPF
        cls.taxes_sale = {
            "S_IVA10S,S_IRPF20": (4000, 400),
        }
        cls.invoice_2 = cls._invoice_sale_create(
            "2019-04-01", {"partner_id": cls.customer_2.id}
        )
        # # Invoice higher than limit manually excluded
        cls.invoice_3 = cls._invoice_sale_create(
            "2019-01-01", {"partner_id": cls.customer_3.id, "not_in_mod347": True}
        )
        # # Invoice higher than cash limit
        cls.taxes_sale = {
            "S_IVA10S": (6000, 600),
        }
        cls.invoice_4 = cls._invoice_sale_create(
            "2019-07-01", {"partner_id": cls.customer_4.id}
        )
        # Create payment from invoice
        cls.payment_model = cls.env["account.payment.register"]
        payment_form = Form(
            cls.payment_model.with_context(
                active_model="account.move", active_ids=cls.invoice_4.ids
            )
        )
        payment_form.journal_id = cls.journal_cash
        payment_form.payment_date = "2019-07-01"
        payment_form.save().action_create_payments()
        # Invoice outside period higher than cash limit
        cls.invoice_5 = cls._invoice_sale_create(
            "2018-01-01", {"partner_id": cls.customer_5.id}
        )
        payment_form = Form(
            cls.payment_model.with_context(
                active_model="account.move", active_ids=cls.invoice_5.ids
            )
        )
        payment_form.journal_id = cls.journal_cash
        payment_form.payment_date = "2019-01-01"
        payment_form.save().action_create_payments()
        # Customer refund higher than limit
        cls.taxes_sale = {
            "S_IVA10S": (5000, 500),
        }
        cls.invoice_5 = cls._invoice_sale_create(
            "2019-01-01", {"partner_id": cls.customer_6.id, "move_type": "out_refund"}
        )
        # Purchase invoice higher than the limit
        cls.taxes_purchase = {
            "P_IVA10_SC": (3000, 300),
        }
        cls.invoice_suppler_1 = cls._invoice_purchase_create("2019-01-01")
        # Supplier refund higher than limit
        cls.taxes_purchase = {
            "P_IVA10_SC": (4000, 400),
        }
        cls.invoice_suppler_2 = cls._invoice_purchase_create(
            "2019-01-01", {"partner_id": cls.supplier_2.id, "move_type": "in_refund"}
        )

    def test_model_347(self):
        # Check flag propagation
        self.assertFalse(self.invoice_1.not_in_mod347)
        self.assertTrue(self.invoice_3.not_in_mod347)
        # Check model
        self.model347.button_calculate()
        partner_record_vals = [
            # key, partner, amount, cash_amount, 1T, 2T, 3T, 4T
            ("A", self.supplier, 3300, 0, 3300, 0, 0, 0),
            ("A", self.supplier_2, -4400, 0, -4400, 0, 0, 0),
            ("B", self.customer_2, 4400, 0, 0, 4400, 0, 0),
            ("B", self.customer_4, 6600, 6600, 0, 0, 6600, 0),
            ("B", self.customer_6, -5500, 0, -5500, 0, 0, 0),
            ("B", self.customer_5, 0, 6600, 0, 0, 0, 0),
        ]
        self.assertEqual(self.model347.total_partner_records, len(partner_record_vals))
        self.assertAlmostEqual(
            self.model347.total_amount, sum(x[2] for x in partner_record_vals)
        )
        self.assertAlmostEqual(
            self.model347.total_cash_amount, sum(x[3] for x in partner_record_vals)
        )
        for vals in partner_record_vals:
            partner_record = self.model347.partner_record_ids.filtered(
                lambda x, v=vals: x.partner_id == v[1]
            )
            self.assertEqual(partner_record.operation_key, vals[0])
            self.assertAlmostEqual(partner_record.amount, vals[2])
            self.assertAlmostEqual(partner_record.cash_amount, vals[3])
            self.assertAlmostEqual(partner_record.first_quarter, vals[4])
            self.assertAlmostEqual(partner_record.second_quarter, vals[5])
            self.assertAlmostEqual(partner_record.third_quarter, vals[6])
            self.assertAlmostEqual(partner_record.fourth_quarter, vals[7])
        # Check VAT handle
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_2
        )
        self.assertEqual(partner_record.partner_vat, "12345678Z")
        self.assertEqual(partner_record.partner_country_code, "ES")
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_4
        )
        self.assertEqual(partner_record.partner_vat, "B29805314")
        self.assertEqual(partner_record.partner_country_code, "ES")
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_5
        )
        self.assertEqual(partner_record.partner_vat, "12345678Z")
        self.assertEqual(partner_record.partner_country_code, "ES")
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_6
        )
        self.assertEqual(partner_record.partner_vat, "B29805314")
        self.assertEqual(partner_record.partner_country_code, "ES")
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_config_xml_ids = [
            "l10n_es_aeat_mod347.aeat_mod347_main_export_config",
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(export_to_boe._export_config(self.model347, export_config))

    def test_partner_record_ids_states(self):
        self.model347.button_calculate()
        first_partner_mod347_record = self.model347.partner_record_ids[0]
        first_partner = first_partner_mod347_record.partner_id
        self.assertFalse(first_partner.email)
        second_partner_mod347_record = self.model347.partner_record_ids[1]
        second_partner = second_partner_mod347_record.partner_id
        second_partner.email = "test@email.com"
        self.model347.button_send_mails()
        self.assertTrue(first_partner_mod347_record.state, "pending")
        self.assertTrue(second_partner_mod347_record.state, "sent")
        self.model347.button_send_mails()
        self.assertTrue(first_partner_mod347_record.state, "pending")
        first_partner.email = "test1@email.com"
        self.model347.button_send_mails()
        self.assertTrue(first_partner_mod347_record.state, "sent")

    def test_mod347_unit_report(self):
        # Test _error_count and _compute_error_count
        self.model347.button_calculate()
        # Mock an error in a partner record
        partner_record = self.model347.partner_record_ids[0]
        # Ensure it was OK before
        partner_record._compute_check_ok()
        self.assertTrue(partner_record.check_ok, partner_record.error_text)
        partner_record.partner_state_code = "AA"  # Invalid, must be digits
        partner_record._compute_check_ok()
        self.assertFalse(partner_record.check_ok)
        errors = self.model347._error_count("partner_record")
        self.assertEqual(errors.get(self.model347.id), 1)
        # Test _compute_error_count
        self.model347._compute_error_count()
        # It adds to existing error_count (if any)
        self.assertGreaterEqual(self.model347.error_count, 1)
        # Test button_confirm with errors
        with self.assertRaises(exceptions.ValidationError):
            self.model347.button_confirm()
        # Fix error and test button_confirm
        partner_record.partner_state_code = "28"
        partner_record._compute_check_ok()
        self.model347.button_confirm()
        self.assertEqual(self.model347.state, "done")

    def test_mod347_unit_partner_record(self):
        self.model347.button_calculate()
        partner_record = self.model347.partner_record_ids[0]
        # Test action_exception, action_confirm, action_pending
        partner_record.action_exception()
        self.assertEqual(partner_record.state, "exception")
        partner_record.action_confirm()
        self.assertEqual(partner_record.state, "confirmed")
        partner_record.action_pending()
        self.assertEqual(partner_record.state, "pending")
        # Test action_send
        res = partner_record.action_send()
        self.assertEqual(res["res_model"], "mail.compose.message")
        # Test message_get_suggested_recipients
        recipients = partner_record._message_get_suggested_recipients()
        self.assertTrue(
            any(r.get("partner_id") == partner_record.partner_id.id for r in recipients)
        )
        # Test _onchange_partner_id
        new_partner = self.customer_5
        new_partner.country_id = self.env.ref("base.es")
        partner_record.partner_id = new_partner
        partner_record._onchange_partner_id()
        self.assertEqual(partner_record.partner_vat, "12345678Z")
        self.assertEqual(partner_record.partner_state_code, "28")
        # Test button_recompute
        old_amount = partner_record.amount
        # Force a change in underlying data to see recompute
        # Creating a new invoice for this partner
        self._invoice_purchase_create(
            "2019-01-01", {"partner_id": partner_record.partner_id.id}
        )
        partner_record.button_recompute()
        self.assertNotEqual(partner_record.amount, old_amount)

    def test_mod347_unit_real_estate_record(self):
        # Test _onchange_partner_id and _compute_check_ok
        self.customer_5.state_id = self.state_es_m
        real_estate = self.env["l10n.es.aeat.mod347.real_estate_record"].create(
            {
                "report_id": self.model347.id,
                "partner_id": self.customer_5.id,
                "situation": "1",
            }
        )
        real_estate._onchange_partner_id()
        self.assertEqual(real_estate.partner_vat, "12345678Z")
        self.assertEqual(real_estate.state_code, "28")
        real_estate.state_code = False
        real_estate._compute_check_ok()
        self.assertFalse(real_estate.check_ok)

    def test_mod347_unit_move_record(self):
        # Test _default_partner_record
        self.model347.button_calculate()
        partner_record = self.model347.partner_record_ids[0]
        move_record = (
            self.env["l10n.es.aeat.mod347.move.record"]
            .with_context(partner_record_id=partner_record.id)
            .create(
                {
                    "move_id": self.invoice_1.id,
                    "amount": 100.0,
                }
            )
        )
        self.assertEqual(move_record.partner_record_id, partner_record)

    def test_mod347_unit_wizard_send_mail(self):
        self.model347.button_calculate()
        partner_record = self.model347.partner_record_ids[0]
        self.assertEqual(partner_record.state, "pending")
        composer = (
            self.env["mail.compose.message"]
            .with_context(
                default_model="l10n.es.aeat.mod347.partner_record",
                active_id=partner_record.id,
                active_ids=partner_record.ids,
            )
            .create(
                {
                    "subject": "Test",
                    "body": "Test body",
                    "composition_mode": "comment",
                }
            )
        )
        composer._action_send_mail()
        self.assertEqual(partner_record.state, "sent")
