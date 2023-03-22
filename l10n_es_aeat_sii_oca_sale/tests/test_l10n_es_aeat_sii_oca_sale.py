# Copyright 2023 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


class TestL10nEsAeatSiiOcaSale(TestL10nEsAeatSiiBase):
    def setUp(self):
        super().setUp()
        self.fp_1 = self.env["account.fiscal.position"].create(
            {
                "name": "FP1",
                "company_id": self.company.id,
                "sii_registration_key_sale": self.env.ref(
                    "l10n_es_aeat_sii_oca.aeat_sii_mapping_registration_keys_01"
                ).id,
            }
        )
        self.fp_2 = self.env["account.fiscal.position"].create(
            {
                "name": "FP2",
                "company_id": self.company.id,
                "sii_registration_key_sale": self.env.ref(
                    "l10n_es_aeat_sii_oca.aeat_sii_mapping_registration_keys_02"
                ).id,
            }
        )
        self.partner_fr = self.env["res.partner"].create(
            {
                "name": "French Customer",
                "vat": "FR23334175221",
                "country_id": self.env.ref("base.fr").id,
                "property_account_position_id": self.fp_1.id,
                "company_id": self.company.id,
            }
        )
        self.partner_us = self.env["res.partner"].create(
            {
                "name": "United state Customer",
                "vat": "US-whatever",
                "country_id": self.env.ref("base.us").id,
                "property_account_position_id": self.fp_2.id,
                "company_id": self.company.id,
            }
        )

    def test_registration_key_delivery_address(self):
        """When changing the delivery address, the registration key changes too."""
        inv_f = Form(
            self.env["account.move"].with_context(
                default_company_id=self.company.id, default_move_type="out_invoice"
            ),
            view="account.view_move_form",
        )
        inv_f.partner_id = self.partner_fr
        self.assertEqual(
            inv_f.sii_registration_key,
            inv_f.fiscal_position_id.sii_registration_key_sale,
        )
        inv_f.partner_shipping_id = self.partner_us
        self.assertEqual(
            inv_f.sii_registration_key,
            inv_f.fiscal_position_id.sii_registration_key_sale,
        )
