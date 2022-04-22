# Copyright 2021 Tecnativa - João Marques

from datetime import datetime

from odoo import _
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..hooks import post_init_hook


@tagged("post_install", "-at_install")
class TestL10nIntraStatReport(AccountTestInvoicingCommon):
    @classmethod
    def _create_invoice(cls, inv_type, partner, product=None):
        product = product or cls.product
        if inv_type in ("out_invoice", "in_refund"):
            account = cls.company_data["default_account_revenue"]
        elif inv_type in ("in_invoice", "out_refund"):
            account = cls.company_data["default_account_expense"]
        move_form = Form(
            cls.env["account.move"].with_context(default_move_type=inv_type)
        )
        move_form.ref = "ABCDE"
        move_form.partner_id = partner
        move_form.partner_shipping_id = partner
        move_form.invoice_date = datetime.today()
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.account_id = account
            line_form.product_id = product
            line_form.quantity = 1.0
            line_form.price_unit = 100
        inv = move_form.save()
        inv.action_post()
        return inv

    @classmethod
    def _create_declaration(cls, declaration_type):
        return cls.env["l10n.es.intrastat.product.declaration"].create(
            {
                "year": datetime.today().year,
                "month": str(datetime.today().month).zfill(2),
                "declaration_type": declaration_type,
                "action": "replace",
            }
        )

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        chart_template_ref = (
            "l10n_es.account_chart_template_common" or chart_template_ref
        )
        super().setUpClass(chart_template_ref=chart_template_ref)
        # Set current company to Spanish
        cls.env.user.company_id.country_id = cls.env.ref("base.es").id
        cls.env.user.company_id.incoterm_id = cls.env.ref("account.incoterm_FCA").id
        # Create Intrastat partners
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Test Partner FR", "country_id": cls.env.ref("base.fr").id}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "Test Partner PT", "country_id": cls.env.ref("base.pt").id}
        )
        # Import Intrastat data
        cls.env["l10n.es.intrastat.code.import"].create({}).execute()
        # Create product ans assign random HS Code
        cls.hs_code = cls.env["hs.code"].search([], limit=1)
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "hs_code_id": cls.hs_code.id,
                "origin_country_id": cls.env.ref("base.fr").id,
            }
        )
        # Invoices to be used in dispatches
        cls.invoices = {
            "dispatches": {
                "invoices": [],
                cls.partner_1.country_id: 0,
                cls.partner_2.country_id: 0,
            },
            "arrivals": {
                "invoices": [],
                cls.partner_1.country_id: 0,
                cls.partner_2.country_id: 0,
            },
        }
        for inv_type in ("out_invoice", "in_refund", "in_invoice", "out_refund"):
            declaration_type = (
                "dispatches" if inv_type in ("out_invoice", "in_refund") else "arrivals"
            )
            for partner in (cls.partner_1, cls.partner_2):
                invoice = cls._create_invoice(inv_type, partner)
                invoice.intrastat_fiscal_position = True
                cls.invoices[declaration_type]["invoices"].append(invoice)
                cls.invoices[declaration_type][partner.country_id] += 1

    def test_post_init_hook(self):
        fp = self.env["account.fiscal.position"].create(
            {
                "name": "Test FP",
                "intrastat": False,
            }
        )
        item = self.env["ir.model.data"].create(
            {
                "name": "l10n_es_intrastat_report_fp_intra_private",
                "model": "account.fiscal.position",
                "module": "l10n_es",
                "res_id": fp.id,
            }
        )
        post_init_hook(self.env.cr, None)
        fp = self.env["account.fiscal.position"].browse(item.res_id)
        self.assertTrue(fp.intrastat)

    def _check_move_lines_present(self, original, target):
        for move in original:
            for line in move.invoice_line_ids:
                self.assertTrue(line in target.mapped("invoice_line_id"))

    def _check_declaration_lines(self, lines, fr_qty, pt_qty):
        for line in lines:
            if line.src_dest_country_id == self.env.ref("base.fr"):
                self.assertEqual(line.suppl_unit_qty, fr_qty)
            if line.src_dest_country_id == self.env.ref("base.pt"):
                self.assertEqual(line.suppl_unit_qty, pt_qty)

    def test_report_creation_dispatches(self):
        # Generate report
        report_dispatches = self._create_declaration("dispatches")
        report_dispatches.action_gather()
        self._check_move_lines_present(
            self.invoices["dispatches"]["invoices"],
            report_dispatches.computation_line_ids,
        )
        report_dispatches.generate_declaration()
        self.assertEqual(
            len(report_dispatches.declaration_line_ids), 2
        )  # One line for each country
        self.assertEqual(
            report_dispatches.declaration_line_ids.mapped("hs_code_id"),
            self.hs_code,
        )
        self._check_declaration_lines(
            report_dispatches.declaration_line_ids,
            self.invoices["dispatches"][self.partner_1.country_id],
            self.invoices["dispatches"][self.partner_2.country_id],
        )
        csv_result = report_dispatches._generate_csv()
        csv_lines = csv_result.decode("utf-8").rstrip().splitlines()
        self.assertEqual(len(csv_lines), 2)
        for line in csv_lines:
            items = line.split(";")
            self.assertTrue(items[0] in ("PT", "FR"))
            self.assertEqual(items[6], self.hs_code.local_code)

    def test_report_creation_dispatches_notes_and_lines(self):
        # Generate report
        self.product.origin_country_id = False
        report_dispatches = self._create_declaration("dispatches")
        expected_invoices = self.invoices["dispatches"]["invoices"]
        expected_notes = [
            _("Missing origin country on product %s. ") % (self.product.display_name),
            _("Missing partner vat on invoice %s. ") % (expected_invoices[0].name),
        ]
        report_dispatches.action_gather()
        for expected_note in expected_notes:
            self.assertIn(expected_note, report_dispatches.note)
        report_dispatches.generate_declaration()
        self.assertEqual(len(report_dispatches.declaration_line_ids), 0)
        # Change data to remove some notes and create lines
        self.product.origin_country_id = self.env.ref("base.fr")
        self.partner_1.vat = "FR23334175221"
        self.partner_2.vat = "FR23334175221"
        report_dispatches.action_gather()
        report_dispatches.generate_declaration()
        total_expected_invoices = len(expected_invoices) / 2
        self.assertEqual(
            len(report_dispatches.declaration_line_ids), total_expected_invoices
        )
        for expected_note in expected_notes:
            self.assertNotIn(expected_note, report_dispatches.note)

    def test_report_creation_arrivals(self):
        # Generate report
        report_arrivals = self._create_declaration("arrivals")
        report_arrivals.action_gather()
        self._check_move_lines_present(
            self.invoices["arrivals"]["invoices"], report_arrivals.computation_line_ids
        )
        report_arrivals.generate_declaration()
        self.assertEqual(
            len(report_arrivals.declaration_line_ids), 2
        )  # One line for each country
        self.assertEqual(
            report_arrivals.declaration_line_ids.mapped("hs_code_id"),
            self.hs_code,
        )
        self._check_declaration_lines(
            report_arrivals.declaration_line_ids,
            self.invoices["arrivals"][self.partner_1.country_id],
            self.invoices["arrivals"][self.partner_2.country_id],
        )
        csv_result = report_arrivals._generate_csv()
        csv_lines = csv_result.decode("utf-8").rstrip().splitlines()
        self.assertEqual(len(csv_lines), 2)
        for line in csv_lines:
            items = line.split(";")
            self.assertTrue(items[0] in ("PT", "FR"))
            self.assertEqual(items[6], self.hs_code.local_code)
