# Copyright 2025 FactorLibre - Almudena de La Puente <almudena.delapuente@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command

from odoo.addons.l10n_es_verifactu_oca.tests.test_10n_es_verifactu import (
    TestL10nEsAeatVerifactu,
)


class TestL10nEsAeatVerifactuOSS(TestL10nEsAeatVerifactu):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        account_fiscal_position_env = cls.env["account.fiscal.position"]
        cls.tax_fr_20 = cls.env["account.tax"].create(
            {
                "name": "Test tax 20%",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 20,
                "oss_country_id": cls.env.ref("base.fr").id,
            }
        )
        cls.fpos_fr_id = account_fiscal_position_env.create(
            {
                "name": "Test FPOS OSS France",
                "company_id": cls.company.id,
                "vat_required": False,
                "auto_apply": True,
                "country_id": cls.env.ref("base.fr").id,
                "fiscal_position_type": "b2c",
            }
        )

    def test_invoice_verifactu_oss_tax_mapped(self):
        self.partner.aeat_simplified_invoice = True
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "invoice_date": "2026-01-01",
            "fiscal_position_id": self.fpos_fr_id.id,
            "verifactu_registration_key": self.fp_registration_key_01.id,
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "price_unit": 10,
                        "quantity": 1,
                        "tax_ids": [Command.set([self.tax_fr_20.id])],
                    },
                )
            ],
        }
        invoice = self.env["account.move"].create(invoice_vals)
        invoice.action_post()
        res = invoice._get_verifactu_invoice_dict_out()
        invoice_dict = res["RegistroAlta"]
        self.assertEqual(
            invoice_dict["Desglose"]["DetalleDesglose"][0]["CalificacionOperacion"],
            "N2",
        )
