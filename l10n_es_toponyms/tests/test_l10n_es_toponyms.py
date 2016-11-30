# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests import common


class TestL10nEsToponyms(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsToponyms, self).setUp()
        self.wizard = self.env['config.es.toponyms'].create({
            'name': '',
            'state': 'official',
            'city_info': 'yes'
        })

    def test_official_state_names(self):
        self.wizard.with_context(max_import=10).execute()
        self.assertEqual(
            self.env.ref('l10n_es_toponyms.ES01').name,
            'Araba')

    def test_spanish_state_names(self):
        self.wizard.state = 'spanish'
        self.wizard.with_context(max_import=10).execute()
        self.assertEqual(
            self.env.ref('l10n_es_toponyms.ES01').name,
            'Alava')

    def test_both_state_names(self):
        self.wizard.state = 'both'
        self.wizard.with_context(max_import=10).execute()
        self.assertEqual(
            self.env.ref('l10n_es_toponyms.ES01').name,
            'Alava / Araba')
