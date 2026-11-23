##############################################################################
#
# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright (c) 2023 Binhex
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################

import logging
from unittest.mock import patch
from urllib.parse import urlsplit

from odoo.fields import Command
from odoo.tests import Form, HttpCase, tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("atc")


class TestL10nEsAtcMod415Base(TestL10nEsAeatModBase):
    # The chart is the one of the base: 20.0 merged the Canary templates into
    # es_common, so es_pymes already carries the IGIC taxes this declaration
    # reads. Odoo core ships them archived and activates them (archiving the
    # IVA ones) when the company gets a Canary province, as a Canary user does.
    @classmethod
    def _chart_of_accounts_create(cls):
        res = super()._chart_of_accounts_create()
        cls.company.sudo().write(
            {
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_gc").id,
            }
        )
        return res

    @classmethod
    def _model415_create(cls):
        return cls.env["l10n.es.atc.mod415.report"].create(
            {
                "name": "9990000000415",
                "company_id": cls.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2019,
                "date_start": "2019-01-01",
                "date_end": "2019-12-31",
            }
        )


@tagged("post_install", "-at_install")
class TestL10nEsAtcMod415(TestL10nEsAtcMod415Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create model
        cls.model415 = cls._model415_create()
        cls.customer_2 = cls.customer.copy(
            {"name": "Test customer 2", "vat": "ES12345678Z"}
        )
        cls.customer_3 = cls.customer.copy({"name": "Test customer 3"})
        # A customer excluded from the 415 on its form, invoiced through one of
        # its contacts
        cls.customer_7 = cls.customer.copy(
            {"name": "Test customer 7", "is_company": True, "not_in_mod415": True}
        )
        cls.customer_7_contact = cls.env["res.partner"].create(
            {"name": "Contact of customer 7", "parent_id": cls.customer_7.id}
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
        cls.supplier_2 = cls.supplier.copy({"name": "Test supplier 2"})
        # Invoice lower than the limit
        cls.taxes_sale = {
            "account_tax_template_igic_r_7": (2000, 140),
        }
        cls.invoice_1 = cls._invoice_sale_create("2019-01-01")
        # Cancelled invoice - Shouldn't count for partner `customer`
        cls.invoice_cancel = cls._invoice_sale_create("2019-01-01")
        cls.invoice_cancel.button_cancel()
        # Invoice higher than limit
        cls.taxes_sale = {
            "account_tax_template_igic_r_7": (4000, 280),
        }
        cls.invoice_2 = cls._invoice_sale_create(
            "2019-04-01", {"partner_id": cls.customer_2.id}
        )
        # # Invoice higher than limit manually excluded
        cls.invoice_3 = cls._invoice_sale_create(
            "2019-01-01", {"partner_id": cls.customer_3.id, "not_in_mod415": True}
        )
        cls.invoice_7 = cls._invoice_sale_create(
            "2019-04-01", {"partner_id": cls.customer_7_contact.id}
        )
        # # Invoice higher than cash limit
        cls.taxes_sale = {
            "account_tax_template_igic_r_7": (6000, 420),
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
            "account_tax_template_igic_r_7": (5000, 350),
        }
        cls.invoice_5 = cls._invoice_sale_create(
            "2019-01-01", {"partner_id": cls.customer_6.id, "move_type": "out_refund"}
        )
        # Purchase invoice higher than the limit
        cls.taxes_purchase = {
            "account_tax_template_igic_sop_7": (3000, 210),
        }
        cls.invoice_suppler_1 = cls._invoice_purchase_create("2019-01-01")
        # Supplier refund higher than limit
        cls.taxes_purchase = {
            "account_tax_template_igic_sop_7": (4000, 280),
        }
        cls.invoice_suppler_2 = cls._invoice_purchase_create(
            "2019-01-01", {"partner_id": cls.supplier_2.id, "move_type": "in_refund"}
        )

    def test_model_415(self):
        # invoice_3 is excluded on the invoice and invoice_7 on the form of
        # the commercial partner of its contact: none of them is declared
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
                lambda x, vals=vals: x.partner_id == vals[1]
            )
            self.assertEqual(partner_record.operation_key, vals[0])
            self.assertAlmostEqual(partner_record.amount, vals[2])
            self.assertAlmostEqual(partner_record.cash_amount, vals[3])
            self.assertAlmostEqual(partner_record.first_quarter, vals[4])
            self.assertAlmostEqual(partner_record.second_quarter, vals[5])
            self.assertAlmostEqual(partner_record.third_quarter, vals[6])
            self.assertAlmostEqual(partner_record.fourth_quarter, vals[7])
        self.assertFalse(
            self.model415.partner_record_ids.filtered(
                lambda x: (
                    x.partner_id
                    in (self.customer_3, self.customer_7, self.customer_7_contact)
                )
            )
        )

    def test_model_415_partner_excluded_in_its_company(self):
        """A partner left out of the 415 of a company is still declared by
        another one, as in the 347."""
        self.assertTrue(self.customer_7.not_in_mod415)
        other_company = self.env["res.company"].sudo().create({"name": "Other company"})
        self.env.user.sudo().company_ids += other_company
        partner_form = Form(self.customer_7.with_company(other_company))
        self.assertFalse(partner_form.not_in_mod415)
        self.assertTrue(Form(self.customer_7).not_in_mod415)

    def test_model_415_igic_taxes_of_odoo_core(self):
        """Every IGIC tax of Odoo core counts in the key of its side: purchases
        in A and sales in B, each invoice entered with the fiscal position the
        tax belongs to, as the user picks the tax."""
        taxes_by_key = {
            "A": (
                "igic_sop_5",
                "igic_sop_5_inv",
                "igic_sop_i_5",
                "igic_sop_i_5_inv",
                "igic_ISP5",
                "igic_p_re05",
                "igic_p_ex",
                "igic_sop_0_s",
                "igic_sop_7_s",
                "igic_sop_20_s",
                "igic_sop_cmino",
                "igic_sop_7_cmino",
                "igic_sop_20_cmino",
                "p_igic_ns",
            ),
            "B": ("igic_r_5", "s_igic_ns"),
        }
        expected = {}
        for key, xmlids in taxes_by_key.items():
            for xmlid in xmlids:
                # With the module of the template: without it, `_get_taxes`
                # takes a key with capitals (igic_ISP5) for an old tax code
                tax_key = f"l10n_es.account_tax_template_{xmlid}"
                tax = self._get_taxes(tax_key)
                self.assertTrue(tax, xmlid)
                partner = self.customer.copy({"name": f"Partner {xmlid}"})
                vals = {
                    "partner_id": partner.id,
                    "fiscal_position_id": tax.fiscal_position_ids[:1].id,
                }
                if key == "A":
                    with patch.object(
                        type(self), "taxes_purchase", {tax_key: (4000, 0)}
                    ):
                        invoice = self._invoice_purchase_create("2019-05-01", vals)
                else:
                    with patch.object(type(self), "taxes_sale", {tax_key: (4000, 0)}):
                        invoice = self._invoice_sale_create("2019-05-01", vals)
                expected[partner] = (key, invoice.amount_total)
        self.model415.button_calculate()
        for partner, (key, amount) in expected.items():
            record = self.model415.partner_record_ids.filtered(
                lambda x, partner=partner: x.partner_id == partner
            )
            self.assertEqual(record.operation_key, key, partner.name)
            self.assertAlmostEqual(record.amount, amount, 2, partner.name)

    def test_model_415_cash_of_another_company(self):
        """With several companies active, the cash collected by another
        company is not declared in the 415 of this one."""
        other_company = (
            self.env["res.company"]
            .sudo()
            .create(
                {"name": "Other company", "currency_id": self.env.ref("base.EUR").id}
            )
        )
        self.env["account.chart.template"].sudo()._load(
            template_code="es_pymes", company=other_company, install_demo=False
        )
        self.env.user.sudo().company_ids = [Command.link(other_company.id)]
        env = self.env(
            context=dict(
                self.env.context,
                allowed_company_ids=[self.company.id, other_company.id],
            )
        )
        partner = env["res.partner"].create({"name": "Customer of the other company"})
        invoice = (
            env["account.move"]
            .with_company(other_company)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": partner.id,
                    "invoice_date": "2019-03-01",
                    "invoice_line_ids": [
                        Command.create(
                            {"name": "Sale", "price_unit": 7000, "tax_ids": []}
                        )
                    ],
                }
            )
        )
        invoice.action_post()
        payment_form = Form(
            env["account.payment.register"]
            .with_company(other_company)
            .with_context(active_model="account.move", active_ids=invoice.ids)
        )
        # The charts of 20.0 do not create a cash journal
        payment_form.journal_id = (
            env["account.journal"]
            .with_company(other_company)
            .create({"name": "Cash", "code": "CSHO", "type": "cash"})
        )
        payment_form.payment_date = "2019-03-01"
        payment_form.save().action_create_payments()
        self.model415.with_env(env).button_calculate()
        self.assertFalse(
            self.model415.partner_record_ids.filtered(lambda x: x.partner_id == partner)
        )
        # The cash of this company is still declared
        self.assertTrue(
            self.model415.partner_record_ids.filtered(
                lambda x: x.partner_id == self.customer_5
            ).cash_amount
        )

    def test_model_415_recompute_a_partner(self):
        """A bill entered after the calculation reaches the partner record when
        the user presses Recompute on it, and the record has to be sent again."""
        self.model415.button_calculate()
        record = self.model415.partner_record_ids.filtered(
            lambda x: x.partner_id == self.supplier
        )
        record.action_confirm()
        self.assertAlmostEqual(record.amount, 3210)
        # A bill of 4000 + 7 % IGIC
        self._invoice_purchase_create("2019-10-01")
        record.button_recompute()
        self.assertAlmostEqual(record.amount, 3210 + 4280)
        self.assertAlmostEqual(record.fourth_quarter, 4280)
        self.assertEqual(record.state, "pending")

    def test_model_415_email_of_the_report_company(self):
        """The email to the partner names the company of the declaration, also
        when the user works in another one, and is kept once sent."""
        self.model415.button_calculate()
        record = self.model415.partner_record_ids[:1]
        record.partner_id.email = "partner@example.com"
        other_company = self.env["res.company"].sudo().create({"name": "Other company"})
        self.env.user.sudo().write(
            {
                "company_ids": [Command.link(other_company.id)],
                "company_id": other_company.id,
            }
        )
        record.send_email_direct()
        mail = (
            self.env["mail.mail"]
            .sudo()
            .search([("model", "=", record._name), ("res_id", "=", record.id)])
        )
        self.assertIn(self.model415.company_id.name, mail.subject)
        self.assertNotIn(other_company.name, mail.subject)
        self.assertFalse(mail.auto_delete)

    def test_model_415_partner_record_sent_from_the_composer(self):
        """The email sent from the composer that the Send button of a partner
        record opens marks the record as sent, as in the 347."""
        self.model415.button_calculate()
        record = self.model415.partner_record_ids[:1]
        record.partner_id.email = "partner@example.com"
        action = record.action_send()
        composer_form = Form(
            self.env[action["res_model"]].with_context(
                active_id=record.id,
                active_ids=record.ids,
                **action["context"],
            ),
            view=self.env["ir.ui.view"].browse(action["view_id"]),
        )
        composer_form.body = "Test body"
        composer_form.save().action_send_mail()
        self.assertEqual(record.state, "sent")

    def test_model_415_new_partner_record_from_its_list(self):
        """A partner record added from the list that the declaration opens
        belongs to that declaration."""
        self.model415.button_calculate()
        action = self.model415.btn_list_records()
        record_form = Form(
            self.env[action["res_model"]].with_context(**action.get("context", {}))
        )
        record_form.partner_id = self.env["res.partner"].create({"name": "New partner"})
        record = record_form.save()
        self.assertEqual(record.report_id, self.model415)


@tagged("post_install", "-at_install")
class TestL10nEsAtcMod415NonDeductible(TestL10nEsAtcMod415Base):
    def test_model_415_deductible_percentage(self):
        """A bill of 4000 + 7 % IGIC with a deductible percentage of 50 % is
        declared with its total, 4280: the IGIC borne counts whether it is
        deductible or not, as in the model 347 (RGAT art. 34.2.a).
        """
        bill_form = Form(
            self.env["account.move"]
            .with_user(self.billing_user)
            .with_context(default_move_type="in_invoice")
        )
        bill_form.partner_id = self.supplier
        bill_form.invoice_date = "2019-02-01"
        bill_form.journal_id = self.journal_purchase
        with bill_form.invoice_line_ids.new() as line_form:
            line_form.name = "Mixed use car"
            line_form.price_unit = 4000
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self._get_taxes("account_tax_template_igic_sop_7"))
            line_form.deductible_percentage = 0.5
        bill = bill_form.save()
        bill.action_post()
        model415 = self._model415_create()
        model415.button_calculate()
        record = model415.partner_record_ids
        self.assertEqual(record.partner_id, self.supplier)
        self.assertEqual(record.operation_key, "A")
        self.assertAlmostEqual(record.amount, 4280, 2)
        self.assertAlmostEqual(record.first_quarter, 4280, 2)
        self.assertEqual(record.move_record_ids.move_id, bill)
        self.assertAlmostEqual(record.move_record_ids.amount, 4280, 2)


@tagged("post_install", "-at_install")
class TestL10nEsAtcMod415Answer(TestL10nEsAtcMod415Base, HttpCase):
    taxes_purchase = {  # noqa: RUF012
        "account_tax_template_igic_sop_7": (4000, 280),
    }

    def _open_link(self, url):
        # The partner opens the link without logging in: the public session
        # tells the server which database it is for
        self.authenticate(None, None)
        parts = urlsplit(url)
        return self.url_open(f"{parts.path}?{parts.query}")

    def test_partner_answers_the_415_data(self):
        """The buttons of the email sent to a partner confirm or reject its
        415 record."""
        model415 = self._model415_create()
        self._invoice_purchase_create("2019-02-01")
        model415.button_calculate()
        record = model415.partner_record_ids
        self.assertEqual(record.partner_id, self.supplier)
        response = self._open_link(record.get_confirm_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn("Modelo 415", response.text)
        record.invalidate_recordset()
        self.assertEqual(record.state, "confirmed")
        self._open_link(record.get_reject_url())
        record.invalidate_recordset()
        self.assertEqual(record.state, "exception")
