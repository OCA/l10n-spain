# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2017 Tecnativa - Pedro M. Baeza
# Copyright 2018 PESOL - Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import exceptions, fields
from odoo.tests import common
from odoo.modules.module import get_resource_path

try:
    from zeep.client import ServiceProxy
except (ImportError, IOError) as err:
    ServiceProxy = object

CERTIFICATE_PATH = get_resource_path(
    'l10n_es_aeat_sii', 'tests', 'cert', 'entidadspj_act.p12',
)
CERTIFICATE_PASSWD = '794613'


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


class TestL10nEsAeatSiiBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatSiiBase, cls).setUpClass()
        cls.maxDiff = None
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
            # Needed for discriminatory tax amount in supplier invoices
            'description': 'P_IVA10_BC',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': '10',
            'account_id': cls.account_tax.id,
        })
        cls.env.user.company_id.sii_description_method = 'manual'
        cls.invoice = cls.env['account.invoice'].create({
            'partner_id': cls.partner.id,
            'date_invoice': '2018-02-01',
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
                })],
            'sii_manual_description': '/',
        })
        cls.invoice.company_id.write({
            'sii_enabled': True,
            'sii_test': True,
            'use_connector': True,
            'chart_template_id': cls.env.ref(
                'l10n_es.account_chart_template_pymes').id,
            'vat': 'ESU2687761C',
        })


class TestL10nEsAeatSii(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAeatSii, cls).setUpClass()
        cls.invoice.action_invoice_open()
        cls.invoice.number = 'INV001'
        cls.invoice.refund_invoice_id = cls.invoice.copy()
        cls.user = cls.env['res.users'].create({
            'name': 'Test user',
            'login': 'test_user',
            'groups_id': [
                (4, cls.env.ref('account.group_account_invoice').id)
            ],
            'email': 'somebody@somewhere.com',
        })
        with open(CERTIFICATE_PATH, 'rb') as certificate:
            content = certificate.read()
        cls.sii_cert = cls.env['l10n.es.aeat.sii'].create({
            'name': 'Test Certificate',
            'file': base64.b64encode(content),
            'company_id': cls.invoice.company_id.id,
        })
        cls.tax_agencies = cls.env['aeat.sii.tax.agency'].search([])

    def test_job_creation(self):
        self.assertTrue(self.invoice.invoice_jobs_ids)

    def _get_invoices_test(self, invoice_type, special_regime):
        expedida_recibida = 'FacturaExpedida'
        if self.invoice.type in ['in_invoice', 'in_refund']:
            expedida_recibida = 'FacturaRecibida'
        res = {
            'IDFactura': {
                'FechaExpedicionFacturaEmisor': '01-02-2018',
            },
            expedida_recibida: {
                'TipoFactura': invoice_type,
                'Contraparte': {
                    'NombreRazon': 'Test partner',
                    'NIF': 'F35999705',
                },
                'DescripcionOperacion': '/',
                'ClaveRegimenEspecialOTrascendencia': special_regime,
                'ImporteTotal': 110,
            },
            'PeriodoLiquidacion': {
                'Periodo': '02',
                'Ejercicio': 2018,
            }
        }
        if self.invoice.type in ['out_invoice', 'out_refund']:
            res['IDFactura'].update({
                'NumSerieFacturaEmisor': 'INV001',
                'IDEmisorFactura': {'NIF': 'U2687761C'},
            })
            res[expedida_recibida].update({
                'TipoDesglose': {},
                'ImporteTotal': 110.0,
            })
        else:
            res['IDFactura'].update({
                'NumSerieFacturaEmisor': 'sup0001',
                'IDEmisorFactura': {'NIF': 'F35999705'},
            })
            res[expedida_recibida].update({
                "FechaRegContable": self.invoice._change_date_format(
                    fields.Date.today()),
                "DesgloseFactura": {
                    'DesgloseIVA': {
                        'DetalleIVA': [
                            {
                                'BaseImponible': 100.0,
                                'CuotaSoportada': 10.0,
                                'TipoImpositivo': '10.0',
                            },
                        ],
                    },
                },
                "CuotaDeducible": 10,
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
        for key in list(invoices.keys()):
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_out_inv.get(key)),
            )
        self.invoice.type = 'out_refund'
        self.invoice.sii_refund_type = 'S'
        invoices = self.invoice._get_sii_invoice_dict()
        test_out_refund = self._get_invoices_test('R4', '01')
        for key in list(invoices.keys()):
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_out_refund.get(key)),
            )
        self.invoice.type = 'in_invoice'
        self.invoice.reference = 'sup0001'
        invoices = self.invoice._get_sii_invoice_dict()
        test_in_invoice = self._get_invoices_test('F1', '01')
        for key in list(invoices.keys()):
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_invoice.get(key)),
            )
        self.invoice.type = 'in_refund'
        self.invoice.sii_refund_type = 'S'
        self.invoice.reference = 'sup0001'
        self.invoice.compute_taxes()
        self.invoice.refund_invoice_id.type = 'in_invoice'
        invoices = self.invoice._get_sii_invoice_dict()
        test_in_refund = self._get_invoices_test('R4', '01')
        for key in list(invoices.keys()):
            self.assertDictEqual(
                _deep_sort(invoices.get(key)),
                _deep_sort(test_in_refund.get(key)),
            )

    def test_action_cancel(self):
        self.invoice.invoice_jobs_ids.state = 'started'
        self.invoice.journal_id.update_posted = True
        with self.assertRaises(exceptions.Warning):
            self.invoice.action_cancel()

    def test_sii_description(self):
        company = self.invoice.company_id
        company.write({
            'sii_header_customer': 'Test customer header',
            'sii_header_supplier': 'Test supplier header',
            'sii_description': ' | Test description',
            'sii_description_method': 'fixed',
        })
        invoice_temp = self.invoice.copy()
        self.assertEqual(
            invoice_temp.sii_description,
            'Test customer header | Test description',
        )
        invoice_temp = self.invoice.copy({'type': 'in_invoice'})
        self.assertEqual(
            invoice_temp.sii_description,
            'Test supplier header | Test description',
        )
        company.sii_description_method = 'manual'
        invoice_temp = self.invoice.copy()
        self.assertEqual(invoice_temp.sii_description, 'Test customer header')
        invoice_temp.sii_description = 'Other thing'
        self.assertEqual(invoice_temp.sii_description, 'Other thing')
        company.sii_description_method = 'auto'
        invoice_temp = self.invoice.copy()
        self.assertEqual(
            invoice_temp.sii_description, 'Test customer header | Test line',
        )

    def test_permissions(self):
        """This should work without errors"""
        self.invoice.sudo(self.user).action_invoice_open()

    def _activate_certificate(self, passwd=None):
        """Obtain Keys from .pfx and activate the cetificate"""
        if passwd:
            wizard = self.env['l10n.es.aeat.sii.password'].create({
                'password': passwd,
                'folder': 'test',
            })
            wizard.with_context(active_id=self.sii_cert.id).get_keys()
        self.sii_cert.action_activate()
        self.sii_cert.company_id.write({
            'name': 'ENTIDAD FICTICIO ACTIVO',
            'vat': 'ESJ7102572J',
        })

    def test_certificate(self):
        self.assertRaises(
            exceptions.ValidationError,
            self._activate_certificate,
            'Wrong passwd',
        )
        self._activate_certificate(CERTIFICATE_PASSWD)
        self.assertEqual(self.sii_cert.state, 'active')
        proxy = self.invoice._connect_sii(self.invoice.type)
        self.assertIsInstance(proxy, ServiceProxy)

    def _test_binding_address(self, invoice):
        company = invoice.company_id
        tax_agency = company.sii_tax_agency_id
        self.sii_cert.company_id.sii_tax_agency_id = tax_agency
        proxy = invoice._connect_sii(invoice.type)
        address = proxy._binding_options['address']
        self.assertTrue(address)
        if company.sii_test and tax_agency:
            params = tax_agency._connect_params_sii(invoice.type)
            if params['address']:
                self.assertEqual(address, params['address'])

    def _test_tax_agencies(self, invoice):
        for tax_agency in self.tax_agencies:
            invoice.company_id.sii_tax_agency_id = tax_agency
            self._test_binding_address(invoice)
        else:
            invoice.company_id.sii_tax_agency_id = False
            self._test_binding_address(invoice)

    def test_tax_agencies_sandbox(self):
        self._activate_certificate(CERTIFICATE_PASSWD)
        self.invoice.company_id.sii_test = True
        for inv_type in ['out_invoice', 'in_invoice']:
            self.invoice.type = inv_type
            self._test_tax_agencies(self.invoice)

    def test_tax_agencies_production(self):
        self._activate_certificate(CERTIFICATE_PASSWD)
        self.invoice.company_id.sii_test = False
        for inv_type in ['out_invoice', 'in_invoice']:
            self.invoice.type = inv_type
            self._test_tax_agencies(self.invoice)
