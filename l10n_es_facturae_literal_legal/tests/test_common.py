# Copyright 2025 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import exceptions
from odoo.tests import tagged

from odoo.addons.l10n_es_facturae.tests.common import CommonTest


@tagged("post_install", "-at_install")
class CommonTestLiteralLegal(CommonTest):
    def _create_move(self):
        return self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )

    def _post_and_generate(self, move):
        move.action_post()
        move.name = "2999/99999"
        self._activate_certificate(self.certificate_password)
        return self._create_facturae_file(move, force=True)

    def _legal_reference_texts(self, generated_facturae):
        ns = {"fe": self.fe}
        legal_literal_xpath = (
            "/fe:Facturae/Invoices/Invoice/LegalLiterals/LegalReference"
        )
        nodes = generated_facturae.xpath(legal_literal_xpath, namespaces=ns)
        return [node.text for node in nodes]

    def test_facturae_with_literal_legals(self):
        long_description = "A" * 250 + "B" * 250 + "C" * 100
        self.move.write(
            {
                "literal_legal_ids": [
                    (0, 0, {"description": long_description, "sequence": 7})
                ]
            }
        )

        self.assertEqual(
            len(self.move.literal_legal_ids),
            3,
            "A long literal should be split into multiple records.",
        )
        literals = self.move.literal_legal_ids.sorted("id")
        self.assertEqual(literals[0].description, "A" * 250)
        self.assertEqual(literals[1].description, "B" * 250)
        self.assertEqual(literals[2].description, "C" * 100)
        self.assertEqual(literals.mapped("sequence"), [7, 7, 7])

        generated_facturae = self._post_and_generate(self.move)
        texts = self._legal_reference_texts(generated_facturae)

        # The base module may render its own legal notes from taxes first;
        # ours are appended after them.
        self.assertGreaterEqual(len(texts), 3)
        self.assertEqual(texts[-3:], ["A" * 250, "B" * 250, "C" * 100])

        with self.assertRaises(
            exceptions.ValidationError,
            msg="Should not be able to write a description longer than 250 chars.",
        ):
            literals[0].write({"description": "D" * 300})

    def test_facturae_without_literal_legals_keeps_tax_legal_notes(self):
        """Base legal notes from taxes must survive without literal legals."""
        move = self._create_move()
        generated_facturae = self._post_and_generate(move)

        texts = self._legal_reference_texts(generated_facturae)
        self.assertIn("Legal note for tax", texts)
