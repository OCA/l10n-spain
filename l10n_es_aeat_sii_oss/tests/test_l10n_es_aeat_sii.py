# -*- coding: utf-8 -*-
# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common
from openerp import fields


class TestL10nEsAeatSiiOss(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsAeatSiiOss, self).setUp()
        account_fiscal_position_env = self.env["account.fiscal.position"]
        account_account_env = self.env['account.account']
        account_tax_code_env = self.env['account.tax.code']
        account_tax_env = self.env['account.tax']

        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'vat': 'ESF35999705'
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
        })
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account type',
            'code': 'TEST',
        })
        self.account_expense = account_account_env.create({
            'name': 'Test account',
            'code': 'EXP',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Test analytic account',
            'type': 'normal',
        })
        self.account_tax = account_account_env.create({
            'name': 'Test tax account',
            'code': 'TAX',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.base_code = account_tax_code_env.create({
            'name': '[28] Test base code',
            'code': 'OICBI',
        })
        self.tax_code = account_tax_code_env.create({
            'name': '[29] Test tax code',
            'code': 'SOICC',
        })
        self.tax_21 = account_tax_env.create({
            'name': 'Test tax 21%',
            'description': 'Test tax 21%',
            'type_tax_use': 'sale',
            'type': 'percent',
            'amount': '0.21',
            'account_collected_id': self.account_tax.id,
            'base_code_id': self.base_code.id,
            'base_sign': 1,
            'tax_code_id': self.tax_code.id,
            'tax_sign': 1,
        })
        self.tax_fr_20 = account_tax_env.create({
            'name': 'Test tax 20%',
            'description': 'Test tax 20%',
            'type_tax_use': 'sale',
            'type': 'percent',
            'amount': '0.20',
            'account_collected_id': self.account_tax.id,
            'base_code_id': self.base_code.id,
            'base_sign': 1,
            'tax_code_id': self.tax_code.id,
            'tax_sign': 1,
            'oss_country_id': self.env.ref("base.fr").id
        })
        self.journal = self.env['account.journal'].create({
            'type': 'bank',
            'name': 'Test bank',
            'code': 'BNKN',
        })
        self.fpos_fr_id = account_fiscal_position_env.create({
            "name": "Intra-EU FR B2C",
            "company_id": self.env.user.company_id.id,
            "vat_required": False,
            "auto_apply": True,
            'country_id': self.env.ref("base.fr").id,
            'fiscal_position_type': 'b2c',
            'sii_registration_key_sale': self.env.ref(
                "l10n_es_aeat_sii_oss.aeat_sii_oss_mapping_registration_keys_1").id,
            'sii_exempt_cause': 'none',
            'sii_partner_identification_type': '2',
        })

        self.partner.sii_simplified_invoice = True
        self.period = self.env['account.period'].find()
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'date_invoice': fields.Date.today(),
            'currency_id': self.env.ref('base.EUR').id,
            'type': 'out_invoice',
            'period_id': self.period.id,
            'fiscal_position': self.fpos_fr_id.id,
            'journal_id': self.journal.id,
            'account_id': self.account_expense.id,
            'invoice_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account.id,
                    'name': 'Test line with irpf and iva',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_id': [(6, 0, self.tax_fr_20.ids)],
                })],
            'sii_manual_description': '/',
        })

    def test_invoice_sii_oss(self):
        self.invoice.company_id.write({
            'sii_enabled': True,
            'sii_test': True,
            'use_connector': True,
            'chart_template_id': self.env.ref(
                'l10n_es.account_chart_template_pymes').id,
            'vat': 'FR00000000190',
        })
        invoices = self.invoice._get_sii_invoice_dict()
        ImporteTotal = invoices[
            'FacturaExpedida']['ImporteTotal']
        ClaveRegimenEspecialOTrascendencia = invoices[
            'FacturaExpedida']['ClaveRegimenEspecialOTrascendencia']
        self.assertEqual(100, ImporteTotal)
        self.assertEqual("17", ClaveRegimenEspecialOTrascendencia)
