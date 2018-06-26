# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2018 Valentin Vinagre <valentin.vinagre@qubiq.es>
# Copyright Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging
from openerp.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase

_logger = logging.getLogger('aeat.296')


class TestL10nEsAeatMod296Base(TestL10nEsAeatModBase):
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

    def test_model_296(self):
        # Set supplier as non-resident
        self.supplier.is_non_resident = True
        # Purchase invoices
        self._invoice_purchase_create('2015-01-01')
        self._invoice_purchase_create('2015-01-02')
        self._invoice_purchase_create('2017-01-02')
        # Create model
        export_config = self.env.ref(
            'l10n_es_aeat_mod296.aeat_mod296_main_export_config')
        self.model296 = self.env['l10n.es.aeat.mod296.report'].create({
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
        })
        _logger.debug('Calculate AEAT 296 1T 2015')
        self.model296.button_calculate()
        self.assertEqual(self.model296.casilla_02, self.taxes_result['2'])
        self.assertEqual(self.model296.casilla_03, self.taxes_result['3'])
        self.assertEqual(self.model296.casilla_04, 0.0)
        self.assertEqual(len(self.model296.lines296), 1)
        self.supplier.is_non_resident = False
        self.model296.button_calculate()
        self.assertEqual(self.model296.casilla_02, 0.0)
        self.assertEqual(self.model296.casilla_03, 0.0)
        self.assertEqual(self.model296.casilla_04, 0.0)
        self.assertEqual(len(self.model296.lines296), 0)
