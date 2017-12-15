# -*- coding: utf-8 -*-
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 \
    import TestL10nEsAeatMod303Base


class TestL10nEsAeatVatProrrate(TestL10nEsAeatMod303Base):
    def setUp(self):
        self.taxes_sale['S_IVA0'] = (2000, 0)  # Add exempt amount
        super(TestL10nEsAeatVatProrrate, self).setUp()
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general',
        })
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
            'type': 'other',
        })
        self.counterpart_account = self.env['account.account'].create({
            'name': 'Test counterpart account',
            'code': 'COUNTERPART',
            'user_type_id': self.account_type.id,
        })

    def test_vat_prorrate(self):
        export_config = self.env.ref(
            'l10n_es_aeat_mod303.aeat_mod303_main_export_config')
        model303 = self.env['l10n.es.aeat.mod303.report'].create({
            'name': '9990000000303',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': '2017-01-01',
            'date_end': '2017-03-31',
            'export_config_id': export_config.id,
            'journal_id': self.journal_misc.id,
            'counterpart_account_id': self.accounts['475000'].id
        })

        prorrate_regul_account = self.env['account.account'].search([
            ('code', 'like', '6391%'),
            ('company_id', '=', model303.company_id.id),
        ], limit=1)
        if not prorrate_regul_account:
            prorrate_regul_account = self.env['account.account'].create({
                'name': 'Test prorrate regularization account',
                'code': '6391000',
                'user_type_id': self.account_type.id,
            })

        model303.write({
            'vat_prorrate_type': 'general',
            'vat_prorrate_percent': 80,
            'journal_id': self.journal.id,
            'counterpart_account_id': self.counterpart_account.id,
        })
        model303_4t = model303.copy({
            'name': '9994000000303',
            'period_type': '4T',
            'date_start': '2017-09-01',
            'date_end': '2017-12-31',
        })

        # First semester
        model303.button_calculate()
        self.assertAlmostEqual(model303.total_deducir, 2043.82, 2)
        model303.create_regularization_move()
        self.assertAlmostEqual(len(model303.move_id.line_ids), 82, 2)
        lines = model303.move_id.line_ids
        line_counterpart = lines.filtered(
            lambda x: x.account_id == self.counterpart_account
        )
        self.assertAlmostEqual(line_counterpart.credit, 2036.18, 2)
        # Last semester
        wizard = self.env['l10n.es.aeat.compute.vat.prorrate'].with_context(
            active_id=model303_4t.id,
        ).create({
            'year': 2017,
        })
        wizard.button_compute()
        self.assertAlmostEqual(model303_4t.vat_prorrate_percent, 82, 2)
        model303_4t.button_calculate()
        self.assertAlmostEqual(model303_4t.casilla_44, 51.10, 2)
        self.assertEqual(
            model303_4t.prorrate_regularization_account_id,
            prorrate_regul_account,
        )
        model303_4t.create_regularization_move()
        lines = model303_4t.move_id.line_ids
        line_prorrate_regularization = lines.filtered(
            lambda x: x.account_id == prorrate_regul_account
        )
        self.assertAlmostEqual(line_prorrate_regularization.credit, 51.10, 2)
