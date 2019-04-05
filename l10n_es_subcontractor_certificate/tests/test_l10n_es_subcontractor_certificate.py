# Copyright 2019 Studio73 - Pablo Fuentes <pablo@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields
from odoo.tests import common
from .. models.subcontractor_certificate import EXPIRED_WARNING_AEAT
from .. models.subcontractor_certificate import REQUIRED_WARNING_AEAT
from .. models.subcontractor_certificate import EXPIRED_WARNING_SS
from .. models.subcontractor_certificate import REQUIRED_WARNING_SS


class TestL10nEsSubcontractorCertificate(common.TransactionCase):

    def setUp(self):
        super(TestL10nEsSubcontractorCertificate, self).setUp()
        self.ctx_no_mail = {
            'no_reset_password': True,
            'mail_create_nosubscribe': True,
            'mail_create_nolog': True
        }
        Partner = self.env['res.partner'].with_context(self.ctx_no_mail)
        Purchase = self.env['purchase.order'].with_context(self.ctx_no_mail)
        Invoice = self.env['account.invoice'].with_context(self.ctx_no_mail)
        self.partner = Partner.create({
            'name': 'Demo Supplier',
            'email': 'demo@supplier.com',
            'supplier': True,
        })
        self.purchase = Purchase.create({'partner_id': self.partner.id})
        self.invoice = Invoice.create({
            'partner_id': self.partner.id,
            'type': 'in_invoice'
        })
        self.expired_date = fields.Date.today() - timedelta(days=1)

    def test_00_onchange_partner_id(self):
        self.partner.write({
            'certificate_required': True,
        })
        res_purchase = self.purchase.onchange_partner_id()
        self.assertEqual(
            res_purchase.get('warning', False),
            REQUIRED_WARNING_AEAT,
            'Purchase should show warning required AEAT'
            'certificate expiration date')
        res_invoice = self.invoice._onchange_partner_id()
        self.assertEqual(
            res_invoice.get('warning', False),
            REQUIRED_WARNING_AEAT,
            'Invoice should show warning required AEAT'
            'certificate expiration date')

    def test_01_onchange_partner_id(self):
        self.partner.write({
            'certificate_required': True,
            'certificate_expiration_aeat': fields.Date.today(),
        })
        res_purchase = self.purchase.onchange_partner_id()
        self.assertEqual(
            res_purchase.get('warning'),
            REQUIRED_WARNING_SS,
            'Purchase should show warning required SS '
            'certificate expiration date')
        res_invoice = self.invoice._onchange_partner_id()
        self.assertEqual(
            res_invoice.get('warning'),
            REQUIRED_WARNING_SS,
            'Invoice should show warning required SS '
            'certificate expiration date')

    def test_02_onchange_partner_id(self):
        self.partner.write({
            'certificate_required': True,
            'certificate_expiration_aeat': self.expired_date,
            'certificate_expiration_ss': fields.Date.today(),
        })
        res_purchase = self.purchase.onchange_partner_id()

        self.assertEqual(
            res_purchase.get('warning'),
            EXPIRED_WARNING_AEAT,
            'Purchase should show warning expired AEAT certificate')
        res_invoice = self.invoice._onchange_partner_id()
        self.assertEqual(
            res_invoice.get('warning'),
            EXPIRED_WARNING_AEAT,
            'Invoice should show warning expired AEAT certificate')

    def test_03_onchange_partner_id(self):
        self.partner.write({
            'certificate_required': True,
            'certificate_expiration_aeat': fields.Date.today(),
            'certificate_expiration_ss': self.expired_date,
        })
        res_purchase = self.purchase.onchange_partner_id()
        self.assertEqual(
            res_purchase.get('warning'),
            EXPIRED_WARNING_SS,
            'Purchase should show warning expired SS certificate')
        res_invoice = self.invoice._onchange_partner_id()
        self.assertEqual(
            res_invoice.get('warning'),
            EXPIRED_WARNING_SS,
            'Invoice should show warning expired SS certificate')
