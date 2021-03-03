# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase


class TestDeliverySeur(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Seur',
            'delivery_type': 'seur',
            'product_id': product_shipping_cost.id,
            'price_method': 'fixed',
            #
            # For tests, please fill next information
            #
            # 'seur_vat': '',
            # 'seur_franchise_code': 0,
            # 'seur_accounting_code': 0,
            # 'seur_integration_code': 0,
            # 'seur_cit_username': '',
            # 'seur_cit_password': '',
            # 'seur_ws_username': '',
            # 'seur_ws_password': '',
        })

    def test_soap_connection(self):
        if not self.carrier.seur_cit_username:
            self.skipTest('Without SEUR credentials')
        response = self.carrier.seur_test_connection()
        self.assertTrue(response)

    def test_delivery_carrier_seur_price(self):
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [(0, 0, {
                'applied_on': '1_product',
                'compute_price': 'fixed',
                'fixed_price': 100.00,
                'product_tmpl_id': product.id,
            })],
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'carrier_id': self.carrier.id,
            'pricelist_id': pricelist.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1})]
        })
        self.carrier.write({
            'price_method': 'fixed',
            'fixed_price': 99.99,
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 99.99)
        self.carrier.write({
            'price_method': 'fixed',
            'fixed_price': 5,
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 5)
        self.carrier.write({
            'price_method': 'base_on_rule',
            'fixed_price': 99.99,
            'price_rule_ids': [(0, 0, {
                'variable': 'quantity',
                'operator': '==',
                'max_value': 1,
                'list_base_price': 11.11})]
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 11.11)

    def test_delivery_carrier_seur_integration(self):
        if not self.carrier.seur_cit_username:
            self.skipTest('Without SEUR credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        partner.name = 'Partner test [ñáéíóú]'
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 10})]
        })
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEquals(len(sale.order_line), 2)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name)
        ])
        self.assertEquals(len(attachments), 1)
        self.assertTrue(picking.carrier_tracking_ref)
        self.assertFalse(picking.tracking_state_history)
        if not self.carrier.seur_ws_username:
            self.skipTest('Without SEUR WS credentials')
        picking.tracking_state_update()
        self.assertEquals(
            picking.tracking_state_history,
            'No existen expediciones para la búsqueda realizada')
        picking.cancel_shipment(picking)
