# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase
from odoo import exceptions

_logger = logging.getLogger('aeat.303')


class TestL10nEsAeatMod303OSSBase(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False

    taxes_sale = {
        'EU-OSS-VAT-PT-23': (81.3, 18.7),
        'EU-OSS-VAT-PT-13': (88.5, 11.5),
        'EU-OSS-VAT-PT-6': (93.3, 5.6),
    }

    taxes_result = {
        '123': (3 * (81.3 + 88.5 + 93.3)) - (1 * (81.3 + 88.5 + 93.3)),  # EU-OSS-VAT-PT-x
    }


    def setUp(self):
        super(TestL10nEsAeatMod303OSSBase, self).setUp()
        self.export_config = self.env.ref(
            'l10n_es_aeat_mod303.aeat_mod303_202107_main_export_config')
        # Create model
        self.model303 = self.env['l10n.es.aeat.mod303.report'].create({
            'name': '9990000000303',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': '2021-08-01',
            'date_end': '2021-08-31',
            'export_config_id': self.export_config.id,
            'journal_id': self.journal_misc.id,
        })
        self.model303_4t = self.model303.copy({
            'name': '9994000000303',
            'period_type': '4T',
            'date_start': '2021-09-01',
            'date_end': '2021-12-31',
        })
        self._create_oss_taxes_pt()

    def _get_taxes(self, descs):
        """
        Need to include taxes without templates (OSS wizard)
        """
        taxes = self.env['account.tax']
        for desc in descs.split(','):
            parts = desc.split('.')
            module = parts[0] if len(parts) > 1 else 'l10n_es'
            xml_id = parts[1] if len(parts) > 1 else parts[0]
            if xml_id.lower() != xml_id and len(parts) == 1:
                # shortcut for not changing existing tests with old codes
                xml_id = 'account_tax_template_' + xml_id.lower()
            tax_template = self.env.ref(
                '%s.%s' % (module, xml_id), raise_if_not_found=False)
            if tax_template:
                tax = self.company.get_taxes_from_templates(tax_template)
                taxes |= tax
            if not tax_template or not tax and 'EU-OSS' in desc:
                taxes_eu_oss = self.env['account.tax'].search([
                    ('oss_country_id', '!=', False),
                    ('company_id', '=', self.company.id)
                ])
                if not taxes_eu_oss:
                    _logger.error("Tax not found: {}".format(desc))
                else:
                    taxes |= taxes_eu_oss
        return taxes

    def _create_oss_taxes_pt(self):
        self.country_pt_id = self.env['res.country'].search([('code', '=', 'PT')], limit=1)
        self.eu_oss_vat_pt_6 = self.env['account.tax'].create({
            'name': 'Test OSS for EU to Portugal: 6.0',
            'description': 'EU-OSS-VAT-PT-6',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 6.,
            'oss_country_id': self.country_pt_id.id
        })
        self.eu_oss_vat_pt_13 = self.env['account.tax'].create({
            'name': 'Test OSS for EU to Portugal: 13.0',
            'description': 'EU-OSS-VAT-PT-13',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 13.,
            'oss_country_id': self.country_pt_id.id
        })
        self.eu_oss_vat_pt_23 = self.env['account.tax'].create({
            'name': 'Test OSS for EU to Portugal: 23.0',
            'description': 'EU-OSS-VAT-PT-23',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 23.,
            'oss_country_id': self.country_pt_id.id
        })


class TestL10nEsAeatMod303OSS(TestL10nEsAeatMod303OSSBase):

    def setUp(self):
        super(TestL10nEsAeatMod303OSS, self).setUp()
        # Sale invoices
        self._invoice_sale_create('2021-08-01')
        self._invoice_sale_create('2021-08-02')
        sale = self._invoice_sale_create('2021-08-03')
        self._invoice_refund(sale, '2021-08-04')

    def _check_tax_lines(self):
        for field, result in iter(self.taxes_result.items()):
            _logger.debug('Checking tax line: %s' % field)
            lines = self.model303.tax_line_ids.filtered(
                lambda x: x.field_number == int(field))
            self.assertAlmostEqual(
                sum(lines.mapped('amount')), result, 2,
                "Incorrect result in field %s" % field
            )

    def test_model_303(self):
        map_line_123 = self.env.ref('l10n_es_aeat_mod303_oss.aeat_mod303_map_line_123')
        map_line_126 = self.env.ref('l10n_es_aeat_mod303_oss.aeat_mod303_map_line_126')
        self.assertTrue(map_line_123)
        self.assertTrue(map_line_126)

        # Test default counterpart
        self.assertEqual(self.model303._default_counterpart_303().id,
                         self.accounts['475000'].id)
        _logger.debug('Calculate AEAT 303 1T 2017')
        self.model303.button_calculate()
        self.assertEqual(self.model303.state, 'calculated')
        # Fill manual fields
        # self.model303.write({
        #     'porcentaje_atribuible_estado': 95,
        #     'potential_cuota_compensar': 250,
        #     'cuota_compensar': 250,
        #     'casilla_77': 455,
        # })
        # self.assertAlmostEqual(self.model303.remaining_cuota_compensar, 0)
        if self.debug:
            self._print_tax_lines(self.model303.tax_line_ids)

        self._check_tax_lines()

