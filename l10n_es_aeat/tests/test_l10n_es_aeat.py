# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestL10nEsAeat(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsAeat, self).setUp()
        self.export_model = self.env["l10n.es.aeat.report.export_to_boe"]

    def test_format_string(self):
        text = " &'(),-./01:;abAB_ÇÑ\"áéíóúÁÉÍÓÚ+!"
        self.assertEqual(
            self.export_model._format_string(text, len(text)),
            " &'(),-./01:;ABAB_ÇÑAEIOUAEIOU   ".encode('iso-8859-1'))
