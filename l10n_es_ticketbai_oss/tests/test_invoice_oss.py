from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestOssInvoiceTBAI(TestL10nEsAeatModBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.oss_country = cls.env.ref("base.be")
        cls.company.country_id = cls.env.ref("base.es").id
        cls.company.account_fiscal_country_id = cls.env.ref("base.es").id
        general_tax = cls.env.ref(
            "l10n_es.%s_account_tax_template_s_iva21b" % cls.company.id
        )
        wizard = cls.env["l10n.eu.oss.wizard"].create(
            {
                "company_id": cls.company.id,
                "general_tax": general_tax.id,
                "todo_country_ids": [(4, cls.oss_country.id)],
            }
        )
        wizard.generate_eu_oss_taxes()
        cls.oss_customer = cls.env["res.partner"].create(
            {
                "company_id": cls.company.id,
                "name": "Test Customer OSS",
                "country_id": cls.oss_country.id,
            }
        )

    def test_no_subject_invoice(self):

        # Customer Invoice for Belgian customer
        data = {
            "company_id": self.company.id,
            "partner_id": self.oss_customer.id,
            "move_type": "out_invoice",
            "journal_id": self.journal_sale.id,
            "invoice_date": "2024-01-01",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Test BE Tax",
                        "account_id": self.accounts["700000"].id,
                        "price_unit": 20,
                        "quantity": 2,
                    },
                )
            ],
        }
        inv_oss = self.env["account.move"].with_company(self.company).create(data)

        self.assertEqual(len(inv_oss.invoice_line_ids), 1)

        is_subject_tax = inv_oss.invoice_line_ids[0].tax_ids.tbai_is_subject_to_tax()
        self.assertFalse(is_subject_tax)

        self.assertEqual(len(inv_oss.line_ids.tax_ids), 1)
        self.assertTrue(inv_oss.line_ids.tax_ids.tbai_es_entrega())
        self.assertFalse(inv_oss.line_ids.tax_ids.tbai_es_prestacion_servicios())
        self.assertEqual(inv_oss.line_ids.tax_ids.tbai_get_value_causa(inv_oss), "IE")
