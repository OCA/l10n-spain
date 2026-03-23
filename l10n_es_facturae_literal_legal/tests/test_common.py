# Copyright 2025 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import exceptions
from odoo.tests import tagged

from odoo.addons.l10n_es_facturae.tests.common import CommonTest


@tagged("post_install", "-at_install")
class CommonTestSpecialPayment(CommonTest):
    def test_facturae_with_literal_legals(self):
        self._activate_certificate(self.certificate_password)
        # Create a description of 600 characters.
        # This should be split into 3 records: 250, 250, and 100 chars.
        long_description = "A" * 250 + "B" * 250 + "C" * 100
        self.move.write(
            {"literal_legal_ids": [(0, 0, {"description": long_description})]}
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

        self.move.action_post()
        self.move.name = "2999/99999"
        generated_facturae = self._create_facturae_file(self.move, force=True)

        ns = {"fe": self.fe}
        legal_literal_xpath = (
            "/fe:Facturae/Invoices/Invoice/LegalLiterals/LegalReference"
        )
        legal_literal_nodes = generated_facturae.xpath(
            legal_literal_xpath, namespaces=ns
        )

        self.assertTrue(legal_literal_nodes)
        self.assertEqual(len(legal_literal_nodes), 3)

        self.assertEqual(legal_literal_nodes[0].text, "A" * 250)
        self.assertEqual(legal_literal_nodes[1].text, "B" * 250)
        self.assertEqual(legal_literal_nodes[2].text, "C" * 100)

        with self.assertRaises(
            exceptions.ValidationError,
            msg="Should not be able to write a description longer than 250 chars.",
        ):
            literals[0].write({"description": "D" * 300})
