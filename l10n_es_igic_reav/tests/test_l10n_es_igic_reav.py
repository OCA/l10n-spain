from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestL10nEsIgicReav(TransactionCase):
    def _check_coa_loading(self, coa):
        company = self.env["res.company"].create({"name": f"Canary Company {coa}"})
        self.env["account.chart.template"].try_loading(
            coa, company=company, install_demo=False
        )
        self.assertEqual(company.chart_template, coa, "Created with wrong COA")

    def test_01_es_pymes_canary(self):
        self._check_coa_loading("es_pymes_canary")

    def test_02_es_full_canary(self):
        self._check_coa_loading("es_full_canary")
