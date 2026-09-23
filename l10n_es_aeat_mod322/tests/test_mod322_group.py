# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestL10nEsAeatMod322Group(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Group = cls.env["l10n.es.aeat.mod322.group"]
        cls.dominant = cls.env["res.company"].create({"name": "Dominant"})
        cls.dependent = cls.env["res.company"].create({"name": "Dependent"})
        cls.other = cls.env["res.company"].create({"name": "Other"})

    def test_default_dependents_exclude_dominant(self):
        group = self.Group.with_context(
            allowed_company_ids=[self.dominant.id, self.dependent.id]
        ).create({"name": "IVA/2026/1"})
        self.assertEqual(group.main_company_id, self.dominant)
        self.assertEqual(group.company_ids, self.dependent)

    def test_dominant_cannot_be_dependent(self):
        with self.assertRaises(ValidationError):
            self.Group.create(
                {
                    "name": "IVA/2026/1",
                    "main_company_id": self.dominant.id,
                    "company_ids": [(6, 0, [self.dominant.id, self.dependent.id])],
                }
            )

    def test_company_in_one_group_only(self):
        self.Group.create(
            {
                "name": "IVA/2026/1",
                "main_company_id": self.dominant.id,
                "company_ids": [(6, 0, self.dependent.ids)],
            }
        )
        with self.assertRaises(ValidationError):
            self.Group.create(
                {
                    "name": "IVA/2026/2",
                    "main_company_id": self.other.id,
                    "company_ids": [(6, 0, self.dependent.ids)],
                }
            )
