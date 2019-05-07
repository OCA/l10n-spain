# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase
from odoo import exceptions

_logger = logging.getLogger('aeat.130')


class TestL10nEsAeatMod130Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        'S_IVA21B': (1000, 0),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        'P_IVA21_BC': (900, 0),
    }

    def test_model_130(self):
        self._invoice_sale_create('2019-01-01')
        self._invoice_purchase_create('2019-01-01')
        # Create model
        export_config = self.env.ref(
            'l10n_es_aeat_mod130.aeat_mod130_sub01_export_config')
        model130 = self.env['l10n.es.aeat.mod130.report'].create({
            'name': '9990000000130',
            'period': '1T',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2019,
            'period_type': '1T',
            'date_start': '2019-01-01',
            'date_end': '2019-03-31',
            'export_config_id': export_config.id,
            'journal_id': self.journal_misc.id,
            'counterpart_account_id': self.accounts['475000'].id
        })
        # Calculate
        _logger.debug('Calculate AEAT 130 1T 2015')
        model130.button_calculate()
        self.assertAlmostEqual(model130.casilla_01, 1000, 2)
        self.assertAlmostEqual(model130.casilla_02, 900, 2)
        self.assertAlmostEqual(model130.casilla_03, 100, 2)
        self.assertAlmostEqual(model130.casilla_04, 20, 2)
        self.assertAlmostEqual(model130.casilla_05, 0, 2)
        self.assertAlmostEqual(model130.casilla_06, 0, 2)
        self.assertAlmostEqual(model130.casilla_07, 20, 2)
        self.assertAlmostEqual(model130.casilla_12, 20, 2)
        self.assertAlmostEqual(model130.casilla_13, 0, 2)
        self.assertAlmostEqual(model130.casilla_14, 20, 2)
        self.assertAlmostEqual(model130.casilla_15, 0, 2)
        # Has no loan
        self.assertAlmostEqual(model130.casilla_16, 0, 2)
        self.assertAlmostEqual(model130.casilla_17, 20, 2)
        self.assertAlmostEqual(model130.casilla_18, 0, 2)
        # Test second trimester
        model130_2t = model130.copy({
            'name': '9990000001130',
            'period_type': '2T',
            'date_start': '2019-04-01',
            'date_end': '2019-06-30',
        })
        self.taxes_sale['S_IVA21B'] = (300, )
        self._invoice_sale_create('2019-04-01')
        model130_2t.button_calculate()
        self.assertAlmostEqual(model130_2t.casilla_01, 1300, 2)
        self.assertAlmostEqual(model130_2t.casilla_02, 900, 2)
        self.assertAlmostEqual(model130_2t.casilla_03, 400, 2)
        self.assertAlmostEqual(model130_2t.casilla_04, 80, 2)
        self.assertAlmostEqual(model130_2t.casilla_05, 20, 2)
        self.assertAlmostEqual(model130_2t.casilla_06, 0, 2)
        self.assertAlmostEqual(model130_2t.casilla_07, 60, 2)
        self.assertAlmostEqual(model130_2t.casilla_12, 60, 2)
        self.assertAlmostEqual(model130_2t.casilla_13, 0, 2)
        self.assertAlmostEqual(model130_2t.casilla_14, 60, 2)
        self.assertAlmostEqual(model130_2t.casilla_15, 0, 2)
        # Has no loan
        self.assertAlmostEqual(model130_2t.casilla_16, 0, 2)
        self.assertAlmostEqual(model130_2t.casilla_17, 60, 2)
        self.assertAlmostEqual(model130_2t.casilla_18, 0, 2)
        # Test has loan
        model130_has_loan = model130.copy({
            'name': '9990000002130',
            'has_prestamo': True,
            'activity_type': 'other',
        })
        model130_has_loan.button_calculate()
        self.assertAlmostEqual(model130_has_loan.casilla_16, 2, 2)
        # Test has loan activity is primary
        model130_has_loan = model130.copy({
            'name': '9990000003130',
            'has_prestamo': True,
            'activity_type': 'primary',
        })
        with self.assertRaises(exceptions.Warning):
            model130_has_loan.button_calculate()
