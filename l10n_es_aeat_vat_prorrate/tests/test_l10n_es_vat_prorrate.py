# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from openerp.tests import common
from openerp.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 \
    import TestL10nEsAeatMod303Base


class TestL10nEsAeatVatProrrate(TestL10nEsAeatMod303Base,
                                common.TransactionCase):
    def setUp(self):
        super(TestL10nEsAeatVatProrrate, self).setUp()
        self.model303.vat_prorrate_type = 'general'
        self.model303.vat_prorrate_percent = 80
        self.model303.button_calculate()

    def test_deductable_part(self):
        self.assertEqual(self.model303.total_deducir, 32)

    def test_regularization_move(self):
        analytic_journal = self.env['account.analytic.journal'].create({
            'name': 'Test analytic journal',
            'type': 'purchase',
        })
        journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general',
            'analytic_journal_id': analytic_journal.id,
        })
        self.model303.journal_id = journal.id
        counterpart_account = self.env['account.account'].create({
            'name': 'Test counterpart account',
            'code': 'COUNTERPART',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.model303.counterpart_account = counterpart_account.id
        self.model303.create_regularization_move()
        self.assertEqual(len(self.model303.move_id.line_id), 5)
        lines = self.model303.move_id.line_id
        line_tax = lines.filtered(lambda x: x.account_id == self.account_tax)
        self.assertEqual(line_tax.credit, 40)
        line_counterpart = lines.filtered(
            lambda x: x.account_id == counterpart_account)
        self.assertEqual(line_counterpart.debit, 32)
        line_vat_prorrate_1 = lines.filtered(
            lambda x: (x.account_id == self.account_expense and
                       x.analytic_account_id == self.analytic_account_1))
        self.assertEqual(line_vat_prorrate_1.debit, 2)
        line_vat_prorrate_2 = lines.filtered(
            lambda x: (x.account_id == self.account_expense and
                       x.analytic_account_id == self.analytic_account_2))
        self.assertEqual(line_vat_prorrate_2.debit, 4)
        line_vat_prorrate_3 = lines.filtered(
            lambda x: (x.account_id == self.account_expense and
                       not x.analytic_account_id))
        self.assertEqual(line_vat_prorrate_3.debit, 2)
