# Copyright 2023 CreuBlanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import base64

from odoo.modules.module import get_module_resource

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsAeatMod115Base(TestL10nEsAeatModBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.vat = "ESA12345674"
        cls.seller = cls.env["res.partner"].create(
            {"vat": "ES59962470K", "name": "Seller"}
        )
        cls.invoice_data = open(
            get_module_resource(
                "l10n_es_account_import_facturae", "tests", "invoice.xsig"
            ),
            "rb",
        ).read()

    def test_update_invoice(self):
        move = (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create({})
        )
        self.assertEqual(move.amount_untaxed, 0.0)
        self.assertEqual(move.amount_total, 0.0)
        move.message_post(
            body="Import invoice", attachments=[("invoice.xsig", self.invoice_data)]
        )
        self.assertEqual(move.amount_untaxed, 147.0)
        self.assertEqual(move.amount_total, 177.87)

    def test_create_invoice(self):
        attachment = self.env["ir.attachment"].create(
            {"name": "invoice.xsig", "datas": base64.b64encode(self.invoice_data)}
        )
        move_action = self.env["account.journal"].create_invoice_from_attachment(
            attachment.ids
        )
        move = self.env[move_action["res_model"]].search(move_action["domain"])
        self.assertEqual(move.amount_untaxed, 147.0)
        self.assertEqual(move.amount_total, 177.87)
