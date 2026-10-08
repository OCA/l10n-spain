# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo.tests.common import TransactionCase
from odoo.tools import file_open, pycompat


class TestL10nEsCnae(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("es_ES")

    def test_create_spanish_industries(self):
        wizard = self.env["res.partner.industry.eu.nace.wizard"].create({})
        wizard.create_spanish_industries()
        with file_open("l10n_es_cnae/data/res.partner.industry.csv", "rb") as csvfile:
            reader = pycompat.csv_reader(csvfile, delimiter=",", quotechar='"')
            all_naces = self.env["res.partner.industry"].search_read(
                [("full_name", "like", " - ")], ["full_name"]
            )
            nace_map = {
                nace.get("full_name").split(" - ")[0]: nace.get("id")
                for nace in all_naces
            }
            for row in reader:
                self.assertTrue(row[2] in nace_map)
                nace = self.env["res.partner.industry"].browse(nace_map[row[2]])
                self.assertEqual(nace.with_context(lang="es_ES").name, row[4])
