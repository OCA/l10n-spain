# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsAeatMod347(TestL10nEsAeatModBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    def _create_real_estates(self):
        self.env.user.groups_id |= self.env.ref(
            "l10n_es_aeat.group_use_aeat_real_estates"
        )
        estate_vals = {
            "partner_id": self.company.partner_id.id,
            "address_type": "CALLE",
            "address": "Mayor",
            "number_type": "NUM",
            "number": 5,
        }
        self.premises, self.shop = self.env["l10n.es.aeat.real_estate"].create(
            [
                {
                    **estate_vals,
                    "name": "Premises",
                    "reference": "8374992BV4192Q4560EG",
                    "city": "Aravaca",
                    "municipality": "Madrid",
                    "municipality_code": "28079",
                    "zip": "28023",
                    "state_id": self.env.ref("base.state_es_m").id,
                    "floor": "2",
                },
                {
                    **estate_vals,
                    "name": "Shop",
                    "reference": "201001000123400001",
                    "city": "Pamplona",
                    "municipality_code": "31201",
                    "zip": "31001",
                    "state_id": self.env.ref("base.state_es_na").id,
                },
            ]
        )
        self.tenant = self.customer.copy({"name": "Tenant", "vat": "ES12345678Z"})
        self.tenant_2 = self.customer.copy({"name": "Tenant 2", "vat": "ES12345678Z"})

    def _invoice_form(self, partner, date, lines, move_type="out_invoice"):
        invoice_form = Form(
            self.env["account.move"].with_context(default_move_type=move_type)
        )
        invoice_form.partner_id = partner
        invoice_form.invoice_date = date
        for price, taxes, real_estate in lines:
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.name = real_estate.name or "Sale"
                line_form.price_unit = price
                line_form.tax_ids.clear()
                for tax in self._get_taxes(taxes):
                    line_form.tax_ids.add(tax)
                line_form.l10n_es_aeat_real_estate_id = real_estate
        invoice = invoice_form.save()
        invoice.action_post()
        return invoice

    def _create_rents(self):
        """The tenant rents the premises and the shop and buys something else,
        the tenant 2 only rents the shop and pays it in cash."""
        self._create_real_estates()
        no_estate = self.env["l10n.es.aeat.real_estate"]
        for partner, date, lines, move_type in (
            (
                self.tenant,
                "2019-02-01",
                [
                    # The withholding is not a 347 operation
                    (1000, "S_IVA21S,S_IRPF19", self.premises),
                    (3000, "S_IVA21B", no_estate),
                ],
                "out_invoice",
            ),
            (self.tenant, "2019-05-01", [(500, "S_IVA21S", self.shop)], "out_invoice"),
            (
                self.tenant,
                "2019-06-01",
                [(200, "S_IVA21S", self.premises)],
                "out_refund",
            ),
            (
                self.tenant_2,
                "2019-03-01",
                [(5000, "S_IVA21S", self.shop)],
                "out_invoice",
            ),
        ):
            invoice = self._invoice_form(partner, date, lines, move_type)
        payment_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids
            )
        )
        payment_form.journal_id = self.journal_cash
        payment_form.payment_date = "2019-03-01"
        payment_form.save().action_create_payments()

    def _tenant_records(self):
        return self.model347.partner_record_ids.filtered(
            lambda r: r.partner_id in (self.tenant | self.tenant_2)
        )

    def _real_estate_records(self):
        return self.model347.real_estate_record_ids.filtered("real_estate_id")

    def test_real_estate_rents(self):
        """The rents go to their own partner record and to a real estate record
        per partner and real estate, filled from the real estate, and
        recomputing either partner record of a partner recomputes both."""
        self._create_rents()
        fields = ["situation", "reference", "floor", "city", "township"]
        fields += ["township_code", "state_code", "postal_code"]
        estate_values = {
            self.premises: ("1", "8374992BV4192Q4560EG", "2", "Aravaca", "Madrid")
            + ("28079", "28", "28023"),
            self.shop: ("2", "201001000123400001", False, False, "Pamplona")
            + ("31201", "31", "31001"),
        }
        RealEstateRecord = self.env["l10n.es.aeat.mod347.real_estate_record"]
        manual = RealEstateRecord.create(
            {
                "report_id": self.model347.id,
                "partner_id": self.tenant.id,
                "situation": "3",
                "state_code": "28",
                "amount": 1000,
            }
        )
        with Form(RealEstateRecord.with_context(report_id=self.model347.id)) as form:
            form.real_estate_id = self.premises
            # The province of the real estate is kept
            form.partner_id = self.tenant
        chosen = form.record
        self.assertEqual(tuple(chosen[f] for f in fields), estate_values[self.premises])
        # The calculation replaces the records with a real estate
        self.model347.button_calculate()
        self.assertEqual(
            {
                (r.partner_id, r.bussiness_real_estate_rent, r.amount, r.cash_amount)
                + (r.first_quarter, r.second_quarter)
                for r in self._tenant_records()
            },
            {
                (self.tenant, False, 3630, 0, 3630, 0),
                (self.tenant, True, 1573, 0, 1210, 363),
                (self.tenant_2, False, 0, 6050, 0, 0),
                (self.tenant_2, True, 6050, 0, 6050, 0),
            },
        )
        self.assertEqual(
            {
                (r.partner_id, r.partner_vat, r.real_estate_id, r.amount)
                + tuple(r[f] for f in fields)
                for r in self._real_estate_records()
            },
            {
                (partner, "12345678Z", estate, amount) + estate_values[estate]
                for partner, estate, amount in (
                    (self.tenant, self.premises, 968),
                    (self.tenant, self.shop, 605),
                    (self.tenant_2, self.shop, 6050),
                )
            },
        )
        # The manual record without real estate is kept
        self.assertEqual(
            self.model347.real_estate_record_ids - self._real_estate_records(), manual
        )

        general, rent = (
            self._tenant_records()
            .filtered(lambda r: r.partner_id == self.tenant)
            .sorted("bussiness_real_estate_rent")
        )
        for amount, record, rent_amount, premises_amount in (
            (100, rent, 1694, 1089),
            (1000, general, 2904, 2299),
        ):
            self._invoice_form(
                self.tenant, "2019-11-01", [(amount, "S_IVA21S", self.premises)]
            )
            record.button_recompute()
            self.assertEqual(
                (general.amount, rent.amount, rent.fourth_quarter),
                (3630, rent_amount, rent_amount - 1573),
            )
            self.assertEqual(
                self._real_estate_records()
                .filtered(lambda r: r.real_estate_id == self.premises)
                .mapped("amount"),
                [premises_amount],
            )
