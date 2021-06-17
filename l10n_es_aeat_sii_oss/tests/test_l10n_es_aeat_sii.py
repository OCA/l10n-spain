# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_es_aeat_sii.tests.test_l10n_es_aeat_sii import \
    TestL10nEsAeatSiiBase


class TestL10nEsAeatSiiBaseOss(TestL10nEsAeatSiiBase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatSiiBaseOss, cls).setUpClass()
        account_fiscal_position_env = cls.env["account.fiscal.position"]
        xml_id = '%s_account_tax_template_s_oss20' % cls.company.id
        cls.tax_fr_20 = cls._get_or_create_tax(
            xml_id, "Test tax 20%", "sale", 20, cls.account_tax)
        cls.tax_fr_20.write({
            "oss_country_id": cls.env.ref("base.fr").id
        })
        cls.fpos_fr_id = account_fiscal_position_env.create({
            "name": "Intra-EU FR B2C",
            "company_id": cls.company.id,
            "vat_required": False,
            "auto_apply": True,
            'country_id': cls.env.ref("base.fr").id,
            'fiscal_position_type': 'b2c',
            'sii_registration_key_sale': cls.env.ref(
                "l10n_es_aeat_sii_oss.aeat_sii_oss_mapping_registration_keys_1").id,
            'sii_exempt_cause': 'none',
            'sii_partner_identification_type': '2',
        })

    def test_invoice_sii_oss(self):
        self.partner.sii_simplified_invoice = True
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'date_invoice': '2021-07-01',
            'date': '2021-07-01',
            'type': 'out_invoice',
            'fiscal_position_id': self.fpos_fr_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account.id,
                    'name': 'Test line with iva FR',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_ids': [(6, 0, self.tax_fr_20.ids)],
                })],
            'sii_manual_description': '/',
        })
        invoices = invoice._get_sii_invoice_dict()
        ImporteTotal = invoices[
            'FacturaExpedida']['ImporteTotal']
        ClaveRegimenEspecialOTrascendencia = invoices[
            'FacturaExpedida']['ClaveRegimenEspecialOTrascendencia']
        self.assertEqual(100, ImporteTotal)
        self.assertEqual("17", ClaveRegimenEspecialOTrascendencia)
