# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestL10nEsTaxDigitalCanon(BaseCommon):
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
        cls.env["account.chart.template"]._load(
            template_code="es_pymes", company=cls.company, install_demo=False
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Tablet 32GB",
                "l10n_es_digital_canon": "3_75.tablet_32",
            }
        )
        cls.canon_tax = cls.env.ref(
            f"account.{cls.company.id}_tax_template_canon_purchase_3_75"
        )
        cls.env.user.company_id = cls.company

    def test_canon_applies_in_spain(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = self.partner_es
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
        invoice = move_form.save()
        self.assertIn(self.canon_tax, invoice.invoice_line_ids.tax_ids)

    def test_canon_does_not_apply_for_non_spanish_partner(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = self.partner_fr
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
        invoice = move_form.save()
        self.assertNotIn(self.canon_tax, invoice.invoice_line_ids.tax_ids)

    def test_tax_selection(self):
        selection = (
            self.env["product.product"]._fields["l10n_es_digital_canon"].selection
        )
        for key, _ in selection:
            for ttype in ["sale", "purchase"]:
                # This shouldn"t fail
                self.env.ref(
                    f"account.{self.company.id}_tax_template_canon_{ttype}_{key.split('.')[0]}"
                )

    def test_sale_order_canon_applies(self):
        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner_es
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
        sale_order = sale_form.save()
        canon_sale_tax = self.env.ref(
            f"account.{self.company.id}_tax_template_canon_sale_3_75"
        )
        self.assertIn(canon_sale_tax, sale_order.order_line.tax_id)

    def test_purchase_order_canon_applies(self):
        purchase_form = Form(self.env["purchase.order"])
        purchase_form.partner_id = self.partner_es
        with purchase_form.order_line.new() as line_form:
            line_form.product_id = self.product
        purchase_order = purchase_form.save()
        self.assertIn(self.canon_tax, purchase_order.order_line.taxes_id)
