# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import common
from .common import TestL10nEsTicketBAIAPI


@common.at_install(False)
@common.post_install(True)
class TestL10nEsTicketBAITaxAgency(TestL10nEsTicketBAIAPI):

    def test_tbai_tax_agency_change(self):
        self.main_company.tbai_tax_agency_id = self.env.ref(
            'l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa'
        )
        self.main_company.onchange_tbai_tax_agency()
        self.assertTrue(self.main_company.tbai_test_available)
        self.main_company.tbai_tax_agency_id.test_qr_base_url = False
        self.main_company.onchange_tbai_tax_agency()
        self.assertFalse(self.main_company.tbai_test_available)
