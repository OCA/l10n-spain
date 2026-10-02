# Copyright 2026 Domatix - Álvaro López
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestBalanceResult(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_chart_template("es_pymes")
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_misc"]
        cls.receivable = cls._get_account("430")
        cls.income = cls._get_account("700")
        cls.reserve = cls._get_account("113")
        cls.result = cls.env["account.account"].search(
            [
                ("account_type", "=", "equity_unaffected"),
                ("company_ids", "in", cls.env.company.ids),
            ]
        )
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

    def _compute_report(self, report_xmlid, kpi_names):
        report = self.env.ref(report_xmlid)
        instance = self.env["mis.report.instance"].create(
            {
                "name": "Balance 2024-2026",
                "report_id": report.id,
                "company_id": self.env.company.id,
                "period_ids": [
                    Command.create(
                        {
                            "name": str(year),
                            "mode": "fix",
                            "manual_date_from": f"{year}-01-01",
                            "manual_date_to": f"{year}-12-31",
                        }
                    )
                    for year in (2024, 2025, 2026)
                ],
            }
        )
        rows = {row["label"]: row for row in instance.compute()["body"]}
        values = {}
        for name in kpi_names:
            kpi = report.kpi_ids.filtered(lambda k, name=name: k.name == name)
            values[name] = [
                round(cell.get("val") or 0.0, 2)
                for cell in rows[kpi.description]["cells"]
            ]
        return values

    def _check_balance(self, report_xmlid, result_kpi):
        values = self._compute_report(report_xmlid, ["es10000", "es30000", result_kpi])
        # The 2024 profit is the result of 2024. Once distributed through
        # account 129 in 2025, it must not be reported as result again.
        self.assertEqual(values["es10000"], [1000.0, 1000.0, 1000.0])
        self.assertEqual(values["es30000"], [1000.0, 1000.0, 1000.0])
        self.assertEqual(values[result_kpi], [1000.0, 0.0, 0.0])

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
