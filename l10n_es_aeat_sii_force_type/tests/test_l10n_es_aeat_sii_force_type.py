# © 2024 FactorLibre - Alejandro Ji Cheung <alejandro.jicheung@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests import common, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestL10nEsAeatSiiForceType(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.company = cls.env.ref("base.main_company")
        cls.company.sii_enabled = True
        cls.company.vat = "ES98765432M"
        cls.fiscal_position = cls.env["account.fiscal.position"].create(
            {
                "name": "Test fiscal position",
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.env.ref("base.res_partner_2").id,
                "fiscal_position_id": cls.fiscal_position.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "quantity": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

    @mute_logger("odoo.models", "odoo.models.unlink", "odoo.addons.base.ir.ir_model")
    def test_get_sii_header(self):
        # Tests with sii_allow_force_communication_type = False
        self.fiscal_position.sii_allow_force_communication_type = False
        self.assertFalse(self.fiscal_position.sii_allow_force_communication_type)
        self.invoice._onchange_sii_allow_force_communication_type()
        self.assertFalse(self.invoice._get_sii_header().get("TipoComunicacion"))

        # Tests with sii_allow_force_communication_type = True
        self.fiscal_position.sii_allow_force_communication_type = True
        self.fiscal_position.sii_forced_communication_type = "A0"
        self.assertTrue(self.fiscal_position.sii_allow_force_communication_type)
        self.assertEqual(self.fiscal_position.sii_forced_communication_type, "A0")
        self.invoice._onchange_sii_allow_force_communication_type()
        self.assertEqual(self.invoice._get_sii_header().get("TipoComunicacion"), "A0")
        self.fiscal_position.sii_forced_communication_type = "A1"
        self.assertEqual(self.fiscal_position.sii_forced_communication_type, "A1")
        self.invoice._onchange_sii_allow_force_communication_type()
        self.assertEqual(self.invoice._get_sii_header().get("TipoComunicacion"), "A1")
