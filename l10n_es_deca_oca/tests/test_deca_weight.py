# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from .common import DecaCommon


@tagged("post_install", "-at_install")
class TestDecaWeight(DecaCommon, TransactionCase):
    def test_invalid_resolver_keeps_inventory_usable_but_refuses_issuance(self):
        with (
            mute_logger("odoo.addons.l10n_es_deca_oca.models.stock_move"),
            patch.object(
                type(self.env["product.template"]),
                "_get_weight_uom_id_from_ir_config_parameter",
                side_effect=ValueError("invalid configured ID"),
            ),
        ):
            self.move.product_uom_qty = 1
            self.assertEqual(self.move.deca_weight, 0)
            with self.assertRaisesRegex(UserError, "weight unit"):
                self.picking._check_deca_required_fields()

    def test_positive_weight_below_display_precision_is_rejected(self):
        # Preserve the tiny input with native product weight rounding enabled.
        self.env.ref("product.decimal_stock_weight").digits = 9
        self.product.weight = 0.00000001
        self.assertGreater(self.product.weight, 0)
        self.assertGreater(self.picking.deca_weight, 0)
        with self.assertRaisesRegex(UserError, "six decimal"):
            self.picking._check_deca_required_fields()

    def test_native_fallback_and_pounds(self):
        parameters = self.env["ir.config_parameter"]
        parameters.search([("key", "=", "product_default_weight_uom_id")]).unlink()
        parameters.set_param("product.weight_in_lbs", "0")
        self.move.product_uom_qty = 1
        self.assertAlmostEqual(self.move.deca_weight, 2.5, places=9)
        parameters.set_param("product.weight_in_lbs", "1")
        self.move.product_uom_qty = 2
        # Native uom/data/uom_data.xml uses the rounded factor 2.20462.
        self.assertAlmostEqual(self.move.deca_weight, 5 / 2.20462, places=9)

    def test_invalid_units_and_mixed_cargo(self):
        kg = self.env.ref("uom.product_uom_kgm")
        mass_product = self.env["product.product"].create(
            {
                "name": "DECA mass cargo",
                "type": "consu",
                "uom_id": kg.id,
                "uom_po_id": kg.id,
            }
        )
        mass_move = self.move.copy(
            {"product_id": mass_product.id, "product_uom": kg.id, "product_uom_qty": 2}
        )
        for invalid in (
            self.env["uom.uom"],
            self.env["uom.uom"].browse(2147483647),
            self.env.ref("uom.product_uom_unit"),
            kg | self.env.ref("uom.product_uom_gram"),
        ):
            with (
                self.subTest(ids=invalid.ids),
                mute_logger("odoo.addons.l10n_es_deca_oca.models.stock_move"),
                patch.object(
                    type(self.env["product.template"]),
                    "_get_weight_uom_id_from_ir_config_parameter",
                    return_value=invalid,
                ),
            ):
                self.env.add_to_compute(
                    self.move._fields["deca_weight"], self.move | mass_move
                )
                (self.move | mass_move)._recompute_recordset(["deca_weight"])
                self.assertEqual(self.move.deca_weight, 0)
                self.assertEqual(mass_move.deca_weight, 2)
                self.assertEqual(self.picking.deca_weight, 2)
                with self.assertRaisesRegex(UserError, "weight unit"):
                    self.picking._check_deca_required_fields()
        with (
            mute_logger("odoo.addons.l10n_es_deca_oca.models.stock_move"),
            patch.object(
                type(self.env["product.template"]),
                "_get_weight_uom_id_from_ir_config_parameter",
                side_effect=TypeError("invalid value"),
            ),
        ):
            self.env.add_to_compute(self.move._fields["deca_weight"], self.move)
            self.move._recompute_recordset(["deca_weight"])
            self.assertEqual(self.move.deca_weight, 0)

    def test_tiny_line_with_valid_total_and_formatted_hash(self):
        # Keep distinct source weights that render identically at six decimals.
        self.env.ref("product.decimal_stock_weight").digits = 9
        self.move.product_uom_qty = 1
        self.product.weight = 2.500000001
        before_weight = self.product.weight
        before = self.picking._get_deca_hash()
        self.product.weight = 2.500000002
        self.assertNotEqual(self.product.weight, before_weight)
        self.assertEqual(self.picking._get_deca_hash(), before)
        tiny_product = self.env["product.product"].create(
            {"name": "DECA tiny cargo", "type": "consu", "weight": 0.00000001}
        )
        self.move.copy({"product_id": tiny_product.id, "product_uom_qty": 1})
        self.assertGreater(self.picking.deca_weight, 2)
        with self.assertRaisesRegex(UserError, "six decimal"):
            self.picking._check_deca_required_fields()

    def test_effective_grams_preserved_in_storage_and_report(self):
        gram = self.env.ref("uom.product_uom_gram")
        self.env["ir.config_parameter"].set_param(
            "product_default_weight_uom_id", gram.id
        )
        # The native resolver is the public extension seam. This also exercises
        # the behavior on stock-only installations without product_logistics_uom.
        with patch.object(
            type(self.env["product.template"]),
            "_get_weight_uom_id_from_ir_config_parameter",
            return_value=gram,
        ):
            self.move.product_uom_qty = 1
            self.env.flush_all()
            self.move.invalidate_recordset(["deca_weight"])
            self.picking.invalidate_recordset(["deca_weight"])
            self.assertAlmostEqual(self.move.deca_weight, 0.0025, places=9)
            self.assertAlmostEqual(self.picking.deca_weight, 0.0025, places=9)
            printed = self.picking._get_deca_report_data()["goods"][0]["weight"]
            self.assertEqual(printed.replace(",", "."), "0.0025")
            self.move.product_uom_qty = 10
            self.env.flush_all()
            self.move.invalidate_recordset(["deca_weight"])
            self.picking.invalidate_recordset(["deca_weight"])
            self.assertAlmostEqual(self.move.deca_weight, 0.025, places=9)
            self.assertAlmostEqual(self.picking.deca_weight, 0.025, places=9)
