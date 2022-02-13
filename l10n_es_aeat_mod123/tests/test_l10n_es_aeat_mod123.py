# Copyright 2017 Creu Blanca
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.123")


class TestL10nEsAeatMod123(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_RP19": (100, -19),
        "l10n_es.account_tax_template_p_rrD19": (1000, -190),
    }
    taxes_result = {"2": 3 * (100 + 1000), "3": 3 * (19 + 190)}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Purchase invoices
        cls._invoice_purchase_create("2017-01-01")
        cls._invoice_purchase_create("2017-01-02")
        cls._invoice_purchase_create("2017-01-03")
        export_config = cls.env.ref(
            "l10n_es_aeat_mod123.aeat_mod123_main_export_config"
        )
        cls.model123_new = cls.env["l10n.es.aeat.mod123.report"].new(
            {
                "name": "9990000000123",
                "company_id": cls.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "1T",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
                "export_config_id": export_config.id,
                "journal_id": cls.journal_misc.id,
                "counterpart_account_id": cls.accounts["475000"].id,
                "tipo_declaracion": "I",
            }
        )

    def test_model_123(self):
        self.assertEqual(self.model123_new.company_id.id, self.company.id)
        self.assertEqual(
            self.model123_new.counterpart_account_id.id, self.accounts["475000"].id
        )
        self.assertEqual(self.model123_new.journal_id.id, self.journal_misc.id)
        model123 = self.env["l10n.es.aeat.mod123.report"].create(
            self.model123_new._convert_to_write(self.model123_new._cache)
        )
        _logger.debug("Calculate AEAT 123 1T 2017")
        model123.button_calculate()
        # Fill manual fields
        if self.debug:
            self._print_tax_lines(model123.tax_line_ids)
        # Check tax lines
        for box, result in self.taxes_result.items():
            _logger.debug("Checking tax line: %s" % box)
            lines = model123.tax_line_ids.filtered(lambda x: x.field_number == int(box))
            self.assertAlmostEqual(sum(lines.mapped("amount")), result, 2)
        # Check result
        _logger.debug("Checking results")
        self.assertEqual(model123.casilla_08, 0 + 0 + 3 * (19 + 190))
