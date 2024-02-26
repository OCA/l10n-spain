# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_es_sigaus_account.tests.common import TestL10nEsSigausCommon


class TestL10nEsSigausStockPickingReportValued(TestL10nEsSigausCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.tax = cls.env["account.tax"].create(
            {"name": "Tax 21.0%", "amount": 21.0, "amount_type": "percent"}
        )
        cls.env.ref("l10n_es_sigaus_account.aportacion_sigaus_product_template").write(
            {"taxes_id": [cls.tax.id]}
        )

    def test_valued_picking_sigaus_amount(self):
        sale = self.env["sale.order"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "date_order": "2023-01-01",
                "fiscal_position_id": self.fiscal_position_sigaus.id,
                "order_line": [
                    (
                        0,
                        False,
                        {
                            "product_id": self.product_sigaus_in_product.id,
                            "product_uom_qty": 10,
                            "price_unit": 2,
                            "tax_id": [self.tax.id],
                        },
                    )
                ],
            }
        )
        sale.action_confirm()
        sale.write({"date_order": "2023-01-01"})
        picking = sale.picking_ids

        # No 'done' quantity
        line = picking.move_line_ids
        self.assertAlmostEqual(line.sigaus_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(line.sigaus_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(line.sigaus_amount_total, 0.726, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_total, 0.726, places=2)
        self.assertAlmostEqual(
            picking.picking_total_with_sigaus, sale.amount_total, places=2
        )

        # With 'done' quantity
        line.write({"qty_done": 6})
        # Force amounts recomputation, as stock_picking_report_valued module d
        # does not do it
        line._compute_sale_order_line_fields()
        picking._compute_amount_all()
        self.assertAlmostEqual(line.sigaus_amount_subtotal, 0.36, places=2)
        self.assertAlmostEqual(line.sigaus_amount_tax, 0.0756, places=2)
        self.assertAlmostEqual(line.sigaus_amount_total, 0.4356, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_subtotal, 0.36, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_tax, 0.0756, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_total, 0.4356, places=2)
        self.assertAlmostEqual(picking.picking_total_with_sigaus, 14.9556, places=2)

        # All 'done'
        line.write({"qty_done": 10})
        # Force amounts recomputation, as stock_picking_report_valued module d
        # does not do it
        line._compute_sale_order_line_fields()
        picking._compute_amount_all()
        self.assertAlmostEqual(line.sigaus_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(line.sigaus_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(line.sigaus_amount_total, 0.726, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_subtotal, 0.6, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_tax, 0.126, places=2)
        self.assertAlmostEqual(picking.sigaus_amount_total, 0.726, places=2)
        self.assertAlmostEqual(
            picking.picking_total_with_sigaus, sale.amount_total, places=2
        )
