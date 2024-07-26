# © 2023 FactorLibre - Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSii,
)


class TestL10nEsAeatSiiTaxfree(TestL10nEsAeatSii):
    def test_tax_free_sii(self):
        """Test that the invoice is correctly generated."""
        fiscal_position = self.env["account.fiscal.position"].create(
            {
                "name": "Test fiscal position",
            }
        )
        invoice = self._create_invoice_for_sii("out_invoice")
        invoice.fiscal_position_id = fiscal_position
        invoice.fiscal_position_id.write({"sii_refund_as_regular": False})
        self.assertFalse(invoice.fiscal_position_id.sii_refund_as_regular)
        invoice.partner_id.commercial_partner_id.write(
            {"sii_simplified_invoice": False}
        )
        self.assertFalse(
            invoice.partner_id.commercial_partner_id.sii_simplified_invoice
        )
        inv_dict = invoice._get_sii_invoice_dict_out()
        self.assertEqual(inv_dict["FacturaExpedida"]["TipoFactura"], "F1")

        invoice_1 = self._create_invoice_for_sii("out_invoice")
        invoice_1.fiscal_position_id = fiscal_position
        invoice_1.fiscal_position_id.write({"sii_refund_as_regular": True})
        self.assertTrue(invoice_1.fiscal_position_id.sii_refund_as_regular)
        invoice_1.partner_id.commercial_partner_id.write(
            {"sii_simplified_invoice": True}
        )
        self.assertTrue(
            invoice_1.partner_id.commercial_partner_id.sii_simplified_invoice
        )
        inv_dict_1 = invoice_1._get_sii_invoice_dict_out()
        self.assertEqual(inv_dict_1["FacturaExpedida"]["TipoFactura"], "F2")
        self.assertFalse(inv_dict_1["FacturaExpedida"].get("TipoRectificativa", False))
        self.assertFalse(inv_dict_1["FacturaExpedida"].get("ImporteTotal", False))
