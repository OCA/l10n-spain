# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import Command
from odoo.exceptions import UserError
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

    def _export_boe(self, report):
        """Records of the file given by the "Export to BOE" button."""
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_user(self.account_manager)
            .with_context(active_id=report.id, active_model=report._name)
            .create({})
        )
        wizard.action_get_file()
        content = (
            self.env["ir.attachment"]
            .search([("res_model", "=", report._name), ("res_id", "=", report.id)])
            .raw.decode("iso-8859-1")
        )
        return [content[i : i + 500] for i in range(0, len(content), 500)]

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

    def test_triangular_deal(self):
        """An invoice marked as triangular deal is declared with key T, and so is
        its refund in a later period."""
        invoice = self._sale(
            "2025-01-10",
            self._get_taxes("S_IVA0_G_I"),
            1000,
            eu_triangular_deal=True,
        )
        report_1 = self._create_report("01", "2025-01-01", "2025-01-31")
        report_1.button_calculate()
        self.assertEqual(report_1.partner_record_ids.operation_key, "T")
        self.assertEqual(report_1.partner_record_ids.total_operation_amount, 1000)
        self._invoice_refund(invoice, "2025-02-10")
        report_2 = self._create_report("02", "2025-02-01", "2025-02-28")
        report_2.button_calculate()
        self.assertFalse(report_2.partner_record_ids)
        refund = report_2.partner_refund_ids
        self.assertEqual(refund.operation_key, "T")
        self.assertEqual(refund.period_type, "01")
        self.assertEqual(refund.total_origin_amount, 1000)
        self.assertEqual(refund.total_operation_amount, 0)

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

    def test_boe_export(self):
        invoice = self._sale("2025-01-10", self._get_taxes("S_IVA0_G_I"), 1000)
        report_1 = self._create_report("01", "2025-01-01", "2025-01-31")
        report_1.button_calculate()
        report_1.button_confirm()
        records = self._export_boe(report_1)
        self.assertEqual(records[0][:4], "1349")
        operator = records[1]
        # Positions 76-92 operator NIF, 93-132 name, 133 key, 134-146 base
        self.assertEqual(operator[:8], "23492025")
        self.assertEqual(operator[75:92], "BE0411905847     ")
        self.assertEqual(operator[92:132].strip().upper(), "TEST CUSTOMER")
        self.assertEqual(operator[132], "E")
        self.assertEqual(operator[133:146], "0000000100000")
        self._invoice_refund(invoice, "2025-02-10")
        report_2 = self._create_report("02", "2025-02-01", "2025-02-28")
        report_2.button_calculate()
        report_2.button_confirm()
        refund = self._export_boe(report_2)[1]
        # 147-150 year, 151-152 period, 153-165 rectified base, 166-178 previous
        self.assertEqual(refund[132], "E")
        self.assertEqual(refund[146:152], "202501")
        self.assertEqual(refund[152:165], "0000000000000")
        self.assertEqual(refund[165:178], "0000000100000")

    def test_no_349_tags(self):
        """Without the 349 tags of Odoo core no tax has a key: the calculation
        asks to update the chart of accounts."""
        tags_349 = self.env["account.account.tag"].browse(
            list(self.env["account.tax"]._l10n_es_aeat_349_tags())
        )
        repartition_lines = (
            self.env["account.tax.repartition.line"]
            .sudo()
            .search([("tag_ids", "in", tags_349.ids)])
        )
        for line in repartition_lines:
            line.tag_ids -= tags_349
        report = self._create_report("01", "2025-01-01", "2025-01-31")
        with self.assertRaises(UserError):
            report.button_calculate()

    def test_print_from_declaration(self):
        """The PDF of the declaration is in its print menu."""
        bindings = self.env["ir.actions.actions"].get_bindings(
            "l10n.es.aeat.mod349.report"
        )
        self.assertIn(
            self.env.ref("l10n_es_aeat_mod349.act_report_aeat_mod349_pdf").id,
            [action["id"] for action in bindings.get("report", [])],
        )
