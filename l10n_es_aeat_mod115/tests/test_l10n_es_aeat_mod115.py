# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from openerp.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase

_logger = logging.getLogger('aeat.115')


class TestL10nEsAeatMod115Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase = {
        # tax code: (base, tax_amount)
        'P_RAC19A': (1000, 190),
        'P_RAC195A': (2000, 390),
        'P_RAC20A': (3000, 600),
        'P_RAC21A': (4000, 840),
    }
    taxes_result = {
        # Base retenciones e ingresos a cuenta
        '2': (
            (2 * 1000) + (2 * 2000) +  # P_RAC19A, P_RAC195A
            (2 * 3000) + (2 * 4000)    # P_RAC20A, P_RAC21A
        ),
        # Retenciones e ingresos a cuenta
        '3': (
            (2 * 190) + (2 * 390) +  # P_RAC19A, P_RAC195A
            (2 * 600) + (2 * 840)    # P_RAC20A, P_RAC21A
        ),
    }

    def test_model_115(self):
        # Purchase invoices
        self._invoice_purchase_create('2015-01-01')
        self._invoice_purchase_create('2015-01-02')
        purchase = self._invoice_purchase_create('2015-01-03')
        self._invoice_refund(purchase, '2015-01-18')

        # Create model
        export_config = self.env.ref(
            'l10n_es_aeat_mod115.aeat_mod115_main_export_config')
        self.model115 = self.env['l10n.es.aeat.mod115.report'].create({
            'name': '9990000000115',
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
        _logger.debug('Calculate AEAT 115 1T 2015')
        self.model115.button_calculate()

        # Fill manual fields
        self.model115.write({
            # Resultados a ingresar anteriores
            'casilla_04': 145,
        })

        if self.debug:
            self._print_tax_lines(self.model115.tax_line_ids)

        # Check tax lines
        for box, result in self.taxes_result.iteritems():
            _logger.debug('Checking tax line: %s' % box)
            lines = self.model115.tax_line_ids.filtered(
                lambda x: x.field_number == int(box))
            self.assertEqual(
                round(sum(lines.mapped('amount')), 2),
                round(result, 2))

        # Check result
        _logger.debug('Checking results')
        retenciones = self.taxes_result.get('3', 0.)
        result = retenciones - 145
        self.assertEqual(self.model115.casilla_01, 1)
        self.assertEqual(
            round(self.model115.casilla_03, 2), round(retenciones, 2))
        self.assertEqual(
            round(self.model115.casilla_05, 2), round(result, 2))
