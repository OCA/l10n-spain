# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import TestL10nEsTicketBAIAPI


class TestL10nEsTicketBAITaxAgency(TestL10nEsTicketBAIAPI):
    def test_tbai_tax_agency_change(self):
        self.main_company.tbai_tax_agency_id = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa"
        )
        self.main_company.onchange_tbai_tax_agency()
        self.assertTrue(self.main_company.tbai_test_available)
        self.assertTrue(self.main_company.tbai_pro_available)
        self.main_company.tbai_tax_agency_id.test_qr_base_url = False
        self.main_company.onchange_tbai_tax_agency()
        self.assertFalse(self.main_company.tbai_test_available)
        self.main_company.tbai_tax_agency_id = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_araba"
        )
        self.main_company.onchange_tbai_tax_agency()
        self.assertTrue(self.main_company.tbai_test_available)
        self.assertTrue(self.main_company.tbai_pro_available)
        self.main_company.tbai_tax_agency_id.test_qr_base_url = False
        self.main_company.tbai_tax_agency_id.qr_base_url = ""
        self.main_company.onchange_tbai_tax_agency()
        self.assertFalse(self.main_company.tbai_test_available)
        self.assertFalse(self.main_company.tbai_pro_available)
