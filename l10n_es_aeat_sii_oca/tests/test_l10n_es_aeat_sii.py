# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp.tests import common
from openerp import exceptions, fields


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


class TestL10nEsAeatSii(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsAeatSii, self).setUp()
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
        self.account_expense = self.env['account.account'].create({
            'name': 'Test expense account',
            'code': 'EXP',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Test analytic account',
            'type': 'normal',
        })
        self.account_tax = self.env['account.account'].create({
            'name': 'Test tax account',
            'code': 'TAX',
            'type': 'other',
            'user_type': self.account_type.id,
        })
        self.base_code = self.env['account.tax.code'].create({
            'name': '[28] Test base code',
            'code': 'OICBI',
        })
        self.tax_code = self.env['account.tax.code'].create({
            'name': '[29] Test tax code',
            'code': 'SOICC',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax 10%',
            'type_tax_use': 'purchase',
            'type': 'percent',
            'amount': '0.10',
            'account_collected_id': self.account_tax.id,
            'base_code_id': self.base_code.id,
            'base_sign': 1,
            'tax_code_id': self.tax_code.id,
            'tax_sign': 1,
        })
        self.period = self.env['account.period'].find()
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'date_invoice': fields.Date.today(),
            'type': 'out_invoice',
            'period_id': self.period.id,
            'account_id': self.partner.property_account_payable.id,
            'invoice_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_id': [(6, 0, self.tax.ids)],
                })]
        })

    def _open_invoice(self):
        self.invoice.company_id.write({
            'sii_enabled': True,
            'use_connector': True,
            'chart_template_id': self.env.ref(
                'l10n_es.account_chart_template_pymes').id,
            'vat': 'ESU2687761C',
        })
        self.invoice.signal_workflow('invoice_open')

    def test_job_creation(self):
        self._open_invoice()
        self.assertTrue(self.invoice.invoice_jobs_ids)

    def _get_invoices_test(self, invoice_type, special_regime):
        str_today = self.invoice._change_date_format(fields.Date.today())
        emisor = self.invoice.company_id
        contraparte = self.partner
        expedida_recibida = 'FacturaExpedida'
        if self.invoice.type in ['in_invoice', 'in_refund']:
            emisor = self.partner
            expedida_recibida = 'FacturaRecibida'
        res = {
            'IDFactura': {
                'FechaExpedicionFacturaEmisor': str_today,
                'IDEmisorFactura': {
                    'NIF': emisor.vat[2:]},
                'NumSerieFacturaEmisor': (
                    self.invoice.supplier_invoice_number or
                    self.invoice.number)},
            expedida_recibida: {
                'TipoFactura': invoice_type,
                'Contraparte': {
                    'NombreRazon': contraparte.name,
                    'NIF': contraparte.vat[2:],
                },
                'DescripcionOperacion': u'/',
                'ClaveRegimenEspecialOTrascendencia': special_regime,
                'ImporteTotal': self.invoice.amount_total,
            },
            'PeriodoImpositivo': {
                'Periodo': str(self.invoice.period_id.code[:2]),
                'Ejercicio': int(self.invoice.period_id.code[-4:])
            }
        }
        if self.invoice.type in ['out_invoice', 'out_refund']:
            res[expedida_recibida].update({
                'TipoDesglose': {},
            })
        else:
            res[expedida_recibida].update({
                "FechaRegContable":
                    self.invoice._change_date_format(
                        self.invoice.date_invoice
                    ),
                "DesgloseFactura": {},
                "CuotaDeducible": self.invoice.amount_tax
            })
        if invoice_type == 'R4':
            invoices = self.invoice.origin_invoices_ids
            base_rectificada = sum(invoices.mapped('amount_untaxed'))
            cuota_rectificada = sum(invoices.mapped('amount_tax'))
            res[expedida_recibida].update({
                'TipoRectificativa': 'S',
                'ImporteRectificacion': {
                    'BaseRectificada': base_rectificada,
                    'CuotaRectificada': cuota_rectificada,
                }
            })
        return res

    def test_get_invoice_data(self):
        self._open_invoice()

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
                _deep_sort(test_out_inv.get(key)))

        self.invoice.type = 'out_refund'
        self.invoice.sii_refund_type = 'S'
        invoices = self.invoice._get_sii_invoice_dict()
        test_out_refund = self._get_invoices_test('R4', '01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_out_refund.get(key)))

        self.invoice.type = 'in_invoice'
        self.invoice.supplier_invoice_number = 'sup0001'
        invoices = self.invoice._get_sii_invoice_dict()
        test_in_invoice = self._get_invoices_test('F1', '01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_invoice.get(key)))

        self.invoice.type = 'in_refund'
        self.invoice.sii_refund_type = 'S'
        self.invoice.supplier_invoice_number = 'sup0001'
        invoices = self.invoice._get_sii_invoice_dict()
        test_in_refund = self._get_invoices_test('R4', '01')
        for key in invoices.keys():
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_refund.get(key)))

    def test_action_cancel(self):
        self._open_invoice()
        self.invoice.invoice_jobs_ids.state = 'started'
        self.invoice.journal_id.update_posted = True
        with self.assertRaises(exceptions.Warning):
            self.invoice.action_cancel()
