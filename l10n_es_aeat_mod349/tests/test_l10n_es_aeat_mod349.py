# -*- coding: utf-8 -*-
# Copyright 2017 - Eficent Business and IT Consulting Services, S.L.
#                  <contact@eficent.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging
from openerp.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase

_logger = logging.getLogger('aeat.349')


class TestL10nEsAeatMod349Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        'S_IVA0_IC': (2400, 0),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        'P_IVA21_IC_BC': (300, 0),
    }

    def test_model_349(self):
        # Add some test data
        self.customer.vat = 'BE0411905847'
        self.customer.country_id = self.env.ref('base.be')
        self.supplier.vat = 'BG0000100159'
        self.supplier.country_id = self.env.ref('base.bg')
        # Data for 1T 2017
        # Purchase invoices
        p1 = self._invoice_purchase_create('2017-01-01')
        self._invoice_purchase_create('2017-01-02')
        # Sale invoices
        s1 = self._invoice_sale_create('2017-01-01')
        self._invoice_sale_create('2017-01-02')
        # Create model
        model349 = self.env['l10n.es.aeat.mod349.report'].create({
            'name': '3490000000001',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': '2017-01-01',
            'date_end': '2017-03-31',
        })
        # Calculate
        _logger.debug('Calculate AEAT 349 1T 2017')
        model349.button_calculate()
        self.assertEqual(model349.total_partner_records, 2)
        # p1 + p2 + s1 + s2 = 2400 + 2400 + 300 + 300
        self.assertEqual(model349.total_partner_records_amount, 5400.00)
        self.assertEqual(model349.total_partner_refunds, 0)
        self.assertEqual(model349.total_partner_refunds_amount, 0.0)
        a_records = model349.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'A')
        self.assertEqual(len(a_records), 1)
        a_record = a_records[0]
        self.assertTrue(a_record.partner_vat,  self.supplier.vat)
        self.assertTrue(a_record.country_id, self.supplier.country_id)
        # s1 + s2 = 300 + 300
        self.assertTrue(a_record.total_operation_amount, 600)
        e_records = model349.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'E')
        self.assertEqual(len(a_records), 1)
        e_record = e_records[0]
        self.assertTrue(e_record.partner_vat, self.customer.vat)
        self.assertTrue(e_record.country_id, self.customer.country_id)
        # p1 + p2
        self.assertTrue(e_record.total_operation_amount, 4800)
        # Now we delete p1 and recompute
        record = model349.partner_record_detail_ids.filtered(
            lambda x: x.invoice_id == p1)
        record.unlink()
        e_records = model349.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'E')
        e_record = e_records[0]
        self.assertTrue(e_record.total_operation_amount, 2400)
        record = model349.partner_record_detail_ids.filtered(
            lambda x: x.invoice_id == s1)
        record.unlink()
        a_records = model349.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'A')
        a_record = a_records[0]
        self.assertTrue(a_record.total_operation_amount, 300)

        # Create a complementary presentation for 1T 2017. We expect the
        #  application to propose the records that were not included in the
        # first presentation.
        model349_c = self.env['l10n.es.aeat.mod349.report'].create({
            'name': '3490000000002',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'C',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': '2017-01-01',
            'date_end': '2017-03-31',
            'previous_number': model349.name,
        })
        # Calculate
        _logger.debug('Calculate AEAT 349 1T 2017 - complementary')
        model349_c.button_calculate()
        e_records = model349_c.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'E')
        e_record = e_records[0]
        self.assertTrue(e_record.total_operation_amount, 2400)
        a_records = model349_c.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'A')
        a_record = a_records[0]
        self.assertTrue(a_record.total_operation_amount, 300)

        # Create a substitutive presentation for 1T 2017. We expect that all
        # records for 1T are proposed.
        model349_s = self.env['l10n.es.aeat.mod349.report'].create({
            'name': '3490000000003',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'S',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': '2017-01-01',
            'date_end': '2017-03-31',
            'previous_number': model349.name,
        })
        # Calculate
        _logger.debug('Calculate AEAT 349 1T 2017 - substitutive')
        model349_s.button_calculate()
        e_records = model349_s.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'E')
        e_record = e_records[0]
        self.assertTrue(e_record.total_operation_amount, 4800)
        a_records = model349_s.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'A')
        a_record = a_records[0]
        self.assertTrue(a_record.total_operation_amount, 600)
        # Create a substitutive presentation for 2T 2017.
        # We create a refund of p1, and a new sale
        self._invoice_refund(p1, '2017-04-01')
        self._invoice_sale_create('2017-04-01')
        model349_2t = self.env['l10n.es.aeat.mod349.report'].create({
            'name': '3490000000004',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': '2017-04-01',
            'date_end': '2017-06-30',
        })
        # Calculate
        _logger.debug('Calculate AEAT 349 2T 2017')
        model349_2t.button_calculate()
        self.assertEqual(model349_2t.total_partner_records, 1)
        self.assertEqual(model349_2t.total_partner_refunds, 1)
        e_records = model349_2t.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'E')
        e_record = e_records[0]
        self.assertTrue(e_record.total_operation_amount, 2400)
        a_records = model349_2t.partner_record_ids.filtered(
            lambda x: x.operation_key.code == 'A')
        self.assertEqual(len(a_records), 0)
        e_refunds = model349_2t.partner_refund_ids.filtered(
            lambda x: x.operation_key.code == 'E')
        self.assertEqual(len(e_refunds), 0)
        a_refunds = model349_2t.partner_refund_ids.filtered(
            lambda x: x.operation_key.code == 'A')
        self.assertEqual(len(a_refunds), 1)
        a_refund = a_refunds[0]
        self.assertTrue(a_refund.total_operation_amount, 0)
        self.assertTrue(a_refund.total_origin_amount, 300)
        self.assertTrue(a_refund.period_type, model349_s.period_type)
