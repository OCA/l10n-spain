# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestSiiVerifactuExclusion(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_onchange_sii(self):
        company = self.env.company
        company.verifactu_enabled = True
        with self.assertRaises(ValidationError):
            with Form(company) as form:
                form.sii_enabled = True
        self.assertTrue(company.verifactu_enabled)
        self.assertFalse(company.sii_enabled)

    def test_02_onchange_verifactu(self):
        company = self.env.company
        company.sii_enabled = True
        with self.assertRaises(ValidationError):
            with Form(company) as form:
                form.verifactu_enabled = True
        self.assertTrue(company.sii_enabled)
        self.assertFalse(company.verifactu_enabled)

    def test_03_constrains_both_enabled(self):
        company = self.env.company
        company.sii_enabled = True
        with self.assertRaises(ValidationError), self.cr.savepoint():
            company.verifactu_enabled = True
