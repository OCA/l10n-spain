# Copyright 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import SavepointCase


class TestClosingMoves(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestClosingMoves, cls).setUpClass()
        partner = cls.env["res.partner"].create({
            "name": "Test Partner",
        })
        Invoice = cls.env["account.invoice"]
        cls.invoice_out = Invoice.create({
            "partner_id": partner.id,
            "type": "out_invoice",
            "invoice_line_ids": [(0, 0, {
                "quantity": 1.0,
                "name": "Great Product",
                "price_unit": 1000.0,
                "account_id": cls.env.ref("l10n_es.1_account_common_7000").id,
            })]
        })
        cls.invoice_out.action_invoice_open()
        cls.invoice_in = Invoice.create({
            "partner_id": partner.id,
            "type": "in_invoice",
            "invoice_line_ids": [(0, 0, {
                "quantity": 1.0,
                "name": "Great Product",
                "price_unit": 500.0,
                "account_id": cls.env.ref("l10n_es.1_account_common_600").id,
            })]
        })
        cls.invoice_in.action_invoice_open()

    def test_opening_move(self):
        """Test opening move"""
        wiz = self.env["trial.balance.report.wizard"].create({
            "date_from": "{}-01-01".format(fields.Date.today().year),
            "date_to": "{}-12-31".format(fields.Date.today().year),
            "opening_closing_move": True,
            "move_type": "opening",
        })
        wiz._onchange_opening_closing_move()
        model = self.env["report_trial_balance"]
        report = model.create(wiz._prepare_report_trial_balance())
        report.compute_data_for_report()
        report.print_report("xlsx")
        self.env["ir.actions.report"]._get_report_from_name(
            "o_c.report_opening_closing_xlsx"
        ).render_xlsx(report.ids, None)

    def test_closing_move(self):
        """Test closing move"""
        wiz = self.env["trial.balance.report.wizard"].create({
            "date_from": "{}-01-01".format(fields.Date.today().year),
            "date_to": "{}-12-31".format(fields.Date.today().year),
            "opening_closing_move": True,
            "move_type": "closing",
        })
        wiz._onchange_opening_closing_move()
        model = self.env["report_trial_balance"]
        report = model.create(wiz._prepare_report_trial_balance())
        report.compute_data_for_report()
        report.print_report("xlsx")
        self.env["ir.actions.report"]._get_report_from_name(
            "o_c.report_opening_closing_xlsx"
        ).render_xlsx(report.ids, None)
