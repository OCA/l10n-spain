# Copyright 2024-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging
from io import StringIO

from freezegun import freeze_time
from xlrd import open_workbook

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.592")


@freeze_time("2024-01-01", tick=True)
class TestL10nEsAeatMod592(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write(
            {
                "company_plastic_acquirer": True,
                "company_plastic_manufacturer": True,
                "external_report_layout_id": cls.env.ref(
                    "web.external_layout_standard"
                ).id,
            }
        )
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test Product A",
                "is_plastic_tax": True,
                "tax_plastic_type": "acquirer",
                "plastic_tax_weight": 10,
                "plastic_weight_non_recyclable": 6,
                "plastic_type_key": "A",
                "plastic_tax_regime_acquirer": "A",
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Test Product B",
                "is_plastic_tax": True,
                "tax_plastic_type": "acquirer",
                "plastic_tax_weight": 5,
                "plastic_weight_non_recyclable": 3,
                "plastic_type_key": "B",
                "plastic_tax_regime_acquirer": "B",
            }
        )
        cls.product_c = cls.env["product.product"].create(
            {
                "name": "Test Product C",
            }
        )
        products = cls.product_a + cls.product_b + cls.product_c
        picking_type_out = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.company.id)], limit=1
        )
        picking_form = Form(
            cls.env["stock.picking"].with_context(
                default_picking_type_id=picking_type_out.id,
            )
        )
        picking_form.partner_id = cls.customer
        for product in products:
            with picking_form.move_ids_without_package.new() as line:
                line.product_id = product
                line.product_uom_qty = 3.0
        cls.picking = picking_form.save()
        # Create model
        cls.model592 = cls.env["l10n.es.aeat.mod592.report"].create(
            {
                "name": "9990000000390",
                "company_id": cls.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2024,
                "period_type": "0A",
                "date_start": "2024-01-01",
                "date_end": "2024-12-31",
                "amount_plastic_tax": 1,
            }
        )
        cls.report_obj = cls.env["ir.actions.report"]
        # Reset sequences for testing
        cls.env.ref(
            "l10n_es_aeat_mod592.seq_mod592_report_acquirer"
        ).number_next_actual = 1
        cls.env.ref(
            "l10n_es_aeat_mod592.seq_mod592_report_manufacturer"
        ).number_next_actual = 1

    def test_plastic_weight_non_recyclable(self):
        with self.assertRaises(UserError):
            self.product_a.write({"plastic_weight_non_recyclable": 12})
        self.product_a.plastic_weight_non_recyclable = 8

    def test_model_592(self):
        self.picking.action_confirm()
        res = self.picking.button_validate()
        wizard = self.env[res["res_model"]].with_context(**res["context"]).create({})
        wizard.process()
        self.model592.calculate()
        acquirer_lines = self.model592.acquirer_line_ids
        self.assertEqual(self.model592.total_acquirer_entries, 2)
        self.assertEqual(self.model592.total_weight_acquirer, 45)  # 45 = 30 + 15
        self.assertEqual(
            self.model592.total_weight_acquirer_non_reclyclable, 27
        )  # 27 = 18 + 9
        self.assertEqual(self.model592.total_amount_acquirer, 27)
        sm_a = self.picking.move_ids_without_package.filtered(
            lambda x: x.product_id == self.product_a
        )
        sm_b = self.picking.move_ids_without_package.filtered(
            lambda x: x.product_id == self.product_b
        )
        sm_c = self.picking.move_ids_without_package.filtered(
            lambda x: x.product_id == self.product_c
        )
        self.assertIn(sm_a, acquirer_lines.stock_move_id)
        self.assertIn(sm_b, acquirer_lines.stock_move_id)
        self.assertNotIn(sm_c, acquirer_lines.stock_move_id)
        acquirer_line_a = acquirer_lines.filtered(lambda x: x.stock_move_id == sm_a)
        self.assertEqual(acquirer_line_a.entry_number, "A001")
        self.assertEqual(
            acquirer_line_a.date_done, fields.Date.from_string("2024-01-01")
        )
        self.assertEqual(acquirer_line_a.concept, "2")
        self.assertEqual(acquirer_line_a.product_key, "A")
        self.assertEqual(acquirer_line_a.proof, self.picking.name)
        self.assertEqual(acquirer_line_a.kgs, 30)  # 30 = 10*3
        self.assertEqual(acquirer_line_a.no_recycling_kgs, 18)  # 18 = 6*3
        self.assertEqual(acquirer_line_a.supplier_social_reason, "Test customer")
        self.assertFalse(acquirer_line_a.supplier_document_number)
        self.assertEqual(acquirer_line_a.supplier_document_type, "3")
        self.assertEqual(acquirer_line_a.fiscal_acquirer, "A")
        self.assertFalse(acquirer_line_a.entries_ok)
        acquirer_line_b = acquirer_lines.filtered(lambda x: x.stock_move_id == sm_b)
        self.assertEqual(acquirer_line_b.entry_number, "A002")
        self.assertEqual(
            acquirer_line_b.date_done, fields.Date.from_string("2024-01-01")
        )
        self.assertEqual(acquirer_line_b.concept, "2")
        self.assertEqual(acquirer_line_b.product_key, "B")
        self.assertEqual(acquirer_line_b.proof, self.picking.name)
        self.assertEqual(acquirer_line_b.kgs, 15)  # 15 = 5*3
        self.assertEqual(acquirer_line_b.no_recycling_kgs, 9)  # 9 = 3*3
        self.assertEqual(acquirer_line_b.supplier_social_reason, "Test customer")
        self.assertFalse(acquirer_line_b.supplier_document_number)
        self.assertEqual(acquirer_line_b.supplier_document_type, "3")
        self.assertEqual(acquirer_line_b.fiscal_acquirer, "B")
        self.assertFalse(acquirer_line_b.entries_ok)
        self.assertTrue(self.model592.show_error_acquirer)
        # Without VAT + Recalculate
        self.customer.vat = "12345678Z"
        self.model592.button_recalculate()
        self.assertEqual(self.model592.acquirer_line_ids, acquirer_lines)
        self.assertTrue(acquirer_line_a.entries_ok)
        self.assertTrue(acquirer_line_b.entries_ok)
        self.assertFalse(self.model592.show_error_acquirer)
        self.assertEqual(self.model592.state, "draft")
        self.model592.button_confirm()
        self.assertEqual(self.model592.state, "done")
        res = self.model592.view_action_mod592_report_line_acquirer()
        items = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(acquirer_lines, items)
        # Although it is not correct, add stock_move_c as a manufacturer to test
        # the whole process
        self.product_c.write(
            {
                "is_plastic_tax": True,
                "tax_plastic_type": "manufacturer",
                "plastic_tax_weight": 2,
                "plastic_weight_non_recyclable": 1,
                "plastic_type_key": "C",
                "plastic_tax_regime_acquirer": "C",
            }
        )
        self.model592.manufacturer_line_ids = [(0, 0, {"stock_move_id": sm_c.id})]
        self.assertEqual(self.model592.total_manufacturer_entries, 1)
        self.assertEqual(self.model592.total_weight_manufacturer, 6)  # 6 = 2 * 3
        self.assertEqual(
            self.model592.total_weight_manufacturer_non_reclyclable, 3
        )  # 3 = 1 * 3
        self.assertEqual(self.model592.total_amount_manufacturer, 3)  # 3 = 3 * 1
        self.assertNotIn(sm_a, self.model592.manufacturer_line_ids.stock_move_id)
        self.assertNotIn(sm_b, self.model592.manufacturer_line_ids.stock_move_id)
        self.assertIn(sm_c, self.model592.manufacturer_line_ids.stock_move_id)
        res = self.model592.view_action_mod592_report_line_manufacturer()
        items = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(self.model592.manufacturer_line_ids, items)
        # report_file_name
        self.assertTrue(self.model592.get_report_file_name())
        # export_csv_acquirer
        csv_result_acquirer = self.model592.export_csv_acquirer()
        report_name = csv_result_acquirer["report_name"]
        res = self.report_obj._render(report_name, self.model592.ids, {})
        str_io = StringIO(res[0])
        csv_lines_acquirer = list(
            csv.DictReader(str_io, delimiter=";", quoting=csv.QUOTE_ALL)
        )
        csv_line_1_acquirer = list(csv_lines_acquirer[0].values())
        csv_line_2_acquirer = list(csv_lines_acquirer[1].values())
        self.assertIn("A001", csv_line_1_acquirer)
        self.assertIn("A002", csv_line_2_acquirer)
        self.assertIn(self.picking.name, csv_line_1_acquirer)
        # export_csv_manufacturer
        csv_result_manufacturer = self.model592.export_csv_manufacturer()
        report_csv_name = self.report_obj._get_report_from_name(
            csv_result_manufacturer["report_name"]
        ).report_name
        res = self.report_obj._render(report_csv_name, self.model592.ids, {})
        str_io = StringIO(res[0])
        csv_lines_manufacturer = list(
            csv.DictReader(str_io, delimiter=";", quoting=csv.QUOTE_ALL)
        )
        csv_line_1_manufacturer = list(csv_lines_manufacturer[0].values())
        self.assertIn("M001", csv_line_1_manufacturer)
        self.assertIn(self.picking.name, csv_line_1_manufacturer)
        # export_xlsx_acquirer
        xlsx_res = self.model592.export_xlsx_acquirer()
        res = self.report_obj._get_report_from_name(xlsx_res["report_name"])._render(
            xlsx_res["report_name"], self.model592.ids, {}
        )
        wb = open_workbook(file_contents=res[0])
        sheet = wb.sheet_by_index(0)
        self.assertEqual(sheet.cell(1, 0).value, "A001")
        self.assertEqual(sheet.cell(2, 0).value, "A002")
        # export_xlsx_manufacturer
        xlsx_res = self.model592.export_xlsx_manufacturer()
        res = self.report_obj._get_report_from_name(xlsx_res["report_name"])._render(
            xlsx_res["report_name"], self.model592.ids, {}
        )
        wb = open_workbook(file_contents=res[0])
        sheet = wb.sheet_by_index(0)
        self.assertEqual(sheet.cell(1, 0).value, "M001")
        # report_l10n_es_mod592_pdf
        res = self.report_obj._get_report_from_name(
            "l10n_es_aeat_mod592.report_l10n_es_mod592_pdf"
        )._render_qweb_text(
            "l10n_es_aeat_mod592.report_l10n_es_mod592_pdf", self.model592.ids
        )
        res_text = str(res[0])
        self.assertRegex(res_text, "A001")
        self.assertRegex(res_text, "A002")
        self.assertRegex(res_text, "M001")
        self.assertRegex(res_text, self.picking.name)
