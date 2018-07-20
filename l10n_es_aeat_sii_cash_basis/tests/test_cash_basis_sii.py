# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_es_aeat_sii.tests.test_l10n_es_aeat_sii import \
    TestL10nEsAeatSiiBase


SII_PAYMENT_DICTS = {
    'out_invoice_payment': {
        "IDFactura": {
            "IDEmisorFactura": {
                "NIF": u'F35999705',
                "NombreRazon": u"Test partner",
            },
            "NumSerieFacturaEmisor": u'FACE001',
            "FechaExpedicionFacturaEmisor": '01-02-2018',
        },
        "Pagos": {
            "Pago": [{
                'Fecha': '20-02-2018',
                'Importe': 110.0,
                'Medio': u'01',
            }],
        },

    },
}


class TestCashBasisSii(TestL10nEsAeatSiiBase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestCashBasisSii, cls).setUpClass()
        cls.invoice.write({
            'type': 'in_invoice',
            'reference': 'FACE001',
        })
        cls.account_tax_cash_basis = cls.env['account.account'].create({
            'name': 'Test tax cash basis account',
            'code': 'TAX_CB',
            'user_type_id': cls.account_type.id,
        })
        cls.tax.write({
            'use_cash_basis': True,
            'cash_basis_account': cls.account_tax_cash_basis.id,
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test payment journal',
            'code': 'BNK_TEST',
            'type': 'bank',
        })
        cls.env.user.company_id.tax_cash_basis_journal_id = cls.journal.id
        cls.payment_method = cls.env.ref(
            'account.account_payment_method_manual_in'
        )
        cls.payment_method.sii_payment_mode_id = cls.env.ref(
            'l10n_es_aeat_sii_cash_basis.aeat_sii_payment_mode_key_01'
        ).id
        cls.invoice.action_invoice_open()

    def test_cash_basis_one_invoice(self):
        payment = self.env['account.payment'].with_context(
            default_invoice_ids=self.invoice.ids,
            test_sii_cash_basis=True,
        ).create({
            'journal_id': self.journal.id,
            'payment_date': '2018-02-20',
            'payment_method_id': self.payment_method.id,
        })
        payment.post()
        job = self.invoice.invoice_jobs_ids.filtered(lambda x: (
            x.job_function_id.name ==
            '<account.invoice>.send_cash_basis_payment'
        ))
        self.assertTrue(job)
        payment = self.invoice._get_ssi_payment_dict(job.args[0])
        self.assertDictEqual(payment, SII_PAYMENT_DICTS['out_invoice_payment'])
