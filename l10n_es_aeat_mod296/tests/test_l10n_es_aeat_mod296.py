# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2018 Valentin Vinagre <valentin.vinagre@qubiq.es>
# Copyright Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging
from typing import ClassVar

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.296")


class TestL10nEsAeatMod296Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "l10n_es.account_tax_template_p_irpfnrnue24p": (1000, 240),
        "l10n_es.account_tax_template_p_irpfnrue19p": (2000, 380),
    }
    taxes_result: ClassVar[dict] = {
        # Rendimientos del trabajo (dinerarios) - Base
        "2": 6000,
        # Rendimientos del trabajo (dinerarios) - Retenciones
        "3": 1240,  # (2 * 240) + (2 * 380)
    }

    def test_model_296(self):
        # Purchase invoices
        self._invoice_purchase_create("2015-01-01")
        self._invoice_purchase_create("2015-01-02")
        self._invoice_purchase_create("2017-01-02")
        # Create model
        self.model296 = self.env["l10n.es.aeat.mod296.report"].create(
            {
                "name": "9990000000216",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2015,
                "period_type": "1T",
                "date_start": "2015-01-01",
                "date_end": "2015-03-31",
                "journal_id": self.journal_misc.id,
            }
        )
        _logger.debug("Calculate AEAT 296 1T 2015")
        self.model296.button_calculate()
        self.assertEqual(self.model296.casilla_02, self.taxes_result["2"])
        self.assertEqual(self.model296.casilla_03, self.taxes_result["3"])
        self.assertEqual(self.model296.casilla_04, 0.0)
        self.assertEqual(len(self.model296.lines296), 1)
        # The line keeps the base and retention move lines of its partner
        tax_move_lines = self.model296.tax_line_ids.filtered(
            lambda x: x.field_number in (2, 3)
        ).move_line_ids
        self.assertEqual(self.model296.lines296.move_line_ids, tax_move_lines)
        self.assertEqual(self.model296.lines296.partner_id, tax_move_lines.partner_id)
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_config = self.env.ref(
            "l10n_es_aeat_mod296.aeat_mod296_main_export_config"
        )
        content = export_to_boe._export_config(self.model296, export_config)
        # The declarant name is the company name
        self.assertIn(export_to_boe._format_string(self.company.name, 40), content)
