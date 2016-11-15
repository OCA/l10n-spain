# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp.tests import common


class TestL10nEsPartner(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsPartner, cls).setUpClass()
        cls.country_spain = cls.env.ref('base.es')
        cls.bank = cls.env['res.bank'].create({
            'name': 'BDE',
            'code': '9999',
            'lname': 'Banco de España',
            'vat': '12345678Z',
            'website': 'www.bde.es',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Empresa de prueba',
            'comercial': 'Nombre comercial',
            'vat': 'ES12345678Z',
            'country_id': cls.country_spain.id,
        })
        cls.partner_bank = cls.env['res.partner.bank'].create({
            'partner_id': cls.partner.id,
            'acc_number': 'ES7620770024003102575766',
        })
        cls.wizard = cls.env['l10n.es.partner.import.wizard'].create({})
        cls.wizard_toponyms = cls.env['config.es.toponyms'].create({
            'name': '',
            'state': 'both',
            'city_info': 'no'
        })
        cls.env.user.company_id.country_id = cls.country_spain.id

    def test_search_commercial(self):
        res = self.env['res.partner'].name_search(self.partner.comercial)
        self.assertTrue(res)

    def test_onchange_acc_number_old(self):
        with self.env.do_in_onchange():
            record = self.env['res.partner.bank'].new()
            record.acc_number = '99999999509999999999'
            record.acc_country_id = self.country_spain.id
            record.onchange_acc_number_l10n_es_partner()
            self.assertEqual(record.acc_number, '9999 9999 50 9999999999')
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number_old_journal(self):
        with self.env.do_in_onchange():
            record = self.env['account.journal'].new()
            record.bank_acc_number = '99999999509999999999'
            record.bank_acc_country_id = self.country_spain.id
            record.onchange_bank_acc_number_l10n_es_partner()
            self.assertEqual(record.bank_acc_number, '9999 9999 50 9999999999')
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number(self):
        with self.env.do_in_onchange():
            record = self.env['res.partner.bank'].new()
            record.acc_number = 'ES1299999999509999999999'
            record.acc_country_id = self.country_spain.id
            record.onchange_acc_number_l10n_es_partner()
            self.assertEqual(
                record.acc_number, 'ES12 9999 9999 5099 9999 9999')
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number_journal(self):
        with self.env.do_in_onchange():
            record = self.env['account.journal'].new()
            record.bank_acc_number = 'ES1299999999509999999999'
            record.bank_acc_country_id = self.country_spain.id
            record.onchange_bank_acc_number_l10n_es_partner()
            self.assertEqual(
                record.bank_acc_number, 'ES12 9999 9999 5099 9999 9999')
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number_invalid(self):
        with self.env.do_in_onchange():
            record = self.env['res.partner.bank'].new()
            record.acc_number = 'ES9999999999999999999999'
            record.acc_country_id = self.country_spain.id
            res = record.onchange_acc_number_l10n_es_partner()
            self.assertTrue(res['warning']['message'])

    def test_onchange_acc_number_invalid_journal(self):
        with self.env.do_in_onchange():
            record = self.env['account.journal'].new()
            record.bank_acc_number = 'ES9999999999999999999999'
            record.bank_acc_country_id = self.country_spain.id
            res = record.onchange_bank_acc_number_l10n_es_partner()
            self.assertTrue(res['warning']['message'])

    def test_create_journal(self):
        journal = self.env['account.journal'].create({
            'type': 'bank',
            'bank_id': self.bank.id,
            'bank_acc_number': 'ES12 9999 9999 5099 9999 9999',
        })
        self.assertEqual(journal.name, 'BDE ES12 9999 9999 5099 9999 9999')

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

    def test_name(self):
        self.env['ir.config_parameter'].set_param(
            'l10n_es_partner.name_pattern', '%(comercial_name)s (%(name)s)')
        self.assertEqual(self.partner.display_name,
                         'Nombre comercial (Empresa de prueba)')
