# Copyright 2025 Juan Carlos Oñate - Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import date

import xlrd
from freezegun import freeze_time

from odoo import Command, fields
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon


@freeze_time("2025-09-02")
@tagged("post_install", "-at_install")
class TestDigitalCanonReport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = date.today()
        cls.product_brand = cls.env["product.brand"].create(
            {
                "name": "Brand X",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Mobile X",
                "type": "consu",
                "is_storable": True,
                "tracking": "serial",
                "l10n_es_digital_canon": "3_25.phone_64",
                "product_brand_id": cls.product_brand.id,
            }
        )
        cls.customer_es = cls.env["res.partner"].create(
            {
                "name": "Test Customer ES",
                "country_id": cls.env.ref("base.es").id,
                "vat": "ESB87530432",
            }
        )
        cls.customer_us = cls.env["res.partner"].create(
            {
                "name": "Test Customer US",
                "country_id": cls.env.ref("base.us").id,
                "vat": "US987654321",
            }
        )
        cls.excepted_customer_es = cls.env["res.partner"].create(
            {
                "name": "Test Excepted Customer ES",
                "country_id": cls.env.ref("base.es").id,
                "vat": "ESB87530432",
                "is_digital_canon_exempt": True,
                "digital_canon_exempt_type": "administracion",
            }
        )
        cls.vendor_es = cls.env["res.partner"].create(
            {
                "name": "Test Vendor ES",
                "country_id": cls.env.ref("base.es").id,
                "vat": "ESB87530432",
            }
        )
        cls.vendor_us = cls.env["res.partner"].create(
            {
                "name": "Test Vendor US",
                "country_id": cls.env.ref("base.us").id,
                "vat": "US987654321",
            }
        )
        cls.wizard = cls.env["digital.canon.report.wizard"].create(
            {
                "date_start": today.replace(day=1),
                "date_end": today,
            }
        )
        ctx = {
            "report_name": "l10n_es_digital_canon_report.digital_canon_report",
            "active_model": "digital.canon.report.wizard",
            "active_ids": [cls.wizard.id],
        }
        cls.report = cls.env["ir.actions.report"].with_context(**ctx)
        cls.lot_mobile_1 = cls.env["stock.lot"].create(
            {
                "name": "LOT-MOBILEX-001",
                "product_id": cls.product.id,
            }
        )
        cls.lot_mobile_2 = cls.env["stock.lot"].create(
            {
                "name": "LOT-MOBILE2-001",
                "product_id": cls.product.id,
            }
        )
        cls.create_purchase_with_invoice(cls.vendor_es, cls.product, cls.lot_mobile_1)

    @classmethod
    def create_purchase_with_invoice(self, vendor, product, lot, qty=1):
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": vendor.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "name": product.name,
                            "product_qty": qty,
                        },
                    )
                ],
            }
        )
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.quantity = qty
        picking.move_line_ids.lot_id = lot
        picking.button_validate()
        purchase.action_create_invoice()
        bill = purchase.invoice_ids
        bill.invoice_date = fields.Date.today()
        bill.action_post()

    def _render_report_xlsx(self, wizard, report, row_n=4):
        data = {
            "date_start": wizard.date_start.isoformat(),
            "date_end": wizard.date_end.isoformat(),
        }
        report_xls = report._render_xlsx(None, wizard, data)
        wb = xlrd.open_workbook(file_contents=report_xls[0])
        ws = wb.sheet_by_index(0)
        data_row = ws.row_values(row_n)
        return data_row

    def create_sale_with_invoice(self, customer):
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": customer.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        self.sale_order.action_confirm()
        self.sale_order.picking_ids.action_assign()
        self.sale_order.picking_ids.move_line_ids.quantity = 1
        self.sale_order.picking_ids.move_line_ids.lot_id = self.lot_mobile_1
        self.sale_order.picking_ids.button_validate()
        self.sale_order._create_invoices()
        self.sale_order.invoice_ids.invoice_date = fields.Date.today()
        self.sale_order.invoice_ids.action_post()

    def test_xlsx_contains_expected_headers(self):
        headers = self._render_report_xlsx(self.wizard, self.report, row_n=3)
        expected_headers = [
            "Tipo de Operación",
            "Seleccionar un equipo/aparato/soporte",
            "Marca Comercializada",
            "Unidades vendidas en la operación",
            "Operación Exceptuada",
            "Tipo de Exceptuación",
            "País de Destino",
            "Con compensación",
            "Razón Social Proveedor",
            "NIF Proveedor",
            "Nº Factura de Compra",
            "Importe Total Fra. Compra",
            "Fecha Fra. Compra",
            "ID Fra. Compra",
            "Razón Social Beneficiario",
            "NIF Beneficiario",
            "Número Fra. Venta",
            "Fecha Fra. Venta",
            "Importe Total Fra. Venta",
            "Id Fra. Venta",
            "Nombre y Apellidos receptor/Razón Social",
            "Email",
            "Dirección entrega",
            "Dirección Facturación",
        ]
        self.assertEqual(headers, expected_headers)
        block_headers = self._render_report_xlsx(self.wizard, self.report, row_n=2)
        self.assertIn("Datos de la compra", block_headers)
        self.assertIn(
            "Venta a Cliente Exceptuado > o igual a 10 Unidades", block_headers
        )
        self.assertIn("Venta a Cliente Exceptuado < a 10 Unidades", block_headers)

    def test_report_xlsx_normal_sale_with_canon(self):
        """Case of a normal sale: product purchased and sold in Spain
        without any exemption.
        """
        self.create_sale_with_invoice(self.customer_es)
        data_row = self._render_report_xlsx(self.wizard, self.report, row_n=4)
        self.assertEqual(data_row[0], "Mayorista/Minorista")
        self.assertEqual(data_row[1], "Teléfono inteligente hasta 64 Gb - 3,25")
        self.assertEqual(data_row[2], "Brand X")
        self.assertEqual(data_row[3], 1.0)
        self.assertEqual(data_row[4], "No")
        self.assertEqual(data_row[7], "Sí")
        self.assertEqual(data_row[8], "Test Vendor ES")
        self.assertEqual(data_row[9], "ESB87530432")

    def test_report_xlsx_sale_to_excepted_customer(self):
        """Case of a customer exempted from the digital canon with a
        certificate as a Public Administration.
        """
        self.create_sale_with_invoice(self.excepted_customer_es)
        data_row = self._render_report_xlsx(self.wizard, self.report, row_n=4)
        self.assertEqual(data_row[0], "Mayorista/Minorista")
        self.assertEqual(data_row[1], "Teléfono inteligente hasta 64 Gb - 3,25")
        self.assertEqual(data_row[2], "Brand X")
        self.assertEqual(data_row[3], 1.0)
        self.assertEqual(data_row[4], "Sí")
        self.assertEqual(data_row[5], "Administraciones Públicas")
        self.assertEqual(data_row[7], "Sí")
        self.assertEqual(data_row[8], "Test Vendor ES")
        self.assertEqual(data_row[9], "ESB87530432")
        self.assertEqual(data_row[10], "BILL/2025/09/0001")
        self.assertEqual(data_row[11], 0.0)
        self.assertEqual(data_row[13], "BILL/2025/09/0001")
        self.assertEqual(data_row[20], "Test Excepted Customer ES")

    def test_report_xlsx_sale_to_export_customer(self):
        """Case of exportation: product purchased in Spain and sold to a
        customer outside Spain.
        """
        self.create_sale_with_invoice(self.customer_us)
        data_row = self._render_report_xlsx(self.wizard, self.report, row_n=4)
        self.assertEqual(data_row[0], "Mayorista/Minorista")
        self.assertEqual(data_row[1], "Teléfono inteligente hasta 64 Gb - 3,25")
        self.assertEqual(data_row[2], "Brand X")
        self.assertEqual(data_row[3], 1.0)
        self.assertEqual(data_row[4], "Sí")
        self.assertEqual(data_row[5], "Exportaciones")
        self.assertEqual(data_row[6], "United States")
        self.assertEqual(data_row[7], "Sí")
        self.assertEqual(data_row[8], "Test Vendor ES")
        self.assertEqual(data_row[9], "ESB87530432")
        self.assertEqual(data_row[10], "BILL/2025/09/0001")
        self.assertEqual(data_row[11], 0.0)
        self.assertEqual(data_row[13], "BILL/2025/09/0001")
        self.assertEqual(data_row[20], "Test Customer US")

    def test_report_xlsx_sale_backorder(self):
        """Case with two purchases linked to a sale order that generated a
        backorder and therefore has two outgoing pickings.
        """
        self.create_purchase_with_invoice(
            self.vendor_es, self.product, self.lot_mobile_2
        )
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer_es.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                        },
                    )
                ],
            }
        )
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].quantity = 1
        picking.move_line_ids[1].quantity = 0
        picking.move_line_ids.lot_id = self.lot_mobile_1
        action_data = picking.button_validate()
        backorder_wizard = Form(
            self.env["stock.backorder.confirmation"].with_context(
                **action_data["context"]
            )
        ).save()
        backorder_wizard.process()
        picking_2 = self.sale_order.picking_ids[0]
        picking_2.action_assign()
        picking_2.move_line_ids.quantity = 1
        picking_2.move_line_ids.lot_id = self.lot_mobile_2
        picking_2.button_validate()
        self.sale_order._create_invoices()
        self.sale_order.invoice_ids.invoice_date = fields.Date.today()
        self.sale_order.invoice_ids.action_post()
        data_row_1 = self._render_report_xlsx(self.wizard, self.report, row_n=4)
        data_row_2 = self._render_report_xlsx(self.wizard, self.report, row_n=5)
        self.assertEqual(data_row_1[0], "Mayorista/Minorista")
        self.assertEqual(data_row_1[1], "Teléfono inteligente hasta 64 Gb - 3,25")
        self.assertEqual(data_row_1[2], "Brand X")
        self.assertEqual(data_row_1[3], 2.0)
        self.assertEqual(data_row_1[4], "No")
        self.assertEqual(data_row_1[7], "Sí")
        self.assertEqual(data_row_1[8], "Test Vendor ES")
        self.assertEqual(data_row_1[9], "ESB87530432")
        self.assertEqual(data_row_2[0], "Mayorista/Minorista")
        self.assertEqual(data_row_2[1], "Teléfono inteligente hasta 64 Gb - 3,25")
        self.assertEqual(data_row_2[2], "Brand X")
        self.assertEqual(data_row_2[3], 2.0)
        self.assertEqual(data_row_2[4], "No")
        self.assertEqual(data_row_2[7], "Sí")
        self.assertEqual(data_row_2[8], "Test Vendor ES")
        self.assertEqual(data_row_2[9], "ESB87530432")

    def test_report_vendor_bill_multiple_invoices(self):
        """When a purchase has multiple invoices, the report should pick the
        posted one and not fail with a singleton error."""
        self.create_sale_with_invoice(self.excepted_customer_es)
        purchase = self.env["purchase.order"].search(
            [("partner_id", "=", self.vendor_es.id)], limit=1
        )
        posted_bill = purchase.invoice_ids.filtered(lambda i: i.state == "posted")
        self.assertTrue(posted_bill)
        self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.vendor_es.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "purchase_line_id": purchase.order_line[:1].id,
                        }
                    )
                ],
            }
        )
        self.assertEqual(len(purchase.invoice_ids), 2)
        data_row = self._render_report_xlsx(self.wizard, self.report, row_n=4)
        self.assertEqual(data_row[0], "Mayorista/Minorista")
        self.assertEqual(data_row[4], "Sí")
        self.assertEqual(data_row[10], posted_bill[:1].name)

    def test_report_xlsx_sale_mixed_providers(self):
        """Case of a single outgoing picking that contains two lots
        coming from two different providers: one national and one
        foreign.
        """
        self.create_purchase_with_invoice(
            self.vendor_us, self.product, self.lot_mobile_2
        )
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer_es.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                        },
                    )
                ],
            }
        )
        self.sale_order.action_confirm()
        self.sale_order.picking_ids.action_assign()
        self.sale_order.picking_ids.move_line_ids[0].quantity = 1
        self.sale_order.picking_ids.move_line_ids[1].quantity = 1
        self.sale_order.picking_ids.button_validate()
        self.sale_order._create_invoices()
        self.sale_order.invoice_ids.invoice_date = fields.Date.today()
        self.sale_order.invoice_ids.action_post()
        data_row_1 = self._render_report_xlsx(self.wizard, self.report, row_n=4)
        data_row_2 = self._render_report_xlsx(self.wizard, self.report, row_n=5)
        self.assertEqual(data_row_1[0], "Fabricante/Importador")
        self.assertEqual(data_row_1[1], "Teléfono inteligente hasta 64 Gb - 3,25")
        self.assertEqual(data_row_1[2], "Brand X")
        self.assertEqual(data_row_1[3], 2.0)
        self.assertEqual(data_row_1[4], "No")
        self.assertEqual(data_row_1[7], "No")
        self.assertEqual(data_row_2[0], "Mayorista/Minorista")
        self.assertEqual(data_row_2[1], "Teléfono inteligente hasta 64 Gb - 3,25")
        self.assertEqual(data_row_2[2], "Brand X")
        self.assertEqual(data_row_2[3], 2.0)
        self.assertEqual(data_row_2[4], "No")
        self.assertEqual(data_row_2[7], "Sí")
        self.assertEqual(data_row_2[8], "Test Vendor ES")
        self.assertEqual(data_row_2[9], "ESB87530432")
