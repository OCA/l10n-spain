# Copyright 2026 MDSX - Manuel Diez Silva
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.exceptions import UserError, ValidationError

from .common import TestVerifactuCommon


class TestVerifactuSubstitution(TestVerifactuCommon):
    """Invoices issued in substitution of simplified ones (canje, F3).

    Reference: AEAT, "Aclaraciones a dudas de los desarrolladores" v1.3
    (4-dic-2025), section 27, and art. 15.6 §2 of RD 1619/2012.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_21 = cls.env.ref(
            f"account.{cls.company.id}_account_tax_template_s_iva21b"
        )
        cls.simplified_partner = cls.env["res.partner"].create(
            {
                "name": "Cliente de mostrador",
                "aeat_simplified_invoice": True,
                "country_id": cls.env.ref("base.es").id,
            }
        )

    def _create_invoice(self, partner=None, amount=100, date="2026-01-01"):
        return self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": (partner or self.partner).id,
                "invoice_date": date,
                "move_type": "out_invoice",
                "fiscal_position_id": self.fp_nacional.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "account_id": self.account_expense.id,
                            "name": "Test line",
                            "price_unit": amount,
                            "quantity": 1,
                            "tax_ids": [Command.set(self.tax_21.ids)],
                        },
                    )
                ],
            }
        )

    def _create_simplified_invoice(self, **kwargs):
        """A posted F2, already registered in the chain."""
        invoice = self._create_invoice(partner=self.simplified_partner, **kwargs)
        invoice.action_post()
        return invoice

    def test_no_substitution_is_a_regular_invoice(self):
        invoice = self._create_invoice()
        self.assertEqual(invoice._get_verifactu_document_type(), "F1")
        self.assertEqual(invoice._get_verifactu_substituted_documents(), [])

    def test_substitution_document_type(self):
        simplified = self._create_simplified_invoice()
        self.assertEqual(simplified._get_verifactu_document_type(), "F2")
        canje = self._create_invoice()
        canje.verifactu_substituted_invoice_ids = simplified
        self.assertEqual(canje._get_verifactu_document_type(), "F3")

    def test_substitution_payload(self):
        simplified = self._create_simplified_invoice()
        canje = self._create_invoice()
        canje.verifactu_substituted_invoice_ids = simplified
        canje.action_post()
        alta = canje._get_verifactu_invoice_dict()["RegistroAlta"]
        self.assertEqual(alta["TipoFactura"], "F3")
        self.assertEqual(
            alta["FacturasSustituidas"],
            {
                "IDFacturaSustituida": [
                    {
                        "IDEmisorFactura": self.company.partner_id._parse_aeat_vat_info()[
                            2
                        ],
                        "NumSerieFactura": simplified.name,
                        "FechaExpedicionFactura": "01-01-2026",
                    }
                ]
            },
        )
        # An F3 always carries the destinatario and never claims art. 6.1.d
        self.assertIn("Destinatarios", alta)
        self.assertNotIn("FacturaSinIdentifDestinatarioArt61d", alta)
        # Substituting is not rectifying
        self.assertNotIn("TipoRectificativa", alta)
        self.assertNotIn("FacturasRectificadas", alta)

    def test_substitution_payload_several_simplified_invoices(self):
        """One F3 may replace many simplified invoices."""
        first = self._create_simplified_invoice(date="2026-01-01")
        second = self._create_simplified_invoice(date="2026-01-02")
        canje = self._create_invoice(date="2026-01-03")
        canje.verifactu_substituted_invoice_ids = first + second
        canje.action_post()
        alta = canje._get_verifactu_invoice_dict()["RegistroAlta"]
        substituted = alta["FacturasSustituidas"]["IDFacturaSustituida"]
        self.assertEqual(
            [x["NumSerieFactura"] for x in substituted], [first.name, second.name]
        )
        self.assertEqual(
            [x["FechaExpedicionFactura"] for x in substituted],
            ["01-01-2026", "02-01-2026"],
        )

    def test_substitution_hash_literal(self):
        """The hash covers TipoFactura, but not the substituted invoices."""
        simplified = self._create_simplified_invoice()
        canje = self._create_invoice()
        canje.verifactu_substituted_invoice_ids = simplified
        canje.action_post()
        self.assertIn("TipoFactura=F3&", canje.verifactu_hash_string)
        self.assertNotIn("Sustitu", canje.verifactu_hash_string)

    def test_substituted_invoice_is_left_alone(self):
        """The substituted invoice is neither cancelled nor rectified."""
        simplified = self._create_simplified_invoice()
        entry = simplified.last_verifactu_invoice_entry_id
        canje = self._create_invoice()
        canje.verifactu_substituted_invoice_ids = simplified
        canje.action_post()
        self.assertEqual(simplified.state, "posted")
        self.assertEqual(simplified.last_verifactu_invoice_entry_id, entry)
        self.assertEqual(entry.entry_type, "register")

    def test_substitution_requires_customer_vat(self):
        """An F3 without destinatario is not valid."""
        simplified = self._create_simplified_invoice()
        canje = self._create_invoice(partner=self.simplified_partner)
        canje.verifactu_substituted_invoice_ids = simplified
        with self.assertRaisesRegex(UserError, "identify the customer"):
            canje.action_post()

    def test_substitution_requires_an_identifiable_customer(self):
        """A VAT number alone is not enough if it cannot be placed in a country.

        Without a country the receiver goes out as an IDOtro with no
        CodigoPais, which declares a foreign document of nowhere for what is
        actually a Spanish NIF.
        """
        countryless = self.env["res.partner"].create(
            {"name": "Cliente sin país", "vat": "89890001K"}
        )
        self.assertFalse(countryless._is_valid_verifactu_receiver())
        simplified = self._create_simplified_invoice()
        canje = self._create_invoice(partner=countryless)
        canje.verifactu_substituted_invoice_ids = simplified
        # The savepoint undoes the posting the same way the failed transaction
        # does in real use, leaving the invoice in draft to be corrected.
        with self.assertRaisesRegex(UserError, "identify the customer"):
            with self.env.cr.savepoint():
                canje.action_post()
        self.assertEqual(canje.state, "draft")
        countryless.country_id = self.env.ref("base.es")
        self.assertTrue(countryless._is_valid_verifactu_receiver())
        canje.action_post()
        alta = canje._get_verifactu_invoice_dict()["RegistroAlta"]
        self.assertEqual(alta["Destinatarios"]["IDDestinatario"]["NIF"], "89890001K")

    def test_substituted_invoice_must_be_registered(self):
        """Only an already declared simplified invoice can be substituted."""
        never_sent = self._create_invoice(partner=self.simplified_partner)
        canje = self._create_invoice()
        canje.verifactu_substituted_invoice_ids = never_sent
        with self.assertRaisesRegex(UserError, "never registered at VERI"):
            canje.action_post()

    def test_substituted_invoice_must_be_simplified(self):
        ordinary = self._create_invoice()
        ordinary.action_post()
        canje = self._create_invoice()
        canje.verifactu_substituted_invoice_ids = ordinary
        with self.assertRaisesRegex(UserError, "not a simplified"):
            canje.action_post()

    def test_substitution_only_once(self):
        """A simplified invoice can only be exchanged for one ordinary invoice."""
        simplified = self._create_simplified_invoice()
        first = self._create_invoice()
        first.verifactu_substituted_invoice_ids = simplified
        first.action_post()
        second = self._create_invoice()
        with self.assertRaises(ValidationError):
            second.verifactu_substituted_invoice_ids = simplified
            second.flush_recordset()

    def test_invoice_cannot_substitute_itself(self):
        invoice = self._create_invoice()
        with self.assertRaises(ValidationError):
            invoice.verifactu_substituted_invoice_ids = invoice
            invoice.flush_recordset()
