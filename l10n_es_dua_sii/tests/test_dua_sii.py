# Copyright 2019 Tecnativa - Alexandre Díaz
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


class TestL10nEsDuaSii(TestL10nEsAeatSiiBase):
    def test_dua_sii(self):
        invoice = self._create_and_test_invoice_sii_dict(
            inv_type="in_invoice",
            lines=[(100, ["p_iva21_ibc"])],
            extra_vals={
                "ref": "sup0001",
                "sii_account_registration_date": "2020-10-01",
                "currency_id": self.usd.id,
            },
            module="l10n_es_dua_sii",
        )
        self.assertTrue(invoice.sii_dua_invoice)

    def test_not_dua_sii(self):
        invoice = self._create_and_test_invoice_sii_dict(
            inv_type="in_invoice",
            lines=[(100, ["p_iva10_bc"])],
            extra_vals={
                "ref": "sup0001",
                "sii_account_registration_date": "2020-10-01",
            },
            module="l10n_es_dua_sii",
        )
        self.assertFalse(invoice.sii_dua_invoice)
