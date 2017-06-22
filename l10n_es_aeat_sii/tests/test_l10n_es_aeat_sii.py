# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests import common
from odoo import exceptions


def _deep_sort(obj):
    """
    Recursively sort list or dict nested lists
    """
    if isinstance(obj, dict):
        _sorted = {}
        for key in sorted(obj):
            _sorted[key] = _deep_sort(obj[key])
    elif isinstance(obj, list):
        new_list = []
        for val in obj:
            new_list.append(_deep_sort(val))
        _sorted = sorted(new_list)
    else:
        _sorted = obj
    return _sorted


class TestL10nEsAeatSii(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatSii, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test partner',
            'vat': 'ESF35999705'
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test product',
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test account type',
        })
        cls.account_expense = cls.env['account.account'].create({
            'name': 'Test expense account',
            'code': 'EXP',
            'user_type_id': cls.account_type.id,
        })
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Test analytic account',
        })
        cls.account_tax = cls.env['account.account'].create({
            'name': 'Test tax account',
            'code': 'TAX',
            'user_type_id': cls.account_type.id,
        })
        cls.tax = cls.env['account.tax'].create({
            'name': 'Test tax 10%',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': '10',
            'account_id': cls.account_tax.id,
        })
        cls.invoice = cls.env['account.invoice'].create({
            'partner_id': cls.partner.id,
            'date_invoice': '2017-06-19',
            'type': 'out_invoice',
            'account_id': cls.partner.property_account_payable_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'account_id': cls.account_expense.id,
                    'account_analytic_id': cls.analytic_account.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_ids': [(6, 0, cls.tax.ids)],
                })]
        })
        cls.invoice.company_id.write({
            'sii_enabled': True,
            'use_connector': True,
            'chart_template_id': cls.env.ref(
                'l10n_es.account_chart_template_pymes').id,
            'vat': 'ESU2687761C',
        })
        cls.invoice.signal_workflow('invoice_open')
        cls.invoice.number = 'INV001'
        cls.invoice.origin_invoice_ids = cls.invoice.copy()

    def _open_invoice(self):
        self.invoice.signal_workflow('invoice_open')

    def test_job_creation(self):
        self.assertTrue(self.invoice.invoice_jobs_ids)

    def _get_invoices_test(self, invoice_type, special_regime):
        expedida_recibida = 'FacturaExpedida'
        if self.invoice.type in ['in_invoice', 'in_refund']:
            expedida_recibida = 'FacturaRecibida'
        res = {
            'IDFactura': {
                'FechaExpedicionFacturaEmisor': '19-06-2017',
            },
            expedida_recibida: {
                'TipoFactura': invoice_type,
                'Contraparte': {
                    'NombreRazon': u'Test partner',
                    'NIF': u'F35999705',
                },
                'DescripcionOperacion': u'/',
                'ClaveRegimenEspecialOTrascendencia': special_regime,
                'ImporteTotal': self.invoice.amount_total,
            },
            'PeriodoImpositivo': {
                'Periodo': '06',
                'Ejercicio': 2017,
            }
        }
        if self.invoice.type in ['out_invoice', 'out_refund']:
            res['IDFactura'].update({
                'NumSerieFacturaEmisor': u'INV001',
                'IDEmisorFactura': {'NIF': u'U2687761C'},
            })
            res[expedida_recibida].update({
                'TipoDesglose': {},
                'ImporteTotal': 110.0,
            })
        else:
            res['IDFactura'].update({
                'NumSerieFacturaEmisor': u'sup0001',
                'IDEmisorFactura': {'NIF': u'F35999705'},
            })
            res[expedida_recibida].update({
                "FechaRegContable": '19-06-2017',
                "DesgloseFactura": {},
                "CuotaDeducible": 10.0,
            })
        if invoice_type == 'R4':
            res[expedida_recibida].update({
                'TipoRectificativa': 'S',
                'ImporteRectificacion': {
                    'BaseRectificada': 100.0,
                    'CuotaRectificada': 10.0,
                }
            })
        return res

    def test_get_invoice_data(self):
        vat = self.partner.vat
        self.partner.vat = False
        with self.assertRaises(exceptions.Warning):
            self.invoice._get_sii_invoice_dict()
        self.partner.vat = vat
        invoices = self.invoice._get_sii_invoice_dict()
        test_out_inv = self._get_invoices_test('F1', '01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_out_inv.get(key)),
            )
        self.invoice.type = 'out_refund'
        self.invoice.refund_type = 'S'
        invoices = self.invoice._get_sii_invoice_dict()
        test_out_refund = self._get_invoices_test('R4', '01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_out_refund.get(key)),
            )
        self.invoice.type = 'in_invoice'
        self.invoice.reference = 'sup0001'
        invoices = self.invoice._get_sii_invoice_dict()
        test_in_invoice = self._get_invoices_test('F1', '01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_invoice.get(key)),
            )
        self.invoice.type = 'in_refund'
        self.invoice.refund_type = 'S'
        self.invoice.reference = 'sup0001'
        invoices = self.invoice._get_sii_invoice_dict()
        test_in_refund = self._get_invoices_test('R4', '01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_refund.get(key)),
            )

    def test_action_cancel(self):
        self.invoice.invoice_jobs_ids.state = 'started'
        self.invoice.journal_id.update_posted = True
        with self.assertRaises(exceptions.Warning):
            self.invoice.action_cancel()
