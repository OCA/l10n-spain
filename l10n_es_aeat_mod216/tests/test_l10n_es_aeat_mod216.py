# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.216")


class TestL10nEsAeatMod216Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "l10n_es_irnr.account_tax_template_p_irpfnrnue24p": (1000, 240),
        "l10n_es_irnr.account_tax_template_p_irpfnrue19p": (2000, 380),
        "l10n_es_irnr.account_tax_template_p_irpfnrnue0p": (3000, 0),
    }
    taxes_result = {
        # Rendimientos del trabajo (dinerarios) - Base
        "2": 12000,
        # Rendimientos del trabajo (dinerarios) - Retenciones
        "3": 1240,  # (2 * 240) + (2 * 380) + (2 * 0)
    }

    def test_model_216(self):
        # Purchase invoices
        self._invoice_purchase_create("2015-01-01")
        self._invoice_purchase_create("2015-01-02")
        purchase = self._invoice_purchase_create("2015-01-03")
        self._invoice_refund(purchase, "2015-01-18")
        # Create model
        self.model216 = self.env["l10n.es.aeat.mod216.report"].create(
            {
                "name": "9990000000216",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2015,
                "period_type": "1T",
                "date_start": "2015-01-01",
                "date_end": "2015-03-31",
                "journal_id": self.journal_misc.id,
                "counterpart_account_id": self.accounts["475000"].id,
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 216 1T 2015")
        self.model216.button_calculate()
        # Fill manual fields
        self.model216.write(
            {
                # Resultados a ingresar anteriores
                "casilla_06": 145,
            }
        )
        # Check tax lines
        for box, result in self.taxes_result.items():
            _logger.debug("Checking tax line: %s" % box)
            lines = self.model216.tax_line_ids.filtered(
                lambda x: x.field_number == int(box)
            )
            self.assertEqual(round(sum(lines.mapped("amount")), 2), round(result, 2))
        # Check result
        _logger.debug("Checking results")
        retenciones = self.taxes_result.get("3", 0.0)
        result = retenciones - 145
        self.assertEqual(self.model216.casilla_01, 1)
        self.assertEqual(round(self.model216.casilla_03, 2), round(retenciones, 2))
        self.assertEqual(round(self.model216.casilla_07, 2), round(result, 2))
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_config_xml_ids = [
            "l10n_es_aeat_mod216.aeat_mod216_main_export_config",
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(export_to_boe._export_config(self.model216, export_config))
