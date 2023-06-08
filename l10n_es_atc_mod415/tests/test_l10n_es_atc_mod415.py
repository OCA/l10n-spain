##############################################################################
#
# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright (c) 2023 Binhex System Solutions
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################

import logging

from odoo.tests.common import Form

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("atc")


class TestL10nEsAtcMod415(TestL10nEsAeatModBase):
    @classmethod
    def _chart_of_accounts_create(cls):
        _logger.debug("Creating chart of account")
        cls.company = cls.env["res.company"].create(
            {"name": "Canary test company", "currency_id": cls.env.ref("base.EUR").id}
        )
        cls.chart = cls.env.ref("l10n_es_igic.account_chart_template_pymes_canary")
        cls.env.ref("base.group_multi_company").write({"users": [(4, cls.env.uid)]})
        cls.env.user.write(
            {"company_ids": [(4, cls.company.id)], "company_id": cls.company.id}
        )
        chart = cls.env.ref("l10n_es_igic.account_chart_template_pymes_canary")
        chart.try_loading()
        cls.with_context(company_id=cls.company.id)
        return True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create model
        cls.model415 = cls.env["l10n.es.atc.mod415.report"].create(
            {
                "name": "9990000000415",
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
        cls.customer_3 = cls.customer.copy({"name": "Test customer 3"})
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
        cls.supplier_2 = cls.supplier.copy({"name": "Test supplier 2"})
        # Invoice lower than the limit
        cls.taxes_sale = {
            "l10n_es_igic.account_tax_template_igic_r_7": (2000, 140),
        }
        cls.invoice_1 = cls._invoice_sale_create("2019-01-01")
        # Cancelled invoice - Shouldn't count for partner `customer`
        cls.invoice_cancel = cls._invoice_sale_create("2019-01-01")
        cls.invoice_cancel.button_cancel()
        # Invoice higher than limit
        cls.taxes_sale = {
            "l10n_es_igic.account_tax_template_igic_r_7": (4000, 280),
        }
        cls.invoice_2 = cls._invoice_sale_create(
            "2019-04-01", {"partner_id": cls.customer_2.id}
        )
        # # Invoice higher than limit manually excluded
        cls.invoice_3 = cls._invoice_sale_create(
            "2019-01-01", {"partner_id": cls.customer_3.id, "not_in_mod415": True}
        )
        # # Invoice higher than cash limit
        cls.taxes_sale = {
            "l10n_es_igic.account_tax_template_igic_r_7": (6000, 420),
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
            "l10n_es_igic.account_tax_template_igic_r_7": (5000, 350),
        }
        cls.invoice_5 = cls._invoice_sale_create(
            "2019-01-01", {"partner_id": cls.customer_6.id, "move_type": "out_refund"}
        )
        # Purchase invoice higher than the limit
        cls.taxes_purchase = {
            "l10n_es_igic.account_tax_template_igic_sop_7": (3000, 210),
        }
        cls.invoice_suppler_1 = cls._invoice_purchase_create("2019-01-01")
        # Supplier refund higher than limit
        cls.taxes_purchase = {
            "l10n_es_igic.account_tax_template_igic_sop_7": (4000, 280),
        }
        cls.invoice_suppler_2 = cls._invoice_purchase_create(
            "2019-01-01", {"partner_id": cls.supplier_2.id, "move_type": "in_refund"}
        )

    def test_model_415(self):
        # Check flag propagation
        self.assertFalse(self.invoice_1.not_in_mod415)
        self.assertTrue(self.invoice_3.not_in_mod415)
        # Check model
        self.model415.button_calculate()
        partner_record_vals = [
            # key, partner, amount, cash_amount, 1T, 2T, 3T, 4T
            ("A", self.supplier, 3210, 0, 3210, 0, 0, 0),
            ("A", self.supplier_2, -4280, 0, -4280, 0, 0, 0),
            ("B", self.customer_2, 4280, 0, 0, 4280, 0, 0),
            ("B", self.customer_4, 6420, 6420, 0, 0, 6420, 0),
            ("B", self.customer_6, -5350, 0, -5350, 0, 0, 0),
            ("B", self.customer_5, 0, 6420, 0, 0, 0, 0),
        ]
        self.assertEqual(self.model415.total_partner_records, len(partner_record_vals))
        self.assertAlmostEqual(
            self.model415.total_amount, sum(x[2] for x in partner_record_vals)
        )
        self.assertAlmostEqual(
            self.model415.total_cash_amount, sum(x[3] for x in partner_record_vals)
        )
        for vals in partner_record_vals:
            partner_record = self.model415.partner_record_ids.filtered(
                lambda x: x.partner_id == vals[1]
            )
            self.assertEqual(partner_record.operation_key, vals[0])
            self.assertAlmostEqual(partner_record.amount, vals[2])
            self.assertAlmostEqual(partner_record.cash_amount, vals[3])
            self.assertAlmostEqual(partner_record.first_quarter, vals[4])
            self.assertAlmostEqual(partner_record.second_quarter, vals[5])
            self.assertAlmostEqual(partner_record.third_quarter, vals[6])
            self.assertAlmostEqual(partner_record.fourth_quarter, vals[7])
        # Check VAT handle
        partner_record = self.model415.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_2
        )
        self.assertEqual(partner_record.partner_vat, "12345678Z")
        self.assertEqual(partner_record.partner_country_code, "ES")
        partner_record = self.model415.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_4
        )
        self.assertEqual(partner_record.partner_vat, "B29805314")
        self.assertEqual(partner_record.partner_country_code, "ES")
        partner_record = self.model415.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_5
        )
        self.assertEqual(partner_record.partner_vat, "12345678Z")
        self.assertEqual(partner_record.partner_country_code, "ES")
        partner_record = self.model415.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_6
        )
        self.assertEqual(partner_record.partner_vat, "B29805314")
        self.assertEqual(partner_record.partner_country_code, "ES")
        # # Export to BOE
        # export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
        #     {"name": "test_export_to_boe.txt"}
        # )
        # export_config_xml_ids = [
        #     "l10n_es_atc_mod415.aeat_mod415_main_export_config",
        # ]
        # for xml_id in export_config_xml_ids:
        #     export_config = self.env.ref(xml_id)
        #     self.assertTrue(export_to_boe._export_config(self.model415, export_config))
