# Copyright 2025 Process Control - Jorge Luis López
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .common import TestVerifactuCommon


class TestResPartner(TestVerifactuCommon):
    def test_partner_aeat_sending_enabled_computation(self):
        """Test computation of aeat_sending_enabled field"""
        # Test with company VERI*FACTU enabled
        partner_with_company = self.env["res.partner"].create(
            {
                "name": "Test Partner with Company",
                "company_id": self.company.id,
            }
        )
        partner_with_company._compute_aeat_sending_enabled()
        self.assertTrue(partner_with_company.aeat_sending_enabled)
        self.assertTrue(partner_with_company.verifactu_enabled)

        # Test with company VERI*FACTU disabled
        company_disabled = self.env["res.company"].create(
            {
                "name": "Test Company Disabled",
                "verifactu_enabled": False,
            }
        )
        partner_disabled = self.env["res.partner"].create(
            {
                "name": "Test Partner Disabled",
                "company_id": company_disabled.id,
            }
        )
        partner_disabled._compute_aeat_sending_enabled()
        self.assertFalse(partner_disabled.aeat_sending_enabled)
        self.assertFalse(partner_disabled.verifactu_enabled)

        # Test partner without specific company but with global VERI*FACTU enabled
        partner_no_company = self.env["res.partner"].create(
            {
                "name": "Test Partner No Company",
                "company_id": False,
            }
        )
        # Test when at least one company has VERI*FACTU enabled
        partner_no_company._compute_aeat_sending_enabled()
        self.assertTrue(partner_no_company.aeat_sending_enabled)
        self.assertTrue(partner_no_company.verifactu_enabled)
