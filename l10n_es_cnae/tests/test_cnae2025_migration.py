# Copyright 2026 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.l10n_es_cnae.hooks import (
    CNAE2009_CNAE2025,
    NACE21_SPLIT,
    NAMESPACE,
    migrate_to_cnae2025,
    read_cnae2025,
)


class TestCnae2025Migration(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.industry = cls.env["res.partner.industry"].with_context(active_test=False)
        cls.nace = cls.industry._get_nace_map()
        cls.cnae = cls.industry._get_nace_map(NAMESPACE)

        # CNAE 2009 subclasses, as the previous version of the module created
        # them. The installation already created the CNAE 2025 ones.
        def old(code, name):
            return cls.industry.create({"name": name, "full_name": f"{code} - {name}"})

        cls.hydro = old("35.15", "Production of hydro-electric electricity")
        cls.residential = old("41.21", "Construction of residential buildings (2009)")
        cls.fish = old("10.21", "Processing of fish (2009)")
        partner = cls.env["res.partner"]
        cls.dam = partner.create({"name": "Dam", "industry_id": cls.hydro.id})
        cls.builder = partner.create(
            {
                "name": "Builder",
                "industry_id": cls.residential.id,
                "secondary_industry_ids": [(6, 0, cls.hydro.ids)],
            }
        )
        cls.cannery = partner.create({"name": "Cannery", "industry_id": cls.fish.id})

    def test_data(self):
        rows = read_cnae2025()
        self.assertEqual(len(rows), 25)
        codes = {row["code"] for row in rows}
        kept = {row["nace2_code"] for row in rows if row["nace2_code"]}
        self.assertEqual(len(kept), 14)
        self.assertLessEqual(kept, codes)
        self.assertFalse(set(CNAE2009_CNAE2025) & codes)
        # CNAE 2025 = NACE Rev. 2.1 + these subclasses
        self.assertFalse(codes & set(self.nace))
        for row in rows:
            self.assertIn(row["parent_code"], self.nace)
        self.assertLessEqual(NACE21_SPLIT, set(self.nace))

    def test_install(self):
        """Installing the module creates the CNAE 2025 subclasses."""
        # CNAE 2025 = NACE Rev. 2.1 - the 12 classes split in Spain + 25 subclasses
        self.assertEqual(len(self.cnae), len(self.nace) - 12 + 25)
        self.assertEqual(self.cnae["62.10"], self.nace["62.10"])
        self.assertNotIn("25.11", self.cnae)
        self.assertIn("25.13", self.cnae)
        subclass = self.industry.browse(self.cnae["41.01"])
        self.assertEqual(subclass.name, "Construction of residential buildings")
        self.assertEqual(subclass.parent_id.id, self.nace["41.0"])

    def test_migration(self):
        migrate_to_cnae2025(self.env)
        self.assertEqual(self.industry._get_nace_map(NAMESPACE), self.cnae)
        # 35.15 is another activity in NACE Rev. 2.1: archived and moved
        self.assertFalse(self.hydro.active)
        self.assertEqual(self.dam.industry_id.id, self.nace["35.12"])
        self.assertEqual(
            self.industry.browse(self.nace["35.15"]).name, "Trade of electricity"
        )
        # 41.21 becomes CNAE 2025 41.01
        self.assertFalse(self.residential.active)
        self.assertEqual(self.builder.industry_id.id, self.cnae["41.01"])
        self.assertEqual(self.builder.secondary_industry_ids.ids, [self.nace["35.12"]])
        # 10.21 keeps its activity, and its CNAE 2025 industry already exists
        self.assertFalse(self.fish.active)
        self.assertEqual(self.cannery.industry_id.id, self.cnae["10.21"])

    def test_rerun(self):
        migrate_to_cnae2025(self.env)
        before = self.industry.search([]).read(["name", "active", "parent_id"])
        migrate_to_cnae2025(self.env)
        after = self.industry.search([]).read(["name", "active", "parent_id"])
        self.assertEqual(after, before)

    def test_spanish_names(self):
        self.env["res.lang"]._activate_lang("es_ES")
        migrate_to_cnae2025(self.env)
        subclass = self.industry.browse(self.cnae["41.01"])
        self.assertEqual(
            subclass.with_context(lang="es_ES").name,
            "Construcción de edificios residenciales",
        )
