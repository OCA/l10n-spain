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
        "l10n_es.account_tax_template_p_irpfnrnue24p": (1000, 240),
        "l10n_es.account_tax_template_p_irpfnrue19p": (2000, 380),
        "l10n_es.account_tax_template_p_irpfnrnue0p": (3000, 0),
    }
    taxes_result = {
        # Rendimientos del trabajo (dinerarios) - Base
        "2": 12000,
        # Rendimientos del trabajo (dinerarios) - Retenciones
        "3": 1240,  # (2 * 240) + (2 * 380) + (2 * 0)
    }

    def test_model_216_before_2024(self):
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
                "casilla_06_pre_2024": 145,
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
        self.assertEqual(self.model216.casilla_01_pre_2024, 1)
        self.assertEqual(
            round(self.model216.casilla_03_pre_2024, 2), round(retenciones, 2)
        )
        self.assertEqual(round(self.model216.casilla_07_pre_2024, 2), round(result, 2))
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

    def test_model_216_2024(self):
        self.taxes_result = {
            # Resto de rentas - Rendimientos del trabajo (dinerarios) - Base
            "9": 12000,
            # Restos de rentas - Rendimientos del trabajo (dinerarios) - Retenciones
            "12": 1240,  # (2 * 240) + (2 * 380) + (2 * 0)
        }
        # Purchase invoices
        self._invoice_purchase_create("2024-01-01")
        self._invoice_purchase_create("2024-01-02")
        purchase = self._invoice_purchase_create("2024-01-03")
        self._invoice_refund(purchase, "2024-01-18")
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
                "year": 2024,
                "period_type": "1T",
                "date_start": "2024-01-01",
                "date_end": "2024-03-31",
                "journal_id": self.journal_misc.id,
                "counterpart_account_id": self.accounts["475000"].id,
            }
        )
        # Calculate
        _logger.debug("Calculate AEAT 216 1T 2024")
        self.model216.button_calculate()
        # Fill manual fields
        self.model216.write(
            {
                # Num. rentas dividendos sometidas
                "casilla_05": 2,
                # Base rentas dividendos sometidas
                "casilla_08": 200,
                # Retenciones rentas dividendos sometidas
                "casilla_11": 38,
                # Num. rentas dividendos no sometidas
                "casilla_14": 1,
                # Num. rentas resto rentas no sometidas
                "casilla_15": 3,
                # Base dividendos rentas no sometidas
                "casilla_17": 180,
                # Base resto rentas no sometidas
                "casilla_18": 125,
                # Resultados a ingresar anteriores
                "casilla_20": 145,
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
        base = self.taxes_result.get("9", 0.0)
        retenciones = self.taxes_result.get("12", 0.0)
        result = retenciones + 38 - 145
        self.assertEqual(self.model216.casilla_06, 1)
        self.assertEqual(self.model216.casilla_07, 3)
        self.assertEqual(round(self.model216.casilla_09, 2), round(base, 2))
        self.assertEqual(round(self.model216.casilla_10, 2), round(base + 200, 2))
        self.assertEqual(round(self.model216.casilla_12, 2), round(retenciones, 2))
        self.assertEqual(round(self.model216.casilla_13, 2), round(retenciones + 38, 2))
        self.assertEqual(self.model216.casilla_16, 4)
        self.assertEqual(round(self.model216.casilla_19, 2), round(305, 2))
        self.assertEqual(round(self.model216.casilla_21, 2), round(result, 2))
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_config_xml_ids = [
            "l10n_es_aeat_mod216.aeat_mod216_2024_main_export_config",
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(export_to_boe._export_config(self.model216, export_config))
