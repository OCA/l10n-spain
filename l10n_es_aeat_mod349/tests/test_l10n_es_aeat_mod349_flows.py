# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import Command
from odoo.tests.common import tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


@tagged("post_install", "-at_install")
class TestL10nEsAeatMod349Flows(TestL10nEsAeatModBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer.write(
            {"vat": "BE0411905847", "country_id": cls.env.ref("base.be").id}
        )

    def _sale(self, invoice_date, taxes, amount, **vals):
        return self._invoice_sale_create(
            invoice_date,
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Intra-community sale",
                            "account_id": self.accounts["700000"].id,
                            "price_unit": amount,
                            "quantity": 1,
                            "tax_ids": [Command.set(taxes.ids)],
                        }
                    )
                ],
                **vals,
            },
        )

    def _create_report(self, period_type, date_start, date_end, **vals):
        return (
            self.env["l10n.es.aeat.mod349.report"]
            .with_user(self.account_manager)
            .create(
                {
                    "name": f"34900000000{period_type}",
                    "company_id": self.company.id,
                    "company_vat": "123456789",
                    "contact_name": "Test owner",
                    "statement_type": "N",
                    "support_type": "T",
                    "contact_phone": "911234455",
                    "year": 2025,
                    "period_type": period_type,
                    "date_start": date_start,
                    "date_end": date_end,
                    **vals,
                }
            )
        )

    def test_equivalent_tax_without_tag(self):
        """A duplicated tax without the 349 tag (as left by a migrated database)
        takes the key of the tax it duplicates."""
        tax = self._get_taxes("S_IVA0_G_I")
        duplicate = tax.copy()
        tags_349 = self.env["account.account.tag"].browse(
            list(self.env["account.tax"]._l10n_es_aeat_349_tags())
        )
        for line in duplicate.invoice_repartition_line_ids:
            line.tag_ids -= tags_349
        self.assertEqual(duplicate.l10n_es_aeat_349_operation_key, "E")
        self.assertIn(
            duplicate,
            self.env["account.tax"].search(
                [("l10n_es_aeat_349_operation_key", "=", "E")]
            ),
        )
        self._sale("2025-01-10", duplicate, 1000)
        report = self._create_report("01", "2025-01-01", "2025-01-31")
        report.button_calculate()
        self.assertEqual(report.partner_record_ids.operation_key, "E")
        self.assertEqual(report.partner_record_ids.total_operation_amount, 1000)

    def test_branch(self):
        """The 349 of a branch only declares its own operations."""
        branch = (
            self.env["res.company"]
            .sudo()
            .create(
                {
                    "name": "Branch",
                    "parent_id": self.company.id,
                    "country_id": self.env.ref("base.es").id,
                }
            )
        )
        self.env.user.sudo().company_ids |= branch
        self.account_manager.sudo().company_ids |= branch
        self.billing_user.sudo().company_ids |= branch
        # Accounting setup of the customer in the branch, done by an administrator
        self.customer.with_company(
            branch
        ).sudo().property_account_receivable_id = self.accounts["430000"]
        tax = self._get_taxes("S_IVA0_G_I")
        self._sale("2025-01-10", tax, 1000)
        self._sale("2025-01-11", tax, 300, company_id=branch.id)
        report = self._create_report(
            "01", "2025-01-01", "2025-01-31", company_id=branch.id
        )
        report.with_context(
            allowed_company_ids=(branch | self.company).ids
        ).button_calculate()
        self.assertEqual(report.partner_record_ids.total_operation_amount, 300)
        # The 349 of the main company keeps the operations of its branches
        report_main = self._create_report("01", "2025-01-01", "2025-01-31")
        report_main.with_context(
            allowed_company_ids=(self.company | branch).ids
        ).button_calculate()
        self.assertEqual(report_main.partner_record_ids.total_operation_amount, 1300)
