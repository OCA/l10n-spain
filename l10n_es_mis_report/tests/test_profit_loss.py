# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestProfitLoss(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_chart_template("es_pymes")
    def setUpClass(cls):
        super().setUpClass()
        cls.accountant = new_test_user(
            cls.env,
            login="es_mis_accountant",
            groups="base.group_user,account.group_account_manager",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )
        journal = cls.company_data["default_journal_misc"]
        move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2025-06-30",
                "journal_id": journal.id,
                "line_ids": [
                    # Sale of goods, purchase of goods and a non-monetary aid
                    Command.create({"account_id": cls._account("430"), "debit": 1000}),
                    Command.create({"account_id": cls._account("700"), "credit": 1000}),
                    Command.create({"account_id": cls._account("600"), "debit": 400}),
                    Command.create({"account_id": cls._account("400"), "credit": 400}),
                    Command.create({"account_id": cls._account("651"), "debit": 100}),
                    Command.create({"account_id": cls._account("572"), "credit": 100}),
                ],
            }
        )
        move.action_post()

    @classmethod
    def _account(cls, prefix):
        account = cls.env["account.account"].search(
            [
                ("code", "=like", f"{prefix}%"),
                ("company_ids", "in", cls.env.company.ids),
            ],
            limit=1,
        )
        return account.id

    def _compute(self, report_xmlid, kpi_names):
        report = self.env.ref(report_xmlid)
        instance = (
            self.env["mis.report.instance"]
            .with_user(self.accountant)
            .create(
                {
                    "name": report.name,
                    "report_id": report.id,
                    "company_id": self.env.company.id,
                    "period_ids": [
                        Command.create(
                            {
                                "name": "2025",
                                "mode": "fix",
                                "manual_date_from": "2025-01-01",
                                "manual_date_to": "2025-12-31",
                            }
                        )
                    ],
                }
            )
        )
        rows = {row["label"]: row for row in instance.compute()["body"]}
        values = {}
        for name in kpi_names:
            kpi = report.kpi_ids.filtered(lambda k, name=name: k.name == name)
            values[name] = round(rows[kpi.description]["cells"][0].get("val") or 0, 2)
        return values

    def test_profit_loss_abbreviated(self):
        values = self._compute(
            "l10n_es_mis_report.mis_report_es_pyg_abreviado", ["es49500"]
        )
        self.assertEqual(values["es49500"], 500)

    def test_profit_loss_normal(self):
        values = self._compute(
            "l10n_es_mis_report.mis_report_es_pyg_normal", ["es49500"]
        )
        self.assertEqual(values["es49500"], 500)

    def test_profit_loss_sme(self):
        values = self._compute(
            "l10n_es_mis_report.mis_report_es_pyg_pymes", ["es49500"]
        )
        self.assertEqual(values["es49500"], 500)

    def test_profit_loss_sme_sfl(self):
        values = self._compute(
            "l10n_es_mis_report.mis_report_es_pyg_pyme_sfl",
            ["es40200", "es40310", "es40320", "es40600", "es44000"],
        )
        self.assertEqual(values["es40200"], 1000)
        self.assertEqual(values["es40310"], 0)
        self.assertEqual(values["es40320"], -100)
        self.assertEqual(values["es40600"], -400)
        self.assertEqual(values["es44000"], 500)
