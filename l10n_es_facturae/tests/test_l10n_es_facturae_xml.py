# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import importlib.util

from freezegun import freeze_time
from lxml import etree

from odoo.fields import Command
from odoo.tests import Form
from odoo.tools import file_open
from odoo.tools.misc import file_path

from .common import CommonTest


class TestL10nEsFacturaeXml(CommonTest):
    """The whole Facturae 3.2.2 file of an invoice to a public administration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.sudo().write(
            {"name": "Empresa de Prueba", "vat": "ESA12345674", "phone": "926000000"}
        )
        cls.bank.bank_bic = "CAIXESBBXXX"
        cls.administration = cls.env["res.partner"].create(
            {
                "name": "Ayuntamiento de Prueba",
                "street": "Plaza de España, 1",
                "zip": "13700",
                "city": "Tomelloso",
                "state_id": cls.state.id,
                "country_id": cls.env.ref("base.es").id,
                "vat": "ESF35999705",
                "facturae": True,
                "facturae_version": "3_2_2",
                "oficina_contable": "L01130821",
                "organo_gestor": "L01130822",
                "unidad_tramitadora": "L01130823",
            }
        )
        cls.payment_mode_transfer = cls.env["account.payment.mode"].create(
            {
                "name": "Transferencia",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal.id,
                "payment_method_id": cls.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "04",
            }
        )
        tax = cls.company.account_sale_tax_id
        cls.product_box = cls.env["product.product"].create(
            {
                "name": "Caja de cartón",
                "default_code": "CAJA-40",
                "type": "consu",
                "taxes_id": [Command.set(tax.ids)],
            }
        )
        cls.product_service = cls.env["product.product"].create(
            {"name": "Montaje", "type": "service", "taxes_id": [Command.set(tax.ids)]}
        )

    def _create_invoice(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        move_form.partner_id = self.administration
        move_form.invoice_date = "2026-01-15"
        move_form.payment_mode_id = self.payment_mode_transfer
        move_form.narration = "Pedido 77"
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_box
            line_form.quantity = 3
            line_form.price_unit = 25.5
            line_form.discount = 10
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_service
            line_form.price_unit = 100
        move_form.facturae_file_reference = "EXP-2026-15"
        move_form.facturae_receiver_contract_reference = "CTR-2026-01"
        move_form.facturae_receiver_transaction_reference = "PED-77"
        invoice = move_form.save()
        # References of the first line, as entered with its Facturae button
        line = invoice.invoice_line_ids[0]
        with Form.from_action(self.env, line.button_edit_facturae_fields()) as form:
            form.facturae_file_reference = "EXP-2026-15-1"
            form.facturae_receiver_contract_reference = "CTR-2026-01-1"
            form.facturae_receiver_transaction_reference = "PED-77-1"
            form.facturae_issuer_contract_reference = "VTA-2026-01"
            form.facturae_issuer_transaction_reference = "ALB-2026-77"
        invoice.action_post()
        invoice.name = "2026/00001"
        return invoice

    def _export_facturae(self, invoice):
        wizard_form = Form(
            self.env["create.facturae"].with_context(
                active_ids=invoice.ids, active_model="account.move"
            )
        )
        wizard_form.firmar_facturae = False
        wizard = wizard_form.save()
        wizard.create_facturae_file()
        return wizard.facturae.content

    @freeze_time("2026-01-15")
    def test_facturae_322_xml(self):
        invoice = self._create_invoice()
        content = self._export_facturae(invoice)
        with file_open(
            "l10n_es_facturae/data/Facturaev3_2_2.xsd", mode="rb"
        ) as schema_file:
            schema = etree.XMLSchema(etree.parse(schema_file))
        schema.assertValid(etree.fromstring(content))
        with file_open(
            "l10n_es_facturae/tests/data/facturae_322.xml", mode="rb"
        ) as expected_file:
            expected = etree.parse(
                expected_file, etree.XMLParser(remove_blank_text=True)
            ).getroot()
        self.assertEqual(
            etree.tostring(etree.fromstring(content), pretty_print=True).decode(),
            etree.tostring(expected, pretty_print=True).decode(),
        )

    def test_migration_fills_missing_codes(self):
        """The migration to 20.0 gives a code to the chart taxes without one and
        keeps the codes already set"""
        chart = self.env["account.chart.template"].with_company(self.company)
        tax_0 = chart.ref("account_tax_template_s_iva0b")
        tax_21 = chart.ref("account_tax_template_s_iva21b")
        (tax_0 | tax_21).sudo().facturae_code = False
        tax_irpf = chart.ref("account_tax_template_s_irpf24_rdc")
        tax_irpf.sudo().facturae_code = "05"
        script = file_path("l10n_es_facturae/migrations/20.0.1.0.0/post-migration.py")
        spec = importlib.util.spec_from_file_location("post_migration", script)
        post_migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(post_migration)
        # Without the frame of the Odoo migration manager that its decorator
        # inspects, and as superuser like the decorator
        post_migration.migrate.__wrapped__(self.env(su=True), "19.0.1.0.0")
        self.env.invalidate_all()
        self.assertEqual(tax_0.facturae_code, "01")
        self.assertEqual(tax_21.facturae_code, "01")
        self.assertEqual(tax_irpf.facturae_code, "05")
