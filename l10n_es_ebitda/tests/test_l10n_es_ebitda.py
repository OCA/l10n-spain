# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo.tests.common import TransactionCase


class TestL10nEsEbitda(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_pro = cls.env.ref("account_ebitda_report.mis_report_ebitda_pro")
        cls.company = cls.env.user.company_id

        cls.instance = cls.env["mis.report.instance"].create(
            {
                "name": "Test ES EBITDA",
                "report_id": cls.report_pro.id,
                "company_id": cls.company.id,
            }
        )
        cls.env["mis.report.instance.period"].create(
            {
                "name": "Current Year",
                "report_instance_id": cls.instance.id,
                "manual_date_from": "2026-01-01",
                "manual_date_to": "2026-12-31",
            }
        )

    def test_01_es_report_expressions(self):
        """Ensure Spanish localized expressions are syntactically valid."""
        matrix = self.instance._compute_matrix()
        self.assertTrue(
            matrix,
            "The Spanish report matrix should be generated without errors",
        )
