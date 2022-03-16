# Copyright 2019-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase


class TestL10nEsAeatMod347(TestL10nEsAeatModBase):
    def setUp(self):
        super(TestL10nEsAeatMod347, self).setUp()
        # Create model
        self.model347 = self.env['l10n.es.aeat.mod347.report'].create({
            'name': '9990000000347',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2019,
            'date_start': '2019-01-01',
            'date_end': '2019-12-31',
        })
        self.customer_2 = self.customer.copy({
            'name': 'Test customer 2',
            'vat': 'ES12345678Z',
        })
        self.customer_3 = self.customer.copy({'name': 'Test customer 3'})
        self.customer_4 = self.customer.copy({
            'name': 'Test customer 4',
            'vat': 'ESB29805314',
        })
        self.customer_5 = self.customer.copy({
            'name': 'Test customer 5',
            # For testing spanish states mapping
            'country_id': self.env.ref('base.es').id,
            'vat': '12345678Z',
        })
        self.customer_6 = self.customer.copy({
            'name': 'Test customer 6',
            'country_id': self.env.ref('base.es').id,
            'vat': 'B29805314',
        })
        self.supplier_2 = self.supplier.copy({'name': 'Test supplier 2'})
        # Invoice lower than the limit
        self.taxes_sale = {
            'S_IVA10B': (2000, 200),
        }
        self.invoice_1 = self._invoice_sale_create('2019-01-01')
        # Invoice higher than limit with IRPF
        self.taxes_sale = {
            'S_IVA10S,S_IRPF20': (4000, 400),
        }
        self.invoice_2 = self._invoice_sale_create('2019-04-01', {
            'partner_id': self.customer_2.id,
        })
        # Invoice higher than limit manually excluded
        self.invoice_3 = self._invoice_sale_create('2019-01-01', {
            'partner_id': self.customer_3.id,
            'not_in_mod347': True,
        })
        # Invoice higher than cash limit
        self.taxes_sale = {
            'S_IVA10S': (6000, 600),
        }
        self.invoice_4 = self._invoice_sale_create('2019-07-01', {
            'partner_id': self.customer_4.id,
        })
        self.invoice_4.pay_and_reconcile(self.journal_cash, date='2019-07-01')
        # Invoice outside period higher than cash limit
        self.invoice_5 = self._invoice_sale_create('2018-01-01', {
            'partner_id': self.customer_5.id,
        })
        self.invoice_5.pay_and_reconcile(self.journal_cash, date='2019-01-01')
        # Customer refund higher than limit
        self.taxes_sale = {
            'S_IVA10S': (5000, 500),
        }
        self.invoice_5 = self._invoice_sale_create('2019-01-01', {
            'partner_id': self.customer_6.id,
            'type': 'out_refund',
        })
        # Purchase invoice higher than the limit
        self.taxes_purchase = {
            'P_IVA10_SC': (3000, 300),
        }
        self.invoice_suppler_1 = self._invoice_purchase_create('2019-01-01')
        # Supplier refund higher than limit
        self.taxes_purchase = {
            'P_IVA10_SC': (4000, 400),
        }
        self.invoice_suppler_2 = self._invoice_purchase_create('2019-01-01', {
            'partner_id': self.supplier_2.id,
            'type': 'in_refund',
        })

    def test_model_347(self):
        # Check flag propagation
        self.assertFalse(self.invoice_1.move_id.not_in_mod347)
        self.assertTrue(self.invoice_3.move_id.not_in_mod347)
        # Check model
        self.model347.button_calculate()
        partner_record_vals = [
            # key, partner, amount, cash_amount, 1T, 2T, 3T, 4T
            ('A', self.supplier, 3300, 0, 3300, 0, 0, 0),
            ('A', self.supplier_2, -4400, 0, -4400, 0, 0, 0),
            ('B', self.customer_2, 4400, 0, 0, 4400, 0, 0),
            ('B', self.customer_4, 6600, 6600, 0, 0, 6600, 0),
            ('B', self.customer_6, -5500, 0, -5500, 0, 0, 0),
            ('B', self.customer_5, 0, 6600, 0, 0, 0, 0),
        ]
        self.assertEqual(
            self.model347.total_partner_records, len(partner_record_vals))
        self.assertAlmostEqual(
            self.model347.total_amount,
            sum([x[2] for x in partner_record_vals]))
        self.assertAlmostEqual(
            self.model347.total_cash_amount,
            sum([x[3] for x in partner_record_vals]))
        for vals in partner_record_vals:
            partner_record = self.model347.partner_record_ids.filtered(
                lambda x: x.partner_id == vals[1])
            self.assertEqual(partner_record.operation_key, vals[0])
            self.assertAlmostEqual(partner_record.amount, vals[2])
            self.assertAlmostEqual(partner_record.cash_amount, vals[3])
            self.assertAlmostEqual(partner_record.first_quarter, vals[4])
            self.assertAlmostEqual(partner_record.second_quarter, vals[5])
            self.assertAlmostEqual(partner_record.third_quarter, vals[6])
            self.assertAlmostEqual(partner_record.fourth_quarter, vals[7])
        # Check VAT handle
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_2)
        self.assertEqual(partner_record.partner_vat, '12345678Z')
        self.assertEqual(partner_record.partner_country_code, 'ES')
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_4)
        self.assertEqual(partner_record.partner_vat, 'B29805314')
        self.assertEqual(partner_record.partner_country_code, 'ES')
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_5)
        self.assertEqual(partner_record.partner_vat, '12345678Z')
        self.assertEqual(partner_record.partner_country_code, 'ES')
        partner_record = self.model347.partner_record_ids.filtered(
            lambda x: x.partner_id == self.customer_6)
        self.assertEqual(partner_record.partner_vat, 'B29805314')
        self.assertEqual(partner_record.partner_country_code, 'ES')
        # Export to BOE
        export_to_boe = self.env['l10n.es.aeat.report.export_to_boe'].create({
            'name': 'test_export_to_boe.txt',
        })
        export_config_xml_ids = [
            'l10n_es_aeat_mod347.aeat_mod347_main_export_config',
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(
                export_to_boe._export_config(self.model347, export_config)
            )
