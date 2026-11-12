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
