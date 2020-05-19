# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from openerp import exceptions
from openerp.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsAeatMod115Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IRPF19A": (1000, 190),
        "P_IRPF195A": (2000, 390),
        "P_IRPF20A": (3000, 600),
        "P_IRPF21A": (4000, 840),
    }
    taxes_result = {
        # Base retenciones e ingresos a cuenta
        "2": (
            (2 * 1000)
            + (2 * 2000)
            + (2 * 3000)  # P_IRPF19A, P_IRPF195A
            + (2 * 4000)  # P_IRPF20A, P_IRPF21A
        ),
        # Retenciones e ingresos a cuenta
        "3": (
            (2 * 190)
            + (2 * 390)
            + (2 * 600)  # P_IRPF19A, P_IRPF195A
            + (2 * 840)  # P_IRPF20A, P_IRPF21A
        ),
    }

    @classmethod
    def _create_model_115(cls):
        export_config = cls.env.ref(
            "l10n_es_aeat_mod115.aeat_mod115_main_export_config"
        )
        return cls.env["l10n.es.aeat.mod115.report"].create(
            {
                "name": "9990000000115",
                "company_id": cls.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2015,
                "period_type": "1T",
                "date_start": "2015-01-01",
                "date_end": "2015-03-31",
                "export_config_id": export_config.id,
                "journal_id": cls.journal_misc.id,
                "counterpart_account_id": cls.accounts["475000"].id,
            }
        )

    def test_model_115(self):
        # Purchase invoices
        self._invoice_purchase_create("2015-01-01")
        self._invoice_purchase_create("2015-01-02")
        purchase = self._invoice_purchase_create("2015-01-03")
        self._invoice_refund(purchase, "2015-01-18")
        self.model115 = self._create_model_115()
        self.model115.button_calculate()
        self.assertEqual(self.model115.tipo_declaracion, "I")
        self.assertEqual(self.model115.tipo_declaracion_positiva, "I")
        self.assertFalse(self.model115.tipo_declaracion_negativa)
        with self.assertRaises(exceptions.ValidationError):
            self.model115.tipo_declaracion = "N"
        # Fill manual fields
        self.model115.write(
            {
                # Resultados a ingresar anteriores
                "casilla_04": 145,
                "tipo_declaracion_positiva": "U",
            }
        )
        # Check tax lines
        for box, result in self.taxes_result.items():
            lines = self.model115.tax_line_ids.filtered(
                lambda x: x.field_number == int(box)
            )
            self.assertEqual(round(sum(lines.mapped("amount")), 2), round(result, 2))
        # Check result
        retenciones = self.taxes_result.get("3", 0.0)
        result = retenciones - 145
        self.assertEqual(self.model115.casilla_01, 1)
        self.assertEqual(round(self.model115.casilla_03, 2), round(retenciones, 2))
        self.assertEqual(round(self.model115.casilla_05, 2), round(result, 2))
        with self.assertRaises(exceptions.UserError):
            self.model115.button_confirm()
        self.model115.partner_bank_id = self.customer_bank.id
        self.model115.button_confirm()

    def test_negative_model_115(self):
        # Make the invoice in a different period for having negative result
        purchase = self._invoice_purchase_create("2014-01-01")
        self._invoice_refund(purchase, "2015-01-18")
        self.model115 = self._create_model_115()
        self.model115.button_calculate()
        self.assertEqual(self.model115.tipo_declaracion, "N")
        self.assertEqual(self.model115.tipo_declaracion_negativa, "N")
        self.assertFalse(self.model115.tipo_declaracion_positiva)
        with self.assertRaises(exceptions.ValidationError):
            self.model115.tipo_declaracion = "I"
        # this doesn't rise any error
        self.model115.tipo_declaracion_negativa = "N"
