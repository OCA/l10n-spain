# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase

_logger = logging.getLogger('aeat.216')


class TestL10nEsAeatMod216Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase = {
        # tax code: (base, tax_amount)
        'P_IRPFT': (1000, 210),
        'P_IRPFTD': (2000, 420),
        'P_IRPFTE': (3000, 630),
        'P_IRPF1': (4000, 40),
        'P_IRPF2': (5000, 100),
        'P_IRPF7': (6000, 420),
        'P_IRPF9': (7000, 630),
        'P_IRPF15': (8000, 1200),
        'P_IRPF18': (9000, 1620),
        'P_IRPF19': (100, 19),
        'P_IRPF20': (200, 40),
        'P_IRPF21P': (300, 63),
    }
    taxes_result = {
        # Rendimientos del trabajo (dinerarios) - Base
        '2': (
            (2 * 1000) + (2 * 2000) +  # P_IRPFT, P_IRPFTD
            (2 * 3000) + (2 * 4000) +  # P_IRPFTE, P_IRPF1
            (2 * 5000) + (2 * 6000) +  # P_IRPF2, P_IRPF7
            (2 * 7000) + (2 * 8000) +  # P_IRPF9, P_IRPF15
            (2 * 9000) + (2 * 100) +   # P_IRPF18, P_IRPF19
            (2 * 200) + (2 * 300)      # P_IRPF20, P_IRPF21P
        ),
        # Rendimientos del trabajo (dinerarios) - Retenciones
        '3': (
            (2 * 210) + (2 * 420) +   # P_IRPFT, P_IRPFTD
            (2 * 630) + (2 * 40) +    # P_IRPFTE, P_IRPF1
            (2 * 100) + (2 * 420) +   # P_IRPF2, P_IRPF7
            (2 * 630) + (2 * 1200) +  # P_IRPF9, P_IRPF15
            (2 * 1620) + (2 * 19) +   # P_IRPF18, P_IRPF19
            (2 * 40) + (2 * 63)       # P_IRPF20, P_IRPF21P
        ),
    }

    def test_model_216(self):
        # Set supplier as non-resident
        self.supplier.is_non_resident = True
        # Purchase invoices
        self._invoice_purchase_create('2015-01-01')
        self._invoice_purchase_create('2015-01-02')
        purchase = self._invoice_purchase_create('2015-01-03')
        self._invoice_refund(purchase, '2015-01-18')
        # Create model
        export_config = self.env.ref(
            'l10n_es_aeat_mod216.aeat_mod216_main_export_config')
        self.model216 = self.env['l10n.es.aeat.mod216.report'].create({
            'name': '9990000000216',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2015,
            'period_type': '1T',
            'date_start': '2015-01-01',
            'date_end': '2015-03-31',
            'export_config_id': export_config.id,
            'journal_id': self.journal_misc.id,
            'counterpart_account_id': self.accounts['475000'].id
        })
        # Calculate
        _logger.debug('Calculate AEAT 216 1T 2015')
        self.model216.button_calculate()
        # Fill manual fields
        self.model216.write({
            # Resultados a ingresar anteriores
            'casilla_06': 145,
        })
        # Check tax lines
        for box, result in self.taxes_result.iteritems():
            _logger.debug('Checking tax line: %s' % box)
            lines = self.model216.tax_line_ids.filtered(
                lambda x: x.field_number == int(box))
            self.assertEqual(
                round(sum(lines.mapped('amount')), 2),
                round(result, 2))
        # Check result
        _logger.debug('Checking results')
        retenciones = self.taxes_result.get('3', 0.)
        result = retenciones - 145
        self.assertEqual(self.model216.casilla_01, 1)
        self.assertEqual(
            round(self.model216.casilla_03, 2), round(retenciones, 2))
        self.assertEqual(
            round(self.model216.casilla_07, 2), round(result, 2))
