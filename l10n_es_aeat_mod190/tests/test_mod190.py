# Copyright 2019 Creu Blanca
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.exceptions import UserError
from odoo.tests.common import Form

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.190")


class TestL10nEsAeatMod190Base(TestL10nEsAeatModBase):
    debug = False
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IRPF19": (100, -19),
        "P_IRPF20": (1000, -200),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.supplier.write(
            {
                "incluir_190": True,
                "aeat_perception_key_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_key_01"
                ).id,
                "a_nacimiento": "2000",
            }
        )
        cls.customer.write(
            {
                "incluir_190": True,
                "aeat_perception_key_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_key_07"
                ).id,
                "aeat_perception_subkey_id": cls.env.ref(
                    "l10n_es_aeat_mod190.aeat_m190_perception_subkey_08_01"
                ).id,
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
                    "l10n_es_aeat_mod190.aeat_m190_perception_subkey_08_02"
                ).id,
            }
        )

    def test_mod190(self):
        self._invoice_purchase_create("2017-01-01")
        self._invoice_purchase_create("2017-01-02")
        model190 = self.env["l10n.es.aeat.mod190.report"].create(
            {
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2017,
                "date_start": "2017-01-01",
                "date_end": "2017-12-31",
            }
        )
        self.assertEqual(model190.company_id.id, self.company.id)
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
        self.assertTrue(model190.partner_record_ids)
        supplier_record = model190.partner_record_ids.filtered(
            lambda r: r.partner_id == self.supplier
        )
        self.assertEqual(supplier_record.percepciones_dinerarias, 2200)
        self.assertEqual(supplier_record.retenciones_dinerarias, 438)
        self.assertEqual(2, supplier_record.ad_required)
        self.assertEqual(2, self.supplier.ad_required)
        self.customer.write(
            {
                "vat": "ESC2259530J",
                "country_id": self.browse_ref("base.es").id,
                "state_id": self.browse_ref("base.state_es_bi").id,
            }
        )
        self.assertNotIn(
            self.customer, model190.mapped("partner_record_ids.partner_id")
        )
        records = model190.partner_record_ids
        model190_form = Form(model190)
        with model190_form.partner_record_ids.new() as record:
            record.partner_id = self.customer
        model190_form.save()
        record_new = model190.partner_record_ids - records
        self.assertEqual(record_new.partner_vat, "C2259530J")
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
        # Definimos la posición fiscal (se hará con _onchange_partner_id por UX)
        second_invoice.fiscal_position_id = self.fiscal_position
        self.assertTrue(second_invoice.aeat_perception_key_id)
        model190 = self.env["l10n.es.aeat.mod190.report"].create(
            {
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2017,
                "date_start": "2017-01-01",
                "date_end": "2017-12-31",
            }
        )
        self.assertEqual(model190.company_id.id, self.company.id)
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
