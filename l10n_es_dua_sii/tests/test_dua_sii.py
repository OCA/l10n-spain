# Copyright 2019 Tecnativa - Alexandre Díaz
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestL10nEsDuaSii(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_es = cls.env.ref('base.es')
        cls.fp_dua = cls.env['account.fiscal.position'].create(dict(
            name="Importación con DUA",
            auto_apply=True,
            country_id=cls.country_es.id,
            company_id=cls.env.user.company_id.id,
            vat_required=True,
            sequence=50))
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test partner',
            'vat': 'ESF35999705',
            'company_type': 'company',
            'property_account_position_id': cls.fp_dua.id,
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
        cls.company = cls.env.user.company_id
        xml_id = '%s_account_tax_template_p_iva21_ibc' % cls.company.id
        cls.tax = cls.env.ref('l10n_es.' + xml_id, raise_if_not_found=False)
        if not cls.tax:
            cls.tax = cls.env['account.tax'].create({
                'name': 'IVA 21% Importaciones bienes corrientes',
                'type_tax_use': 'purchase',
                'amount_type': 'percent',
                'amount': '0',
                'account_id': cls.account_tax.id,
            })
            cls.env['ir.model.data'].create({
                'module': 'l10n_es',
                'name': xml_id,
                'model': cls.tax._name,
                'res_id': cls.tax.id,
            })

    def test_dua_sii(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'date_invoice': '2019-02-01',
            'date': '2019-02-01',
            'type': 'in_invoice',
            'account_id': self.partner.property_account_payable_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                    'invoice_line_tax_ids': [(6, 0, self.tax.ids)],
                })],
            'sii_manual_description': '/',
        })
        self.assertTrue(invoice.sii_dua_invoice)
        invoice.company_id.write({
            'sii_enabled': True,
            'vat': 'ESU2687761C',
        })
        values = invoice._get_sii_invoice_dict_in()
        self.assertEqual(values['FacturaRecibida']['TipoFactura'], 'F5')
        self.assertEqual(values['FacturaRecibida']['IDEmisorFactura']['NIF'],
                         'U2687761C')
        self.assertEqual(values['FacturaRecibida']['Contraparte']['NIF'],
                         'U2687761C')
        self.assertEqual(
            values['FacturaRecibida']['Contraparte']['NombreRazon'],
            invoice.company_id.name)

    def test_not_dua_sii(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'date_invoice': '2019-02-01',
            'date': '2019-02-01',
            'type': 'in_invoice',
            'account_id': self.partner.property_account_payable_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'account_id': self.account_expense.id,
                    'account_analytic_id': self.analytic_account.id,
                    'name': 'Test line',
                    'price_unit': 100,
                    'quantity': 1,
                })],
            'sii_manual_description': '/',
        })
        self.assertFalse(invoice.sii_dua_invoice)
        values = invoice._get_sii_invoice_dict_in()
        self.assertNotEqual(values['FacturaRecibida']['TipoFactura'], 'F5')
