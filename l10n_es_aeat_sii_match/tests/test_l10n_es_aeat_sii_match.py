# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


class TestL10nEsAeatSiiMatch(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                test_queue_job_no_delay=True,  # no jobs thanks
            )
        )
        cls.invoice.action_post()
        cls.invoice = cls.env[cls.invoice._name].browse(cls.invoice.id)

    def test_invoice_diffs_values(self):
        self._activate_certificate()
        invoice = self.invoice
        invoice.aeat_state = "sent"
        invoice.sii_csv = invoice._get_aeat_invoice_dict()
        res = invoice._get_diffs_values(invoice.sii_csv)
        self.assertEqual(res, [])
