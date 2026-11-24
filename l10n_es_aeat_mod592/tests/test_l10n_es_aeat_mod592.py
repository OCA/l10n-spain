# Copyright 2024-2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import csv
import importlib.util
import io
import logging
from io import StringIO

from freezegun import freeze_time
from openpyxl import load_workbook

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import Form
from odoo.tools.misc import file_path

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.592")


class TestL10nEsAeatMod592(TestL10nEsAeatModBase):
    _test_user_groups = (
        *TestL10nEsAeatModBase._test_user_groups,
        "stock.group_stock_user",
        "product.group_product_manager",
        "uom.group_uom",
        "l10n_es_aeat_mod592.group_mod592_acquirer",
        "l10n_es_aeat_mod592.group_mod592_manufacturer",
    )
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
        warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        picking_form = Form(
            cls.env["stock.picking"].with_context(
                default_picking_type_id=warehouse.out_type_id.id,
            )
        )
        picking_form.partner_id = cls.customer
        for product in products:
            with picking_form.move_ids.new() as line:
                line.product_id = product
                line.product_uom_qty = 3.0
        cls.picking = picking_form.save()
        # Create model
        cls.model592 = cls.env["l10n.es.aeat.mod592.report"].create(
            {
                "name": "9990000000390",
                "company_id": cls.company.id,
                "company_vat": "123456789",
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

    def setUp(self):
        super().setUp()
        # The entry numbers come from standard (non transactional) sequences
        for xmlid in ("seq_mod592_report_acquirer", "seq_mod592_report_manufacturer"):
            self.env.ref(f"l10n_es_aeat_mod592.{xmlid}").sudo().number_next_actual = 1

    def test_plastic_weight_non_recyclable(self):
        with self.assertRaises(UserError):
            self.product_a.write({"plastic_weight_non_recyclable": 12})
        self.product_a.plastic_weight_non_recyclable = 8
        templates = self.env["product.template"].search(
            [("is_plastic_tax", "=", True), ("plastic_type_key", "=", "A")]
        )
        self.assertIn(self.product_a.product_tmpl_id, templates)
        self.assertNotIn(self.product_b.product_tmpl_id, templates)

    @freeze_time("2024-01-01", tick=True)
    def test_model_592(self):
        self.picking.action_confirm()
        self.picking.button_validate()
        self.model592.calculate()
        acquirer_lines = self.model592.acquirer_line_ids
        self.assertEqual(self.model592.total_acquirer_entries, 2)
        self.assertEqual(self.model592.total_weight_acquirer, 45)  # 45 = 30 + 15
        self.assertEqual(
            self.model592.total_weight_acquirer_non_reclyclable, 27
        )  # 27 = 18 + 9
        # Shipping outside Spain is a deduction (concept 2), not a quota
        self.assertEqual(self.model592.plastic_quantity, 0)
        self.assertEqual(self.model592.plastic_tax_base, 0)
        self.assertEqual(self.model592.plastic_quota, 0)
        self.assertEqual(self.model592.plastic_deduction, 27)  # 27 * 1
        self.assertEqual(self.model592.plastic_result, -27)
        sm_a = self.picking.move_ids.filtered(lambda x: x.product_id == self.product_a)
        sm_b = self.picking.move_ids.filtered(lambda x: x.product_id == self.product_b)
        sm_c = self.picking.move_ids.filtered(lambda x: x.product_id == self.product_c)
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
        # With the VAT of the customer of another State + Recalculate
        self.customer.write(
            {"country_id": self.env.ref("base.de").id, "vat": "DE123456788"}
        )
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
        # No manufacturer move is searched yet (see ROADMAP)
        self.assertFalse(self.model592.manufacturer_line_ids)
        self.assertEqual(self.model592.total_manufacturer_entries, 0)
        res = self.model592.view_action_mod592_report_line_manufacturer()
        items = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(self.model592.manufacturer_line_ids, items)
        # report_file_name
        self.assertTrue(self.model592.get_report_file_name())
        # export_csv_acquirer
        csv_result_acquirer = self.model592.export_csv_acquirer()
        res = self.report_obj._render(
            csv_result_acquirer["report_name"], self.model592.ids, {}
        )
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
        res = self.report_obj._render(
            csv_result_manufacturer["report_name"], self.model592.ids, {}
        )
        str_io = StringIO(res[0])
        csv_lines_manufacturer = list(
            csv.DictReader(str_io, delimiter=";", quoting=csv.QUOTE_ALL)
        )
        self.assertFalse(csv_lines_manufacturer)
        # export_xlsx_acquirer
        xlsx_res = self.model592.export_xlsx_acquirer()
        res = self.report_obj._render(xlsx_res["report_name"], self.model592.ids, {})
        file = io.BytesIO(res[0])
        wb = load_workbook(file)
        sheet = wb.active
        self.assertEqual(sheet.cell(2, 1).value, "A001")
        self.assertEqual(sheet.cell(3, 1).value, "A002")
        # # export_xlsx_manufacturer
        xlsx_res = self.model592.export_xlsx_manufacturer()
        res = self.report_obj._render(xlsx_res["report_name"], self.model592.ids, {})
        file = io.BytesIO(res[0])
        wb = load_workbook(file)
        sheet = wb.active
        self.assertFalse(sheet.cell(2, 1).value)
        # report_l10n_es_mod592_pdf
        res = self.env["ir.actions.report"]._render_qweb_text(
            "l10n_es_aeat_mod592.report_l10n_es_mod592_pdf", self.model592.ids
        )
        res_text = str(res[0])
        self.assertRegex(res_text, "A001")
        self.assertRegex(res_text, "A002")
        self.assertRegex(res_text, self.picking.name)

    def _validate_picking(self, picking_type, partner, lines):
        picking_form = Form(
            self.env["stock.picking"].with_context(
                default_picking_type_id=picking_type.id
            )
        )
        picking_form.partner_id = partner
        for product, qty, uom in lines:
            with picking_form.move_ids.new() as move_form:
                move_form.product_id = product
                move_form.product_uom_qty = qty
                if uom:
                    move_form.uom_id = uom
        picking = picking_form.save()
        picking.action_confirm()
        picking.button_validate()
        return picking

    def _scrap(self, picking, product, qty):
        scrap_form = Form.from_action(self.env, picking.action_scrap())
        scrap_form.product_id = product
        scrap_form.quantity = qty
        scrap_form.save().action_scrap()

    def _return(self, picking, qty):
        action = picking.action_return()
        return_picking = self.env["stock.picking"].browse(action["res_id"])
        with (
            Form(return_picking) as return_form,
            return_form.move_ids.edit(0) as move_form,
        ):
            move_form.product_uom_qty = qty
        return_picking.action_confirm()
        return_picking.button_validate()
        return return_picking

    @freeze_time("2024-03-15")
    def test_model_592_acquirer_csv_export(self):
        """Intra-community acquisition, scrap, return to the supplier and
        shipping outside Spain, exported to the CSV file the AEAT imports."""
        supplier = self.env["res.partner"].create(
            {
                "name": "Test FR supplier",
                "country_id": self.env.ref("base.fr").id,
                "vat": "FR23334175221",
            }
        )
        customer = self.env["res.partner"].create(
            {
                "name": "Test DE customer",
                "country_id": self.env.ref("base.de").id,
                "vat": "DE123456788",
            }
        )
        pack = self.env["uom.uom"].create(
            {
                "name": "Pack of 6",
                "relative_factor": 6,
                "relative_uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )
        self.product_a.is_storable = True
        self.product_b.write({"is_storable": True, "uom_ids": [Command.link(pack.id)]})
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        receipt = self._validate_picking(
            warehouse.in_type_id, supplier, [(self.product_a, 10, False)]
        )
        receipt_b = self._validate_picking(
            warehouse.in_type_id, supplier, [(self.product_b, 2, pack)]
        )
        self._scrap(receipt, self.product_a, 1)
        return_picking = self._return(receipt, 2)
        delivery = self._validate_picking(
            warehouse.out_type_id, customer, [(self.product_a, 3, False)]
        )
        self.model592.calculate()
        self.assertEqual(
            self.model592.acquirer_line_ids.mapped("concept"),
            ["1", "1", "3", "4", "2"],
        )
        self.assertEqual(self.model592.acquirer_line_ids.mapped("error_text"), [""] * 5)
        self.assertFalse(self.model592.show_error_acquirer)
        self.model592.button_confirm()
        action = self.model592.export_csv_acquirer()
        content = self.env["ir.actions.report"]._render_csv(
            action["report_name"], self.model592.ids, action["data"]
        )[0]
        self.assertEqual(
            content.split("\r\n"),
            [
                (
                    "Número Asiento;Fecha Hecho Contabilizado;Concepto;Clave Producto;"
                    "Descripción Producto;Régimen Fiscal;Justificante;"
                    "Prov./Dest.: Tipo Documento;Prov./Dest.: Nº documento;"
                    "Prov./Dest.: Razón social;Kilogramos;Kilogramos No Reciclados;"
                    "Observaciones"
                ),
                (
                    f"A001;15-03-2024;1;A;;A;{receipt.name};2;FR23334175221;"
                    "Test FR supplier;100,0;60,0;"
                ),
                (
                    f"A002;15-03-2024;1;B;;B;{receipt_b.name};2;FR23334175221;"
                    "Test FR supplier;60,0;36,0;"
                ),
                f"A003;15-03-2024;3;A;;;{receipt.name};;;;10,0;6,0;",
                (
                    f"A004;15-03-2024;4;A;;;{return_picking.name};2;FR23334175221;"
                    "Test FR supplier;20,0;12,0;"
                ),
                (
                    f"A005;15-03-2024;2;A;;;{delivery.name};2;DE123456788;"
                    "Test DE customer;30,0;18,0;"
                ),
                "",
            ],
        )

    @freeze_time("2024-03-15")
    def test_liquidation_acquirer(self):
        """The intra-community acquisitions make the quota and the shipping
        outside Spain, the scrap and the return to the supplier are deducted
        from it"""
        supplier = self.env["res.partner"].create(
            {
                "name": "Test FR supplier",
                "country_id": self.env.ref("base.fr").id,
                "vat": "FR23334175221",
            }
        )
        customer = self.env["res.partner"].create(
            {
                "name": "Test DE customer",
                "country_id": self.env.ref("base.de").id,
                "vat": "DE123456788",
            }
        )
        self.product_a.is_storable = True
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        receipt = self._validate_picking(
            warehouse.in_type_id, supplier, [(self.product_a, 10, False)]
        )
        self._scrap(receipt, self.product_a, 1)
        self._return(receipt, 2)
        self._validate_picking(
            warehouse.out_type_id, customer, [(self.product_a, 3, False)]
        )
        report = self.env["l10n.es.aeat.mod592.report"].create(
            {
                "name": "9990000000391",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2024,
                "period_type": "1T",
                "date_start": "2024-01-01",
                "date_end": "2024-03-31",
            }
        )
        report.calculate()
        self.assertEqual(
            report.acquirer_line_ids.mapped("concept"), ["1", "3", "4", "2"]
        )
        self.assertEqual(report.amount_plastic_tax, 0.45)
        self.assertEqual(report.plastic_quantity, 100)  # 10 * 10
        self.assertEqual(report.plastic_tax_base, 60)  # 10 * 6
        self.assertEqual(report.plastic_quota, 27)  # 60 * 0.45
        # (1 + 2 + 3) * 6 = 36 kg * 0.45
        self.assertEqual(report.plastic_deduction, 16.2)
        self.assertAlmostEqual(report.plastic_result, 10.8)  # 27 - 16.2
        # The book keeps every entry
        self.assertEqual(report.total_weight_acquirer, 160)
        self.assertEqual(report.total_weight_acquirer_non_reclyclable, 96)

    @freeze_time("2024-01-01", tick=True)
    def test_recalculate_removes_lines(self):
        """The line of a move that doesn't belong to the report anymore is
        removed when recalculating, and the other ones keep their number"""
        self.customer.write(
            {"country_id": self.env.ref("base.de").id, "vat": "DE123456788"}
        )
        self.picking.action_confirm()
        self.picking.button_validate()
        self.model592.calculate()
        self.assertEqual(
            self.model592.acquirer_line_ids.mapped("entry_number"), ["A001", "A002"]
        )
        self.product_b.is_plastic_tax = False
        self.model592.button_recalculate()
        line = self.model592.acquirer_line_ids
        self.assertEqual(line.product_id, self.product_a)
        self.assertEqual(line.entry_number, "A001")
        self.assertEqual(self.model592.total_weight_acquirer, 30)

    @freeze_time("2024-01-01", tick=True)
    def test_line_without_concept(self):
        """A delivery address abroad of a Spanish customer without NIF is
        searched as a shipping outside Spain, but the concept is taken from the
        customer: the line has no concept and the report can't be confirmed"""
        customer_es = self.env["res.partner"].create(
            {
                "name": "Test ES customer",
                "country_id": self.env.ref("base.es").id,
            }
        )
        address_pt = self.env["res.partner"].create(
            {
                "name": "Test PT warehouse",
                "type": "delivery",
                "parent_id": customer_es.id,
                "country_id": self.env.ref("base.pt").id,
            }
        )
        self.assertEqual(customer_es.plastic_document_type, "1")
        self.assertNotEqual(address_pt.plastic_document_type, "1")
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self._validate_picking(
            warehouse.out_type_id, address_pt, [(self.product_a, 2, False)]
        )
        self.model592.calculate()
        line = self.model592.acquirer_line_ids
        self.assertFalse(line.concept)
        self.assertIn("Without concept", line.error_text)
        self.assertTrue(self.model592.show_error_acquirer)
        with self.assertRaises(UserError):
            self.model592.button_confirm()

    def test_plastic_document_type_identifiers(self):
        """The document type follows the identifiers of the contact"""
        partner = self.env["res.partner"].create(
            {"name": "Test ES person", "country_id": self.env.ref("base.es").id}
        )
        partner.l10n_es_passport = "AB1234567"
        self.assertEqual(partner.plastic_document_type, "3")
        partner.write({"l10n_es_passport": False, "vat": "12345678Z"})
        self.assertEqual(partner.plastic_document_type, "1")
        partner.write({"country_id": self.env.ref("base.fr").id, "vat": False})
        partner.vat = "FR23334175221"
        self.assertEqual(partner.plastic_document_type, "2")

    @freeze_time("2024-01-01", tick=True)
    def test_account_user_opens_report(self):
        """A user of the accounting group without management rights opens the
        report with its lines"""
        self.account_user.sudo().group_ids += self.env.ref(
            "l10n_es_aeat_mod592.group_mod592_acquirer"
        )
        self.picking.action_confirm()
        self.picking.button_validate()
        self.model592.calculate()
        report = Form(self.model592.with_user(self.account_user))
        self.assertEqual(report.num_lines_acquirer, 2)
        self.assertEqual(report.total_weight_acquirer, 45)
        action = self.model592.with_user(
            self.account_user
        ).view_action_mod592_report_line_acquirer()
        lines = self.env[action["res_model"]].with_user(self.account_user)
        self.assertEqual(
            lines.search(action["domain"]).mapped("entry_number"), ["A001", "A002"]
        )

    def test_template_plastic_info_to_variant(self):
        """The plastic info written in a template with one variant goes to it"""
        template = self.env["product.template"].create({"name": "Test template"})
        template.write(
            {
                "is_plastic_tax": True,
                "tax_plastic_type": "acquirer",
                "plastic_type_key": "A",
                "plastic_tax_weight": 4,
                "plastic_weight_non_recyclable": 2,
                "plastic_tax_regime_acquirer": "A",
            }
        )
        variant = template.product_variant_ids
        self.assertTrue(variant.is_plastic_tax)
        self.assertEqual(variant.plastic_tax_weight, 4)
        self.assertEqual(variant.plastic_weight_non_recyclable, 2)
        self.assertEqual(variant.plastic_tax_regime_acquirer, "A")

    def test_migration_recomputes_document_type(self):
        """The migration to 20.0 computes again the stored document type"""
        partner = self.env["res.partner"].create(
            {
                "name": "Test FR supplier",
                "country_id": self.env.ref("base.fr").id,
                "vat": "FR23334175221",
            }
        )
        self.assertEqual(partner.plastic_document_type, "2")
        self.env.flush_all()
        # As computed in 19.0 from the identifiers moved by l10n_es_aeat
        self.env.cr.execute(
            "UPDATE res_partner SET plastic_document_type = '3' WHERE id = %s",
            [partner.id],
        )
        partner.invalidate_recordset(["plastic_document_type"])
        self.assertEqual(partner.plastic_document_type, "3")
        script = file_path(
            "l10n_es_aeat_mod592/migrations/20.0.1.0.0/post-migration.py"
        )
        spec = importlib.util.spec_from_file_location("post_migration", script)
        post_migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(post_migration)
        # Without the frame of the Odoo migration manager that its decorator
        # inspects
        post_migration.migrate.__wrapped__(self.env, "19.0.1.0.0")
        partner.invalidate_recordset(["plastic_document_type"])
        self.assertEqual(partner.plastic_document_type, "2")
