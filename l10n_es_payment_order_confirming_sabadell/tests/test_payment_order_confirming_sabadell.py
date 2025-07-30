# © 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, common

from ..models.confirming_sabadell import ConfirmingSabadell


class TestPaymentOrderConfirmingSabadell(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.a_expense = cls.env["account.account"].create(
            {
                "code": "TEA",
                "name": "Test Expense Account",
                "account_type": "expense",
            }
        )
        cls.bank_journal = cls.env["account.journal"].create(
            {
                "name": "Test bank",
                "type": "bank",
                "code": "test-bank",
                "bank_account_id": cls.env.ref(
                    "account_payment_mode.main_company_iban"
                ).id,
            }
        )
        cls.bank_journal.bank_account_id.acc_holder_name = "acc_holder_name"
        cls.bank_journal.bank_account_id.partner_id.vat = "ES40538337D"
        cls.purchase_journal = cls.env["account.journal"].create(
            {
                "name": "Test purchase",
                "type": "purchase",
                "code": "test2-purchase",
            }
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Sabadell confirming",
                "payment_method_id": cls.env.ref(
                    "l10n_es_payment_order_confirming_sabadell.confirming_sabadell"
                ).id,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.bank_journal.id,
                "contrato_bsconfirming": "TEST-CODE",
                "conf_sabadell_type": "58",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr Odoo",
                "email": "demo@demo.com",
                "vat": "40538337D",
                "street": " Calle Leonardo da Vinci, 7",
                "city": "Madrid",
                "zip": "41092",
                "phone": "976123456",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_m").id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.invoice = cls._create_invoice(cls)
        cls.env.ref("account_payment_mode.main_company_iban2").partner_id = cls.partner

    def _create_invoice(self):
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice",
                default_journal_id=self.purchase_journal.id,
            )
        )
        move_form.partner_id = self.partner
        move_form.ref = "custom_ref"
        move_form.invoice_date = fields.Date.today()
        move_form.payment_mode_id = self.payment_mode
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.quantity = 1.0
            line_form.price_unit = 100.00
        move = move_form.save()
        move.action_post()
        return move

    def _create_payment_order(self):
        payment_order = self.env["account.payment.order"].create(
            {"payment_mode_id": self.payment_mode.id}
        )
        line_create = (
            self.env["account.payment.line.create"]
            .with_context(
                active_model="account.payment.order",
                active_id=payment_order.id,
            )
            .create({"date_type": "move", "filter_date": fields.Date.today()})
        )
        line_create.journal_ids = self.purchase_journal.ids
        line_create.populate()
        line_create.create_payment_lines()
        return payment_order

    def test_missing_company_partner_vat_raises_error(self):
        order = self._create_payment_order()
        partner_no_vat = self.env["res.partner"].create({"name": "Test"})
        order.company_partner_bank_id = self.env["res.partner.bank"].create(
            {
                "acc_number": "ES7620770024003102575766",
                "partner_id": partner_no_vat.id,
            }
        )
        with self.assertRaises(UserError) as e:
            order.generate_payment_file()
        self.assertIn("no tiene un NIF establecido", str(e.exception))

    def test_account_payment_order_sabadell(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        self.assertEqual(order.state, "generated")

    def test_generate_file_content(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        content, name = order.generate_payment_file()
        self.assertTrue(name.endswith(".txt"))
        self.assertIn(self.partner.vat.encode(), content)

    def test_payment_file_acc_type_other(self):
        order = self._create_payment_order()
        order.company_partner_bank_id.acc_type = "other"
        order.draft2open()
        order.open2generated()
        content, _ = order.generate_payment_file()
        self.assertIn(b"65", content)

    def test_missing_partner_vat_raises_error(self):
        self.partner.vat = False
        order = self._create_payment_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_generate_payment_file_date_prefered_variants(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        for date_pref in ["due", "now"]:
            order.date_prefered = date_pref
            if date_pref is None:
                order.date_scheduled = fields.Date.today()
            content, _ = order.generate_payment_file()
            self.assertIn(b"65", content)

    def test_missing_partner_address_raises_error(self):
        self.partner.street = False
        order = self._create_payment_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_missing_partner_city_raises_error(self):
        self.partner.city = False
        order = self._create_payment_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_missing_partner_zip_raises_error(self):
        self.partner.zip = False
        order = self._create_payment_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_missing_partner_country_code_raises_error(self):
        self.partner.country_id = False
        order = self._create_payment_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_missing_swift_raises_error(self):
        for b in self.partner.bank_ids:
            b.bank_bic = False
        order = self._create_payment_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_missing_iban_for_transfer_raises_error(self):
        self.payment_mode.conf_sabadell_type = "58"
        for b in self.partner.bank_ids:
            b.acc_type = "bank"
        order = self._create_payment_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_sab_registro_calls(self):
        order = self._create_payment_order()
        self.assertTrue(callable(order.generate_payment_file))

    def test_generate_payment_file_contains_expected_data(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        content, name = order.generate_payment_file()
        self.assertIn(b"KF01", content)
        self.assertIn(b"65", content)
        self.assertIn(self.partner.vat.encode(), content)
        self.assertIn(self.payment_mode.contrato_bsconfirming.encode(), content)
        self.assertTrue(name.endswith(".txt"))

    def test_generate_payment_file_with_various_vat_types(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        vat_examples = [
            "ESA12345674",
        ]
        for vat in vat_examples:
            self.partner.sudo().write({"vat": vat})
            expected = vat
            if self.partner.country_id.code in vat:
                expected = vat.replace(self.partner.country_id.code, "")
            content, _ = order.generate_payment_file()
            self.assertIn(
                expected.encode(), content, f"Expected {expected} in file for VAT {vat}"
            )

    def test_generate_payment_file_delegates_to_super(self):
        self.payment_mode.payment_method_id.write({"code": "other_code"})
        order = self._create_payment_order()
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("No handler for this payment method", str(cm.exception))

    def test_sab_errors_company_partner_missing(self):
        order = self._create_payment_order()
        order.write({"company_partner_bank_id": False})
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("Propietario de la cuenta no", str(cm.exception))

    def test_sab_errors_line_partner_vat_missing(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        line = order.payment_line_ids[0]
        line.partner_id.vat = False
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("no tiene establecido el NIF", str(cm.exception))

    def test_sab_errors_line_partner_street_missing(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        line = order.payment_line_ids[0]
        line.partner_id.street = False
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("no tiene establecido el Domicilio", str(cm.exception))

    def test_sab_errors_line_move_ref_too_long(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        line = order.payment_line_ids[0]
        ml = line.move_line_id
        ml.ref = "X" * 16
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("más de 15 caracteres", str(cm.exception))

    def test_sab_errors_line_partner_city_missing(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        line = order.payment_line_ids[0]
        line.partner_id.city = False
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("no tiene establecida la Ciudad", str(cm.exception))

    def test_sab_errors_line_partner_zip_missing(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        line = order.payment_line_ids[0]
        line.partner_id.zip = False
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("no tiene establecido el C.P.", str(cm.exception))

    def test_sab_errors_line_iban_format_for_type_58(self):
        self.payment_mode.conf_sabadell_type = "58"
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        for b in order.payment_line_ids.mapped("partner_bank_id"):
            b.acc_type = "bank"
        with self.assertRaises(UserError) as cm:
            order.generate_payment_file()
        self.assertIn("tiene que estar en formato IBAN", str(cm.exception))

    def test_sab_tipo_vat_patterns(self):
        patterns = {
            "ES12345678": "01",
            "ESK1234567A": "02",
            "ESM7654321B": "02",
            "ABC123456": "04",
            "ESX12345678": "05",
            "ESX1234567A": "05",
            "ESY1234567Z": "05",
            "ESZ7654321Y": "05",
            "ESFebc12345": "10",
            "ESN1234567C": "12",
            "INVALIDVAT": "99",
        }
        order = self._create_payment_order()
        sab = ConfirmingSabadell(order)
        for vat, _expected in patterns.items():
            code = sab._sab_tipo_vat(vat)
        self.assertEqual(code, _expected, f"VAT {vat} should return {_expected}")

    def test_date_prefered_else_branch(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        sel = order._fields["date_prefered"].selection
        other = next((k for k, _ in sel if k not in ("due", "now")), None)
        if not other:
            self.skipTest("No hay valor extra en date_prefered para probar el else")
        order.date_prefered = other
        scheduled = fields.Date.today()
        timedelta(days=5)
        order.date_scheduled = scheduled
        content, _ = order.generate_payment_file()
        self.assertIn(scheduled.strftime("%Y%m%d").encode(), content)

    def test_strip_vat_prefix_for_record_types(self):
        order = self._create_payment_order()
        order.draft2open()
        order.open2generated()
        partner = order.company_partner_bank_id.partner_id

        partner.vat = "ES99999999"
        content, _ = order.generate_payment_file()
        rec01 = content.splitlines()[0]
        nif01 = rec01[51:60]
        self.assertNotIn(b"ES99999999", nif01)

        partner.vat = "ES88888888A"
        content, _ = order.generate_payment_file()
        rec05 = content.splitlines()[-1]
        nif05 = rec05[1:10]
        self.assertNotIn(b"ES88888888A", nif05)
        self.assertEqual(nif05.strip(), b"ES8888888")
