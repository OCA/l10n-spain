# © 2018 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase
from odoo.tools import file_open
import base64


configurations = {
    'facturae_01.xsig': {
        'country': 'ESP', 'vat': 'ESR3028604A', 'product_code': 'RX'},
    'facturae_02.xsig': {
        'country': 'BEL', 'vat': 'BE0477472701', 'product_code': 'RX'},
    'facturae_03.xsig': {
        'country': 'DEU', 'vat': 'DE123456788', 'product_code': 'RX'},
    'facturae_04.xsig': {
        'country': 'DEU', 'vat': 'DE111111125', 'product_code': 'RX'},
}


class TestImportFacturae(TransactionCase):
    def setUp(self):
        super().setUp()
        self.config = self.env['account.invoice.import.config'].create({
            'name': 'Facturae',
            'invoice_line_method': 'nline_auto_product',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 21.,
            'description': 'TEST TAX',
        })
        self.product = self.env['product.product'].create({
            'name': 'Product',
            'supplier_taxes_id': [(4, self.tax.id)],
        })

    def check_config(self, config, vals):
        country = self.env['res.country'].search([
            ('code', '=', vals['country'])])
        country.ensure_one()
        partner = self.env['res.partner'].create({
            'name': 'Partner',
            'invoice_import_ids': [(4, self.config.id)],
            'country_id': country.id,
            'vat': vals['vat'],
            'supplier': True,
        })
        self.env['product.supplierinfo'].create({
            'name': partner.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'product_code': vals['product_code'],
        })
        filename = config
        f = file_open(
            'account_invoice_import_facturae/tests/files/' + filename, 'rb')
        xml_file = f.read()
        wiz = self.env['account.invoice.import'].create({
            'invoice_file': base64.b64encode(xml_file),
            'invoice_filename': filename,
        })
        f.close()
        action = wiz.import_invoice()
        invoice = self.env['account.invoice'].browse(action['res_id'])
        self.assertTrue(invoice)
        self.assertEqual(invoice.partner_id, partner)

    def test_import(self):
        for config in configurations:
            self.check_config(config, configurations[config])
