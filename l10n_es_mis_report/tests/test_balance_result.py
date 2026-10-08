# Copyright 2026 Domatix - Álvaro López
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.mis_builder.models.accounting_none import AccountingNone


@tagged("post_install", "-at_install")
class TestBalanceResult(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_chart_template("es_pymes")
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_misc"]
        cls.receivable = cls._get_account("430")
        cls.income = cls._get_account("700")
        cls.result = cls._get_account("129")
        cls.reserve = cls._get_account("113")
        # 2024 profit, distributed to reserves in 2025 through account 129
        cls._post_entry("2024-06-30", cls.receivable, cls.income, 1000.0)
        cls._post_entry("2025-06-30", cls.result, cls.reserve, 1000.0)

    @classmethod
    def _get_account(cls, prefix):
        return cls.env["account.account"].search(
            [
                ("code", "=like", f"{prefix}%"),
                ("company_ids", "in", cls.env.company.ids),
            ],
            limit=1,
        )

    @classmethod
    def _post_entry(cls, date, debit_account, credit_account, amount):
        move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": date,
                "journal_id": cls.journal.id,
                "line_ids": [
                    Command.create({"account_id": debit_account.id, "debit": amount}),
                    Command.create({"account_id": credit_account.id, "credit": amount}),
                ],
            }
        )
        move.action_post()
        return move

    def _evaluate(self, report_xmlid):
        report = self.env.ref(report_xmlid)
        aep = report._prepare_aep(self.env.company)
        values = report.evaluate(aep, date_from="2026-01-01", date_to="2026-12-31")
        return {
            name: (0.0 if value is AccountingNone else value)
            for name, value in values.items()
        }

    def _check_balance(self, report_xmlid, result_kpi):
        values = self._evaluate(report_xmlid)
        self.assertAlmostEqual(values["es10000"], 1000.0)
        self.assertAlmostEqual(values["es30000"], 1000.0)
        self.assertAlmostEqual(values[result_kpi], 0.0)

    def test_balance_abbreviated(self):
        self._check_balance(
            "l10n_es_mis_report.mis_report_es_balance_abreviado", "es21700"
        )

    def test_balance_normal(self):
        self._check_balance(
            "l10n_es_mis_report.mis_report_es_balance_normal", "es21700"
        )

    def test_balance_sme(self):
        self._check_balance("l10n_es_mis_report.mis_report_es_balance_pymes", "es21700")

    def test_balance_sme_sfl(self):
        self._check_balance(
            "l10n_es_mis_report.mis_report_es_balance_pymes_sfl", "es21400"
        )
