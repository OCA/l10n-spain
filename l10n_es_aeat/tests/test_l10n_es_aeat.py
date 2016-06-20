# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common


class TestL10nEsAeat(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsAeat, self).setUp()
        self.export_model = self.env["l10n.es.aeat.report.export_to_boe"]

    def test_format_string(self):
        text = u" &'(),-./01:;abAB_ÇÑ\"áéíóúÁÉÍÓÚ+!"
        self.assertEqual(
            self.export_model._formatString(text, len(text)),
            u" &'(),-./01:;ABAB_ÇÑ\"AEIOUAEIOU  ".encode('iso-8859-1'))
