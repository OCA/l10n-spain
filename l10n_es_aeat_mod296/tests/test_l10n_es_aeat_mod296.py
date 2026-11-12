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
        self._invoice_purchase_create("2025-01-01")
        self._invoice_purchase_create("2025-01-02")
        self._invoice_purchase_create("2027-01-02")
        # Create model
        self.model296 = self.env["l10n.es.aeat.mod296.report"].create(
            {
                "name": "2960000000001",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2025,
                "period_type": "0A",
                "date_start": "2025-01-01",
                "date_end": "2025-12-31",
                "journal_id": self.journal_misc.id,
            }
        )
        _logger.debug("Calculate AEAT 296 0A 2025")
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
        # Export to BOE through the report button
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=self.model296.id, active_model=self.model296._name)
            .create({})
        )
        wizard.action_get_file()
        content = wizard.data.content.decode("iso-8859-1")
        # The declarant record starts with its NIF and name
        self.assertEqual(
            content[:57], "12962025123456789" + "SPANISH TEST COMPANY".ljust(40)
        )
