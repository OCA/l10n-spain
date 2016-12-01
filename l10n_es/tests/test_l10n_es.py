# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common


class TestL10nEs(common.TransactionCase):
    def setUp(self):
        super(TestL10nEs, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test company',
        })
        config_obj = self.env['account.config.settings']
        config = config_obj.new({
            'company_id': self.company.id,
        })
        config.onchange_company_id()
        self.config = config_obj.create(
            config._convert_to_write(config._cache))

    def test_install_l10n_es_full(self):
        self.config.chart_template_id = self.env.ref(
            'l10n_es.account_chart_template_full')
        self.config.onchange_chart_template_id()
        # This should end without errors
        self.config.set_chart_of_accounts()

    def test_install_l10n_es_pymes(self):
        self.config.chart_template_id = self.env.ref(
            'l10n_es.account_chart_template_pymes')
        self.config.onchange_chart_template_id()
        # This should end without errors
        self.config.set_chart_of_accounts()

    def test_install_l10n_es_assoc(self):
        self.config.chart_template_id = self.env.ref(
            'l10n_es.account_chart_template_assoc')
        self.config.onchange_chart_template_id()
        # This should end without errors
        self.config.set_chart_of_accounts()
