# Copyright 2021 Tecnativa - João Marques
# Copyright 2023 Tecnativa - Víctor Martínez

from datetime import datetime

from odoo import _
from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT

from ..hooks import post_init_hook


@tagged("post_install", "-at_install")
class TestL10nIntraStatReport(AccountTestInvoicingCommon):
    @classmethod
    def _create_invoice_for_intrastat(cls, inv_type, partner, fiscal_pos, product=None):
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
        partner_shipping = partner.child_ids.filtered(lambda x: x.type == "delivery")
        if inv_type in ["out_invoice", "out_refund", "out_receipt"]:
            move_form.partner_shipping_id = (
                partner_shipping if partner_shipping else partner
            )
        move_form.fiscal_position_id = fiscal_pos
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
        return cls.env["intrastat.product.declaration"].create(
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
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        # Set current company to Spanish
        intrastat_transport = cls.env["intrastat.transport_mode"].search([], limit=1)
        cls.env.user.company_id.write(
            {
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_a").id,
                "incoterm_id": cls.env.ref("account.incoterm_FCA").id,
                "intrastat_transport_id": intrastat_transport.id,
                "vat": "ESA12345674",
            }
        )
        cls.env.user.groups_id += cls.env.ref("account.group_delivery_invoice_address")
        cls.fiscal_position_b2b = cls.env["account.fiscal.position"].create(
            {
                "name": "B2B FP",
                "company_id": cls.env.company.id,
                "intrastat": "b2b",
                "vat_required": True,
            }
        )
        cls.fiscal_position_b2c = cls.env["account.fiscal.position"].create(
            {
                "name": "B2C FP",
                "company_id": cls.env.company.id,
                "intrastat": "b2c",
                "vat_required": False,
            }
        )
        # Create Intrastat partners
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Test Partner FR", "country_id": cls.env.ref("base.fr").id}
        )
        cls.env["res.partner"].create(
            {
                "name": "Test Partner FR",
                "country_id": cls.env.ref("base.fr").id,
                "parent_id": cls.partner_1.id,
                "type": "delivery",
            }
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
            for partner, fiscal in zip(
                (cls.partner_1, cls.partner_2),
                (cls.fiscal_position_b2b, cls.fiscal_position_b2c),
            ):
                invoice = cls._create_invoice_for_intrastat(inv_type, partner, fiscal)
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
            if line.src_dest_country_code == self.env.ref("base.fr").code:
                self.assertEqual(line.suppl_unit_qty, fr_qty)
            if line.src_dest_country_code == self.env.ref("base.pt").code:
                self.assertEqual(line.suppl_unit_qty, pt_qty)
            self.assertTrue(line.intrastat_state_id)
            self.assertTrue(line.incoterm_id)
            if line.declaration_type == "dispatches":
                self.assertTrue(line.partner_vat)

    def test_report_creation_dispatches(self):
        # Generate report
        report_dispatches = self._create_declaration("dispatches")
        report_dispatches.action_gather()
        self._check_move_lines_present(
            self.invoices["dispatches"]["invoices"],
            report_dispatches.computation_line_ids,
        )
        report_dispatches.draft2confirmed()
        report_dispatches.confirmed2done()
        self.assertEqual(report_dispatches.state, "done")
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

    # TODO: Remove if a test is added in intrastat_product to test it
    def test_report_creation_dispatches_notes_and_lines(self):
        # Generate report
        self.product.origin_country_id = False
        report_dispatches = self._create_declaration("dispatches")
        expected_invoices = self.invoices["dispatches"]["invoices"]
        expected_notes = [
            _("Missing <em>Country of Origin</em> <small>"),
            _("Missing <em>VAT Number</em> <small>"),
        ]
        report_dispatches.action_gather()
        for expected_note in expected_notes:
            self.assertIn(expected_note, report_dispatches.note)
        # # Change data to remove some notes and create lines
        self.product.origin_country_id = self.env.ref("base.fr")
        self.partner_1.vat = "FR23334175221"
        self.partner_2.vat = "FR23334175221"
        report_dispatches.action_gather()
        report_dispatches.draft2confirmed()
        report_dispatches.confirmed2done()
        self.assertEqual(report_dispatches.state, "done")
        self.assertEqual(
            len(report_dispatches.declaration_line_ids), len(expected_invoices) / 2
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
        report_arrivals.draft2confirmed()
        report_arrivals.confirmed2done()
        self.assertEqual(report_arrivals.state, "done")
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
