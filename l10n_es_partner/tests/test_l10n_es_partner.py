# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp.tests import common


class TestL10nEsPartner(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsPartner, self).setUp()
        self.country_spain = self.env.ref('base.es')
        self.bank = self.env['res.bank'].create({
            'name': 'BDE',
            'code': '1234',
            'lname': 'Banco de España',
            'vat': 'ES12345678Z',
            'website': 'www.bde.es',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Empresa de prueba',
            'comercial': 'Nombre comercial',
            'vat': 'ES12345678Z',
        })
        self.partner_bank = self.env['res.partner.bank'].create({
            'state': 'iban',
            'partner_id': self.partner.id,
            'acc_number': 'ES7620770024003102575766',
            'country_id': self.country_spain.id,
        })
        self.wizard = self.env['l10n.es.partner.import.wizard'].create({})
        self.wizard_toponyms = self.env['config.es.toponyms'].create({
            'name': '',
            'state': 'both',
            'city_info': 'no'
        })

    def test_search_commercial(self):
        res = self.env['res.partner'].name_search(self.partner.comercial)
        self.assertTrue(res)

    def test_onchange_banco(self):
        res = self.partner_bank.onchange_banco(
            self.partner_bank.acc_number, self.partner_bank.country_id.id,
            self.partner_bank.state)
        self.assertEqual(
            res['value']['acc_number'], 'ES76 2077 0024 0031 0257 5766')

    def test_onchange_banco_invalid(self):
        res = self.partner_bank.onchange_banco(
            'ES9920770024003102575766', self.partner_bank.country_id.id,
            self.partner_bank.state)
        self.assertTrue(res['warning']['message'])

    def test_onchange_vat(self):
        res = self.partner.vat_change('es05680675C')
        self.assertEqual(res['value']['vat'], 'ES05680675C')

    def test_import_banks(self):
        # First import the provinces
        self.wizard_toponyms.execute()
        # Then import banks
        self.wizard.import_local()
        bank = self.env['res.bank'].search([('code', '=', '0182')])
        self.assertTrue(bank)
        # Make sure the bank doesn't exist
        bank.unlink()
        # Import banks again but now from Internet
        self.wizard.execute()
        bank = self.env['res.bank'].search([('code', '=', '0182')])
        self.assertTrue(bank)
