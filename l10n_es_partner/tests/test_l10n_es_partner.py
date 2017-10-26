# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo.tests import common


class TestL10nEsPartner(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsPartner, cls).setUpClass()
        # Make sure there's no commercial name on display_name field
        cls.env['ir.config_parameter'].set_param(
            'l10n_es_partner.name_pattern', '',
        )
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
        cls.env.user.company_id.country_id = cls.country_spain.id
        cls.bank_obj = cls.env['res.partner.bank'].with_context(
            default_partner_id=cls.partner.id
        )

    def test_search_commercial(self):
        partner_obj = self.env['res.partner']
        self.assertTrue(partner_obj.name_search('prueba'))
        self.assertTrue(partner_obj.name_search('comercial'))
        self.assertTrue(partner_obj.search([('name', 'ilike', 'comercial')]))

    def test_onchange_acc_number_old(self):
        with self.env.do_in_onchange():
            record = self.bank_obj.new()
            record.acc_number = '99999999509999999999'
            record._onchange_acc_number_l10n_es_partner()
            self.assertEqual(record.acc_number, '9999 9999 50 9999999999')
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number_old_incorrect_dc(self):
        with self.env.do_in_onchange():
            record = self.bank_obj.new()
            record.acc_number = '99999999999999999999'
            res = record._onchange_acc_number_l10n_es_partner()
            self.assertTrue(res.get('warning'))

    def test_onchange_acc_number_old_incorrect_size(self):
        with self.env.do_in_onchange():
            record = self.bank_obj.new()
            record.acc_number = '9999999950999999999'
            res = record._onchange_acc_number_l10n_es_partner()
            self.assertTrue(res.get('warning'))

    def test_onchange_acc_number_old_journal(self):
        with self.env.do_in_onchange():
            record = self.env['account.journal'].new()
            record.bank_acc_number = '99999999509999999999'
            record.bank_acc_country_id = self.country_spain.id
            record._onchange_bank_acc_number_l10n_es_partner()
            self.assertEqual(record.bank_acc_number, '9999 9999 50 9999999999')
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number(self):
        with self.env.do_in_onchange():
            record = self.bank_obj.new()
            record.acc_number = 'es1299999999509999999999'
            record._onchange_acc_number_l10n_es_partner()
            self.assertEqual(
                record.acc_number, 'ES12 9999 9999 5099 9999 9999')
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number_journal(self):
        with self.env.do_in_onchange():
            record = self.env['account.journal'].new()
            record.bank_acc_number = 'ES1299999999509999999999'
            record.bank_acc_country_id = self.country_spain.id
            record._onchange_bank_acc_number_l10n_es_partner()
            self.assertEqual(
                record.bank_acc_number, 'ES12 9999 9999 5099 9999 9999',
            )
            self.assertEqual(
                record.name, 'BDE ES12 9999 9999 5099 9999 9999',
            )
            self.assertEqual(record.bank_id, self.bank)

    def test_onchange_acc_number_invalid(self):
        with self.env.do_in_onchange():
            record = self.bank_obj.new()
            record.acc_number = 'ES9999999999999999999999'
            res = record._onchange_acc_number_l10n_es_partner()
            self.assertTrue(res['warning']['message'])

    def test_onchange_acc_number_invalid_journal(self):
        with self.env.do_in_onchange():
            record = self.env['account.journal'].new()
            record.bank_acc_number = 'ES9999999999999999999999'
            record.bank_acc_country_id = self.country_spain.id
            res = record._onchange_bank_acc_number_l10n_es_partner()
            self.assertTrue(res['warning']['message'])

    def test_import_banks(self):
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
            'l10n_es_partner.name_pattern', '%(comercial_name)s (%(name)s)',
        )
        partner2 = self.env['res.partner'].create({
            'name': 'Empresa de prueba',
            'comercial': 'Nombre comercial',
        })
        self.assertEqual(
            partner2.display_name, 'Nombre comercial (Empresa de prueba)',
        )
