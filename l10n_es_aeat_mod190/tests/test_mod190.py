# Copyright 2019 Creu Blanca
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from typing import ClassVar

from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tests import Form, new_test_user

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.190")


class TestL10nEsAeatMod190Base(TestL10nEsAeatModBase):
    debug = False
    taxes_purchase: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "P_IRPF19": (100, -19),
        "P_IRPF20": (1000, -200),
        "P_IRPF24": (100, -24),
        "S_GD0": (100, 0),
        "P_IRPF21TD": (2000, -15),
        "P_IRPF21TDIT": (1500, -15),
    }

    # The tests run as the BaseCommon test user: an AEAT user who may see the
    # sensitive data of the perceptors
    _test_user_groups = (
        *TestL10nEsAeatModBase._test_user_groups,
        "l10n_es_aeat_mod190.group_aeat_mod190",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier.write(
            {
                "incluir_190": True,
                "aeat_perception_key_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_key_01"
                ).id,
                "a_nacimiento": "2000",
                "discapacidad": "1",
            }
        )
        cls.customer.write(
            {
                "incluir_190": True,
                "aeat_perception_key_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_key_07"
                ).id,
                "aeat_perception_subkey_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_subkey_07_01"
                ).id,
                "vat": "ESA12345674",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_bi").id,
            }
        )
        cls.fiscal_position = cls.env["account.fiscal.position"].create(
            {
                "company_id": cls.company.id,
                "name": "Testing Fiscal position",
                "aeat_perception_key_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_key_07"
                ).id,
                "aeat_perception_subkey_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_subkey_07_02"
                ).id,
            }
        )

    def _complete_perceptor(self, partner):
        partner.write(
            {
                "vat": "ESC2259530J",
                "country_id": self.browse_ref("base.es").id,
                "state_id": self.browse_ref("base.state_es_bi").id,
            }
        )

    def _create_purchase_move(self, partner, date, lines, move_type="in_invoice"):
        """Supplier invoice or refund entered from its form, with one line for
        each (tax code, price) pair, and posted."""
        move_form = Form(
            self.env["account.move"]
            .with_user(self.billing_user)
            .with_context(default_move_type=move_type)
        )
        move_form.partner_id = partner
        move_form.invoice_date = date
        for tax_code, price in lines:
            with move_form.invoice_line_ids.new() as line_form:
                line_form.name = f"Test for tax {tax_code}"
                line_form.price_unit = price
                line_form.tax_ids.clear()
                line_form.tax_ids.add(self._get_taxes(tax_code))
        move = move_form.save()
        move.action_post()
        return move

    def _create_report(self, year, name="1900000000001"):
        return self.env["l10n.es.aeat.mod190.report"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": year,
                "date_start": f"{year}-01-01",
                "date_end": f"{year}-12-31",
            }
        )

    def _export_boe(self, report):
        """Records of the BOE file exported from the report form."""
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=report.id, active_model=report._name)
            .create({})
        )
        wizard.action_get_file()
        return wizard.data.content.split(b"\r\n")[:-1]

    def test_mod190(self):
        self._invoice_purchase_create("2017-01-01", {"partner_id": self.supplier.id})
        self._invoice_purchase_create("2017-01-02", {"partner_id": self.customer.id})
        model190 = self.env["l10n.es.aeat.mod190.report"].create(
            {
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2017,
                "date_start": "2017-01-01",
                "date_end": "2017-12-31",
            }
        )
        _logger.debug("Calculate AEAT 190 2017")
        with self.assertRaises(UserError):
            model190.button_calculate()
        self.supplier.write(
            {
                "vat": "ESC2259530J",
                "country_id": self.browse_ref("base.es").id,
                "state_id": self.browse_ref("base.state_es_bi").id,
            }
        )
        model190.button_calculate()
        self.assertEqual(model190.state, "calculated")
        # Fill manual fields
        if self.debug:
            self._print_tax_lines(model190.tax_line_ids)
        supplier_record = model190.partner_record_ids.filtered(
            lambda r: r.partner_id == self.supplier
        )
        self.assertEqual(supplier_record.percepciones_dinerarias, 3200)
        self.assertEqual(supplier_record.retenciones_dinerarias, 543)
        self.assertEqual(supplier_record.percepciones_dinerarias_incap, 1500)
        self.assertEqual(supplier_record.retenciones_dinerarias_incap, 225)
        self.assertEqual(supplier_record.gastos_deducibles, 100)
        self.assertEqual(2, supplier_record.ad_required)
        self.assertEqual(2, self.supplier.ad_required)
        self.customer.write(
            {
                "vat": "ESC2259530J",
                "country_id": self.browse_ref("base.es").id,
                "state_id": self.browse_ref("base.state_es_bi").id,
            }
        )
        customer_record = model190.partner_record_ids.filtered(
            lambda r: r.partner_id == self.customer
        )
        self.assertEqual(customer_record.percepciones_dinerarias, 3200)
        self.assertEqual(customer_record.retenciones_dinerarias, 543)
        self.assertEqual(customer_record.percepciones_dinerarias_incap, 1500)
        self.assertEqual(customer_record.retenciones_dinerarias_incap, 225)
        records = model190.partner_record_ids
        model190_form = Form(model190)
        with model190_form.partner_record_ids.new() as record:
            record.partner_id = self.customer
        model190_form.save()
        record_new = model190.partner_record_ids - records
        self.assertEqual(record_new.partner_vat, "C2259530J")
        # Key and subkey of the perceptor (G.01)
        self.assertEqual(
            record_new.aeat_perception_key_id, self.customer.aeat_perception_key_id
        )
        self.assertEqual(
            record_new.aeat_perception_subkey_id,
            self.customer.aeat_perception_subkey_id,
        )
        model190.write({"registro_manual": True})
        model190.button_recalculate()
        model190.button_confirm()
        self.assertEqual(model190.state, "done")

    def test_mod190_multikeys(self):
        self._invoice_purchase_create("2017-01-01")
        self.supplier.with_company(self.company.id).write(
            {
                "vat": "ESC2259530J",
                "country_id": self.browse_ref("base.es").id,
                "state_id": self.browse_ref("base.state_es_bi").id,
                "property_account_position_id": self.fiscal_position.id,
            }
        )
        second_invoice = self._invoice_purchase_create("2017-01-02")
        # Back to draft to set the fiscal position of the perceptor key G.02
        second_invoice.button_draft()
        with Form(second_invoice.with_user(self.billing_user)) as invoice_form:
            invoice_form.fiscal_position_id = self.fiscal_position
        self.assertEqual(
            second_invoice.aeat_perception_key_id,
            self.fiscal_position.aeat_perception_key_id,
        )
        # Key G has subkeys to choose from, key A has none
        self.assertTrue(second_invoice.is_aeat_perception_subkey_visible)
        self.assertFalse(self.supplier.is_aeat_perception_subkey_visible)
        second_invoice.with_user(self.billing_user).action_post()
        model190 = self.env["l10n.es.aeat.mod190.report"].create(
            {
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2017,
                "date_start": "2017-01-01",
                "date_end": "2017-12-31",
            }
        )
        _logger.debug("Calculate AEAT 190 2017")
        model190.button_calculate()
        # Fill manual fields
        if self.debug:
            self._print_tax_lines(model190.tax_line_ids)
        supplier_record = model190.partner_record_ids.filtered(
            lambda r: r.partner_id == self.supplier
        )
        self.assertEqual(2, len(supplier_record))
        self.assertEqual(1, len(supplier_record.mapped("partner_id")))
        self.assertEqual(2, len(supplier_record.mapped("aeat_perception_key_id")))
        record_with_ad = supplier_record.filtered(lambda r: r.ad_required >= 2)
        self.assertEqual(record_with_ad.a_nacimiento, "2000")
        record_without_ad = supplier_record.filtered(lambda r: r.ad_required < 2)
        self.assertFalse(record_without_ad.a_nacimiento)
        model190.button_confirm()
        self.assertEqual(model190.state, "done")

    def test_aeat_fields_visibility(self):
        """Ensure users without permissions cannot see AEAT fields."""
        # Make sure I can read sensitive data
        self.assertTrue(
            self.env.user.has_group("l10n_es_aeat_mod190.group_aeat_mod190")
        )
        # Create a user without the AEAT group
        user_without_group = new_test_user(
            self.env(user=SUPERUSER_ID),
            "no_190_user",
            "base.group_partner_manager,base.group_user",
        )
        # Attempt to access AEAT fields
        supplier_f = Form(self.supplier)
        supplier_limited_f = Form(self.supplier.with_user(user_without_group))
        fields_to_test = [
            "a_nacimiento",
            "aeat_perception_key_id",
            "aeat_perception_subkey_id",
            "ascendientes",
            "ascendientes_discapacidad_33",
            "ascendientes_discapacidad_66",
            "ascendientes_discapacidad_entero_33",
            "ascendientes_discapacidad_entero_66",
            "ascendientes_discapacidad_entero_mr",
            "ascendientes_discapacidad_mr",
            "ascendientes_entero",
            "ascendientes_entero_m75",
            "ascendientes_m75",
            "ceuta_melilla",
            "computo_primeros_hijos_1",
            "computo_primeros_hijos_2",
            "computo_primeros_hijos_3",
            "contrato_o_relacion",
            "discapacidad",
            "hijos_y_desc_discapacidad_33",
            "hijos_y_desc_discapacidad_66",
            "hijos_y_desc_discapacidad_entero_33",
            "hijos_y_desc_discapacidad_entero_66",
            "hijos_y_desc_discapacidad_entero_mr",
            "hijos_y_desc_discapacidad_mr",
            "hijos_y_descendientes",
            "hijos_y_descendientes_entero",
            "hijos_y_descendientes_m",
            "hijos_y_descendientes_m_entero",
            "movilidad_geografica",
            "nif_conyuge",
            "representante_legal_vat",
            "situacion_familiar",
        ]
        for field in fields_to_test:
            with self.subTest(field=field):
                # User with permissions can read field
                getattr(supplier_f, field)
                with self.assertRaises(AssertionError):
                    # User without permissions can't
                    getattr(supplier_limited_f, field)

    def test_mod190_add_partner_without_tax_lines(self):
        """A perceptor without withholdings added by hand has no amounts."""
        self._complete_perceptor(self.supplier)
        model190 = self._create_report(2017)
        model190.button_calculate()
        self.assertFalse(model190.partner_record_ids)
        model190_form = Form(model190)
        with model190_form.partner_record_ids.new() as record:
            record.partner_id = self.supplier
        model190_form.save()
        partner_record = model190.partner_record_ids
        self.assertEqual(partner_record.partner_id, self.supplier)
        self.assertEqual(
            partner_record.aeat_perception_key_id,
            self.env.ref("l10n_es_aeat_mod190.aeat_m190_perception_key_01"),
        )
        self.assertFalse(partner_record.percepciones_dinerarias)
        self.assertFalse(partner_record.retenciones_dinerarias)

    def test_mod190_manual_records(self):
        """With "Manual records", recalculating keeps the perceptor records
        the user added or edited by hand, refreshes their amounts from the
        accounting and totals the boxes from them."""
        self._complete_perceptor(self.supplier)
        self._create_purchase_move(self.supplier, "2025-01-10", [("P_IRPF21T", 1000)])
        model190 = self._create_report(2025)
        model190.button_calculate()
        supplier_record = model190.partner_record_ids
        self.assertEqual(supplier_record.partner_id, self.supplier)
        # The user keeps the records by hand: edits the calculated one and
        # adds a perceptor without invoices
        with Form(model190) as model190_form:
            model190_form.registro_manual = True
            with model190_form.partner_record_ids.edit(0) as record_form:
                record_form.reduccion_aplicable = 2000
            with model190_form.partner_record_ids.new() as record_form:
                record_form.partner_id = self.customer
        records = model190.partner_record_ids
        customer_record = records - supplier_record
        self.assertEqual(customer_record.partner_id, self.customer)
        self._create_purchase_move(self.supplier, "2025-02-10", [("P_IRPF21T", 500)])
        model190.button_recalculate()
        self.assertEqual(model190.partner_record_ids, records)
        self.assertEqual(supplier_record.reduccion_aplicable, 2000)
        self.assertEqual(supplier_record.percepciones_dinerarias, 1500)
        self.assertEqual(supplier_record.retenciones_dinerarias, 225)
        self.assertEqual(
            customer_record.aeat_perception_subkey_id,
            self.customer.aeat_perception_subkey_id,
        )
        self.assertFalse(customer_record.percepciones_dinerarias)
        self.assertEqual(model190.casilla_01, 2)
        self.assertEqual(model190.casilla_02, 1500)
        self.assertEqual(model190.casilla_03, 225)
        model190.button_confirm()
        self.assertEqual(model190.state, "done")

    def test_mod190_export_boe(self):
        """The BOE file of the 2025 record design, from the report form."""
        for partner in self.supplier | self.customer:
            partner.write(
                {
                    "vat": "ESC2259530J",
                    "country_id": self.browse_ref("base.es").id,
                    "state_id": self.browse_ref("base.state_es_bi").id,
                }
            )
        self.supplier.name = "Perceptor Uno"
        self.customer.name = "Perceptor Dos"
        self._invoice_purchase_create("2025-01-01", {"partner_id": self.supplier.id})
        self._invoice_purchase_create("2025-01-02", {"partner_id": self.customer.id})
        model190 = self.env["l10n.es.aeat.mod190.report"].create(
            {
                "name": "1900000000001",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "contact_email": "owner@example.com",
                "year": 2025,
                "date_start": "2025-01-01",
                "date_end": "2025-12-31",
            }
        )
        model190.button_calculate()
        self.assertEqual(
            model190.export_config_id,
            self.env.ref("l10n_es_aeat_mod190.aeat_mod190_2025_main_export_config"),
        )
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=model190.id, active_model=model190._name)
            .create({})
        )
        wizard.action_get_file()
        content = wizard.data.content
        # One declarant record and one record per perceptor and key, 500
        # characters each, as the 2025 record design (DR190) describes them
        expected = [
            (
                b"11902025123456789SPANISH TEST COMPANY                    T91"
                b"1234455TEST OWNER                              1900000000001"
                b"  0000000000000000000002 000000000940000000000000153600OWNER"
                b"@EXAMPLE.COM                                                "
                b"                                                            "
                b"                                                            "
                b"                                                            "
                b"                                                            "
                b"                    "
            ),
            (
                b"21902025123456789C2259530J         PERCEPTOR DOS            "
                b"               48G01 00000003200000000000054300 000000000000"
                b"0000000000000000000000000000000000000         00000000000000"
                b"000000000001000000000000000000000000000000000000000000000000"
                b"00000000000000 00000001500000000000022500 000000000000000000"
                b"000000000000000000000000000000000000000000000000000000000000"
                b"0000000000000000000000000000000000                          "
                b"                                                            "
                b"                    "
            ),
            (
                b"21902025123456789C2259530J         PERCEPTOR UNO            "
                b"               48A00 00000003200000000000054300 000000000000"
                b"0000000000000000000000000000000020000         10000000000000"
                b"000000000001000000000000000000000000000000000000000000000000"
                b"00000000000000 00000001500000000000022500 000000000000000000"
                b"000000000000000000000000000000000000000000000000000000000000"
                b"0000000000000000000000000000000000                          "
                b"                                                            "
                b"                    "
            ),
        ]
        self.assertEqual(content, b"".join(record + b"\r\n" for record in expected))

    def test_mod190_export_boe_sign(self):
        """The total of box [02] is signed only when it is negative: a space
        while it is positive and "N" once a refund larger than the invoice
        makes it negative (DR190, type 1 record, position 145). The total of
        box [03] (positions 161-175) has no sign, as the withholdings of the
        perceptor records (95-107), in the 2017-2024 and 2025 designs."""
        for year in (2024, 2025):
            with self.subTest(year=year):
                self._create_purchase_move(
                    self.customer, f"{year}-01-10", [("P_IRPF15", 100)]
                )
                model190 = self._create_report(year, name=f"190000{year}001")
                model190.button_calculate()
                declarant, perceptor = self._export_boe(model190)
                self.assertEqual(declarant[144:160], b" 000000000010000")
                self.assertEqual(declarant[160:175], b"000000000001500")
                self.assertEqual(perceptor[80:94], b" 0000000010000")
                self.assertEqual(perceptor[94:107], b"0000000001500")
                self._create_purchase_move(
                    self.customer,
                    f"{year}-02-10",
                    [("P_IRPF15", 300)],
                    move_type="in_refund",
                )
                model190.button_recalculate()
                declarant, perceptor = self._export_boe(model190)
                self.assertEqual(len(declarant), 500)
                self.assertEqual(declarant[144:160], b"N000000000020000")
                self.assertEqual(declarant[160:175], b"000000000003000")
                self.assertEqual(perceptor[80:94], b"N0000000020000")
                self.assertEqual(perceptor[94:107], b"0000000003000")

    def test_mod190_export_boe_disability(self):
        """The disability degree of a perceptor is personal data of the
        record: its salary stays a perception not derived from work incapacity
        (positions 82-107), and the work incapacity fields (255-281) stay
        empty."""
        self._complete_perceptor(self.supplier)
        self._create_purchase_move(self.supplier, "2025-01-10", [("P_IRPF21T", 1000)])
        model190 = self._create_report(2025)
        model190.button_calculate()
        self.assertEqual(model190.partner_record_ids.discapacidad, "1")
        _declarant, perceptor = self._export_boe(model190)
        self.assertEqual(perceptor[80:107], b" 00000001000000000000015000")
        self.assertEqual(perceptor[254:281], b" " + b"0" * 26)

    def test_mod190_export_boe_in_kind(self):
        """An in-kind perception is declared once, as not derived from work
        incapacity (positions 108-134), and the in-kind work incapacity fields
        (282-295) stay empty. The total of box [02] matches the records."""
        self._complete_perceptor(self.supplier)
        self._create_purchase_move(
            self.supplier,
            "2025-01-10",
            [("P_IRPF21TE", 1000), ("P_IRPF21TDIT", 500)],
        )
        model190 = self._create_report(2025)
        model190.button_calculate()
        declarant, perceptor = self._export_boe(model190)
        self.assertEqual(declarant[144:160], b" 000000000150000")
        self.assertEqual(perceptor[107:134], b" 00000001000000000000015000")
        self.assertEqual(perceptor[254:281], b" 00000000500000000000007500")
        self.assertEqual(perceptor[281:295], b" " + b"0" * 13)

    def test_mod190_readonly_user_opens_invoice(self):
        """An Accounting / Read-only user who manages the AEAT declarations
        opens a vendor bill that carries a perception key, and its journal
        item."""
        self.supplier.with_company(
            self.company
        ).property_account_position_id = self.fiscal_position
        invoice = self._create_purchase_move(
            self.supplier, "2025-01-10", [("P_IRPF15", 100)]
        )
        self.assertTrue(invoice.aeat_perception_key_id)
        readonly_user = new_test_user(
            self.env(user=SUPERUSER_ID),
            "readonly_190_user",
            "account.group_account_readonly,l10n_es_aeat.group_account_aeat",
            company_id=self.company.id,
            company_ids=[Command.set(self.company.ids)],
        )
        invoice_form = Form(invoice.with_user(readonly_user))
        self.assertEqual(
            invoice_form.aeat_perception_key_id, invoice.aeat_perception_key_id
        )
        self.assertTrue(invoice_form.is_aeat_perception_subkey_visible)
        line = invoice.invoice_line_ids
        line_form = Form(
            line.with_user(readonly_user), view="account.view_move_line_form"
        )
        self.assertEqual(line_form.aeat_perception_key_id, line.aeat_perception_key_id)

    def test_mod190_export_boe_2017_design(self):
        """A 2024 report is exported with the 2017-2024 record design: records
        of 500 characters and the declarant boxes in their positions."""
        self._create_purchase_move(self.customer, "2024-01-10", [("P_IRPF15", 100)])
        model190 = self._create_report(2024)
        model190.button_calculate()
        self.assertEqual(
            model190.export_config_id,
            self.env.ref("l10n_es_aeat_mod190.aeat_mod190_main_export_config"),
        )
        declarant, perceptor = self._export_boe(model190)
        self.assertEqual(len(declarant), 500)
        self.assertEqual(len(perceptor), 500)
        self.assertEqual(declarant[:17], b"11902024123456789")
        # [01] perceptors (136-144), [02] amount with sign (145-160) and
        # [03] withholdings (161-175)
        self.assertEqual(
            declarant[135:175], b"000000001 000000000010000000000000001500"
        )
        self.assertEqual(perceptor[:17], b"21902024123456789")

    def test_mod190_key_b01(self):
        """A perceptor of key B.01 can't be confirmed until the type of
        benefit is checked on its record."""
        self._complete_perceptor(self.supplier)
        self.supplier.write(
            {
                "aeat_perception_key_id": self.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_key_02"
                ).id,
                "aeat_perception_subkey_id": self.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_subkey_02_01"
                ).id,
            }
        )
        self._create_purchase_move(self.supplier, "2025-01-10", [("P_IRPF21T", 1000)])
        model190 = self._create_report(2025)
        model190.button_calculate()
        record = model190.partner_record_ids
        self.assertTrue(record.visible_key_b01)
        with self.assertRaises(ValidationError):
            model190.button_confirm()
        with Form(record) as record_form:
            record_form.clave_b01_jubilacion = True
        model190.button_confirm()
        self.assertEqual(model190.state, "done")
