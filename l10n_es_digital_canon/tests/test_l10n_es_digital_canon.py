# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import tagged
from odoo.tests.common import Form, SavepointCase


@tagged("post_install", "-at_install")
class TestL10nEsTaxDigitalCanon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_es = cls.env.ref("base.es")
        cls.currency = cls.env.ref("base.EUR")
        cls.partner_es = cls.env["res.partner"].create(
            {"name": "Spanish Customer", "country_id": cls.country_es.id}
        )
        cls.partner_fr = cls.env["res.partner"].create(
            {"name": "French Customer", "country_id": cls.env.ref("base.fr").id}
        )
        cls.company = cls.env["res.company"].create(
            {"name": "Test Company", "currency_id": cls.currency.id}
        )
        cls.chart = cls.env.ref("l10n_es.account_chart_template_pymes")
        cls.chart.try_loading(company=cls.company)
        cls.product = cls.env["product.product"].create(
            {
                "name": "Tablet 32GB",
                "l10n_es_digital_canon": "3_75.tablet_32",
            }
        )
        cls.canon_tax = cls.env.ref(
            f"l10n_es_digital_canon.{cls.company.id}_tax_template_canon_purchase_3_75"
        )
        cls.account = cls.env["account.account"].create(
            {
                "name": "Account",
                "code": "account",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
                "company_id": cls.company.id,
            }
        )
        cls.fiscal_position = cls.env["account.fiscal.position"].create(
            {
                "name": "Test Fiscal Position",
                "company_id": cls.company.id,
            }
        )
        cls.env.user.company_id = cls.company

    def test_canon_applies_in_spain(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = self.partner_es
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.account_id = self.account
        invoice = move_form.save()
        self.assertIn(self.canon_tax, invoice.invoice_line_ids.tax_ids)

    def test_canon_does_not_apply_for_non_spanish_partner(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = self.partner_fr
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.account_id = self.account
        invoice = move_form.save()
        self.assertNotIn(self.canon_tax, invoice.invoice_line_ids.tax_ids)

    def test_map_tax(self):
        taxes = self.fiscal_position.map_tax(
            taxes=self.env["account.tax"], product=self.product, partner=self.partner_es
        )
        self.assertIn(self.canon_tax, taxes)
        taxes = self.fiscal_position.map_tax(
            taxes=self.env["account.tax"], product=self.product, partner=self.partner_fr
        )
        self.assertNotIn(self.canon_tax, taxes)
        product_no_canon = self.env["product.product"].create(
            {
                "name": "Tablet 16GB",
                "l10n_es_digital_canon": False,
            }
        )
        taxes = self.fiscal_position.map_tax(
            taxes=self.env["account.tax"],
            product=product_no_canon,
            partner=self.partner_es,
        )
        self.assertNotIn(self.canon_tax, taxes)
        self.partner_es.is_digital_canon_exempt = True
        taxes = self.fiscal_position.map_tax(
            taxes=self.env["account.tax"], product=self.product, partner=self.partner_es
        )
        self.assertNotIn(self.canon_tax, taxes)

    def test_tax_selection(self):
        selection = (
            self.env["product.product"]._fields["l10n_es_digital_canon"].selection
        )
        for key, _ in selection:
            for ttype in ["sale", "purchase"]:
                # This shouldn"t fail
                self.env.ref(
                    f"l10n_es_digital_canon.tax_template_canon_{ttype}_{key.split('.')[0]}"
                )
