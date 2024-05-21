from odoo.tests import tagged

from .common import SequraCommon


@tagged("post_install", "-at_install")
class SequraTest(SequraCommon):
    def test_compatible_providers(self):
        providers = self.env["payment.provider"]._get_compatible_providers(
            partner_id=self.partner.id,
            amount=0,
            currency_id=self.currency_euro.id,
            company_id=self.company.id,
        )
        self.assertIn(self.sequra, providers)
