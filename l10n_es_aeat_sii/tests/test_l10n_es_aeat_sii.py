# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from openerp.tests import common
import exceptions
from datetime import datetime
import logging
import netsvc

_logger = logging.getLogger(__name__)


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


class test_l10n_es_aeat_sii(common.TransactionCase):
    def setUp(self):
        super(test_l10n_es_aeat_sii, self).setUp()
        cr, uid = self.cr, self.uid
        self.partner = self.registry('res.partner')
        self.registry('product.product')
        self.account_type = self.registry('account.account.type')
        self.account_expense = self.registry('account.account')
        self.analytic_account = self.registry('account.analytic.account')
        self.account_tax = self.registry('account.account')
        self.base_code = self.registry('account.tax.code')
        self.tax_code = self.registry('account.tax.code')
        self.tax = self.registry('account.tax')
        self.period = self.registry('account.period')
        self.account_invoice = self.registry('account.invoice')



        partner_id = self.partner.create(cr, uid, {
            'name': 'Test partner',
            'vat': 'ESF35999705'
        })

        # product_id = self.product.create(self.cr, self.uid, {
        #     'name': 'Test product',
        # })
        account_type_id = self.account_type.create(cr, uid, {
            'name': 'Test account type',
            'code': 'TEST',
        })
        account_expense_id = self.account_expense.create(cr, uid, {
            'name': 'Test expense account',
            'code': 'EXP',
            'type': 'other',
            'user_type': account_type_id,
        })
        analytic_account_id = self.analytic_account.create(cr, uid, {
            'name': 'Test analytic account',
            'type': 'normal',
        })
        account_tax_id = self.account_tax.create(cr, uid, {
            'name': 'Test tax account',
            'code': 'TAX',
            'type': 'other',
            'user_type': account_type_id,
        })
        base_code_id = self.base_code.create(cr, uid, {
            'name': '[28] Test base code',
            'code': 'OICBI',
        })
        tax_code_id = self.tax_code.create(cr, uid, {
            'name': '[29] Test tax code',
            'code': 'SOICC',
        })
        tax_id = self.tax.create(cr, uid, {
            'name': 'Test tax 10%',
            'type_tax_use': 'purchase',
            'type': 'percent',
            'amount': '0.10', 'account_collected_id': account_tax_id,
            'base_code_id': base_code_id,
            'base_sign': 1,
            'tax_code_id': tax_code_id,
            'tax_sign': 1,
        })
        period_id = self.registry('account.period').find(cr, uid)
        partner_obj = self.partner.browse(cr, uid, partner_id)


        self.invoice_obj = self.account_invoice.create(cr, uid, {
            'company_id': 1,
            'partner_id': partner_id,
            'date_invoice': datetime.now().date(),
            'type': 'out_invoice',
            'period_id': period_id[0],
            'account_id': partner_obj.property_account_payable.id,
            'invoice_line': [
                (0, 0, {
                    #TODO
                    'product_id': 73,
                    'account_id': account_expense_id,
                    'account_analytic_id': analytic_account_id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_id': [1],
                })]
        })



    def _open_invoice(self):

        self.invoice_obj.company_id.write({
            'sii_enabled': True,
            'use_connector': True,
            # 'chart_template_id': self.registry(
            #     'l10n_es.account_chart_template_pymes').id,
            'vat': 'ESU2687761C',
        })
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(self.uid, 'account.invoice', self.invoice_obj.id, 'button_confirm_advance', self.cr)

    def test_job_creation(self):
        self._open_invoice()
        #self.assertTrue(self.invoice_obj.invoice_jobs_ids)

        def _get_invoices_test(self, invoice_type, special_regime):
            str_today = self.invoice_obj._change_date_format(datetime.now().date())
            emisor = self.invoice_obj.company_id
            contraparte = self.partner
            expedida_recibida = 'FacturaExpedida'
            if self.invoiinvoice_objce.type in ['in_invoice', 'in_refund']:
                emisor = self.partner
                expedida_recibida = 'FacturaRecibida'
            res = {
                'IDFactura': {
                    'FechaExpedicionFacturaEmisor': str_today,
                    'IDEmisorFactura': {
                        'NIF': emisor.vat[2:]},
                    'NumSerieFacturaEmisor': (
                        self.invoice_obj.supplier_invoice_number or
                        self.invoice_obj.number)},
                expedida_recibida: {
                    'TipoFactura': invoice_type,
                    'Contraparte': {
                        'NombreRazon': contraparte.name,
                        'NIF': contraparte.vat[2:],
                    },
                    'DescripcionOperacion': u'/',
                    'ClaveRegimenEspecialOTrascendencia': special_regime,
                    'ImporteTotal': self.invoice_obj.amount_total,
                },
                'PeriodoImpositivo': {
                    'Periodo': str(self.invoice_obj.period_id.code[:2]),
                    'Ejercicio': int(self.invoice_obj.period_id.code[-4:])
                }
            }
            if self.invoice.type in ['out_invoice', 'out_refund']:
                res[expedida_recibida].update({
                    'TipoDesglose': {},
                })
            else:
                res[expedida_recibida].update({
                    "FechaRegContable":
                        self.invoice_obj._change_date_format(
                            self.invoice_obj.date_invoice
                        ),
                    "DesgloseFactura": {},
                    "CuotaDeducible": self.invoice_obj.amount_tax
                })
            if invoice_type == 'R4':
                invoices = self.invoice_obj.origin_invoices_ids
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
                self.invoice_obj._get_sii_invoice_dict(self.cr, self.uid, self.invoice_obj.id)
            self.partner.vat = vat

            invoices = self.invoice_obj._get_sii_invoice_dict(self.cr, self.uid, self.invoice_obj.id)
            test_out_inv = self._get_invoices_test('F1', '01')
            for key in invoices.keys():
                self.assertDictEqual(
                    _deep_sort(invoices.get(key)),
                    _deep_sort(test_out_inv.get(key)))

            self.invoice_obj.type = 'out_refund'
            self.invoice_obj.sii_refund_type = 'S'
            invoices = self.invoice._get_sii_invoice_dict(self.cr, self.uid, self.invoice_obj.id)
            test_out_refund = self._get_invoices_test('R4', '01')
            for key in invoices.keys():
                self.assertDictEqual(
                    _deep_sort(invoices.get(key)),
                    _deep_sort(test_out_refund.get(key)))

            self.invoice_obj.type = 'in_invoice'
            self.invoice_obj.supplier_invoice_number = 'sup0001'
            invoices = self.invoice_obj._get_sii_invoice_dict(self.cr, self.uid, self.invoice_obj.id)
            test_in_invoice = self._get_invoices_test('F1', '01')
            for key in invoices.keys():
                self.assertDictEqual(
                    _deep_sort(invoices.get(key)),
                    _deep_sort(test_in_invoice.get(key)))

            self.invoice_obj.type = 'in_refund'
            self.invoice_obj.sii_refund_type = 'S'
            self.invoice_obj.supplier_invoice_number = 'sup0001'
            invoices = self.invoice_obj._get_sii_invoice_dict(self.cr, self.uid, self.invoice_obj.id)
            test_in_refund = self._get_invoices_test('R4', '01')
            for key in invoices.keys():
                self.assertDictEqual(
                    _deep_sort(invoices.get(key)),
                    _deep_sort(test_in_refund.get(key)))

        def test_action_cancel(self):
            self._open_invoice()
            self.invoice_obj.invoice_jobs_ids.state = 'started'
            self.invoice_obj.journal_id.update_posted = True
            with self.assertRaises(exceptions.Warning):
                self.invoice_obj.action_cancel()