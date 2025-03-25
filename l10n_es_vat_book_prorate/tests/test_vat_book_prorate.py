# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging

from odoo import fields

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.vat.book")


class TestL10nEsAeatVatBookProrate(TestL10nEsAeatModBase):
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21S": (1500, 315),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IVA21_SC": (230, 48.3),
        "P_IVA0_ND": (100, 21),
        "P_IVA21_IC_BC": (200, 42),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.env.company.write(
            {
                "vat": "ES12345678Z",
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    (0, 0, {"date": fields.date(2024, 1, 1), "vat_prorate": 80}),
                ],
            }
        )

    def test_vat_book_prorate(self):
        """
        Test VAT Book with VAT Prorate
        """
        self._invoice_purchase_create("2024-01-01")
        vat_book = self.env["l10n.es.vat.book"].create(
            {
                "name": "Test VAT Book",
                "company_id": self.env.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2024,
                "period_type": "1T",
                "date_start": "2024-01-01",
                "date_end": "2024-03-31",
            }
        )
        _logger.debug("Calculate VAT Book 1T 2024")
        vat_book.button_calculate()
        self.assertRecordValues(
            vat_book.mapped("received_line_ids.tax_line_ids"),
            [
                {"tax_amount": 48.3, "deductible_amount": 38.64},
                {"tax_amount": 21.0, "deductible_amount": 21.0},
                {"tax_amount": 42.0, "deductible_amount": 33.6},
            ],
        )
