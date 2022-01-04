# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


class TestL10nEsAeatSiiBaseOss(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatSiiBaseOss, cls).setUpClass()
        account_fiscal_position_env = cls.env["account.fiscal.position"]
        xml_id = "%s_account_tax_template_s_oss20" % cls.company.id
        cls.tax_fr_20 = cls._get_or_create_tax(xml_id, "Test tax 20%", "sale", 20)
        cls.tax_fr_20.write({"oss_country_id": cls.env.ref("base.fr").id})
        cls.fpos_fr_id = account_fiscal_position_env.create(
            {
                "name": "Intra-EU FR B2C",
                "company_id": cls.company.id,
                "vat_required": False,
                "auto_apply": True,
                "country_id": cls.env.ref("base.fr").id,
                "fiscal_position_type": "b2c",
                "sii_registration_key_sale": cls.env.ref(
                    "l10n_es_aeat_sii_oss.aeat_sii_oss_mapping_registration_keys_1"
                ).id,
                "sii_exempt_cause": "none",
                "sii_partner_identification_type": "2",
            }
        )

    def test_invoice_sii_oss(self):
        self.partner.sii_simplified_invoice = True
        invoice_form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        invoice_form.partner_id = self.partner
        invoice_form.invoice_date = "2021-07-01"
        invoice_form.fiscal_position_id = self.fpos_fr_id
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.price_unit = 100
            line_form.quantity = 1
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax_fr_20)
        invoice = invoice_form.save()
        res = invoice._get_sii_invoice_dict()
        res_issue = res["FacturaExpedida"]
        self.assertEqual(res_issue["ImporteTotal"], 100)
        self.assertEqual(res_issue["ClaveRegimenEspecialOTrascendencia"], "17")
