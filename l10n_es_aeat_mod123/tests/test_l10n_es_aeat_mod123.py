# Copyright 2017 Creu Blanca
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging
from typing import ClassVar

from odoo.fields import Command
from odoo.tests import Form

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.123")


class TestL10nEsAeatMod123(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "P_RP19": (100, -19),
        "l10n_es.account_tax_template_p_rrD19": (1000, -190),
    }
    taxes_result: ClassVar[dict] = {"2": 3 * (100 + 1000), "3": 3 * (19 + 190)}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier2 = cls.supplier.copy({"name": "Test supplier 2"})
        # The view the menu action opens
        cls.form_view = "l10n_es_aeat_mod123.view_l10n_es_aeat_mod123_report_form"

    def _purchase_invoice(self, date, partner, lines):
        """Post a vendor bill of the partner with one line per (tax, price)."""
        return self._invoice_purchase_create(
            date,
            extra_vals={
                "partner_id": partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": f"Test for tax {tax}",
                            "account_id": self.accounts["600000"].id,
                            "price_unit": price,
                            "quantity": 1,
                            "tax_ids": [Command.set(self._get_taxes(tax).ids)],
                        }
                    )
                    for tax, price in lines
                ],
            },
        )

    def _create_report(self, year, **values):
        """Fill in the report form as the user does and press 'Calculate'."""
        with Form(
            self.env["l10n.es.aeat.mod123.report"], view=self.form_view
        ) as report_form:
            report_form.company_vat = "123456789"
            report_form.contact_name = "Test owner"
            report_form.contact_phone = "911234455"
            report_form.year = year
            report_form.period_type = "1T"
            report_form.tipo_declaracion = "I"
            for field, value in values.items():
                setattr(report_form, field, value)
        report = report_form.record
        _logger.debug("Calculate AEAT 123 1T %s", year)
        report.button_calculate()
        if self.debug:
            self._print_tax_lines(report.tax_line_ids)
        return report

    def _export_boe(self, report):
        """Export the report through its 'Export to BOE' button."""
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=report.id, active_model=report._name)
            .create({})
        )
        wizard.action_get_file()
        return wizard.data.content.decode("iso-8859-1")

    def _check_tax_lines(self, report, taxes_result):
        for box, result in taxes_result.items():
            _logger.debug(f"Checking tax line: {box}")
            lines = report.tax_line_ids.filtered(
                lambda x, box=box: x.field_number == int(box)
            )
            self.assertAlmostEqual(sum(lines.mapped("amount")), result, 2)

    def test_model_123_before_2024(self):
        self._invoice_purchase_create("2017-01-01")
        self._invoice_purchase_create("2017-01-02")
        self._invoice_purchase_create("2017-01-03")
        model123 = self._create_report(2017)
        self._check_tax_lines(model123, self.taxes_result)
        self.assertEqual(model123.casilla_01, 1)
        self.assertEqual(model123.casilla_08, 627.0)
        self.assertEqual(model123.amount_result, 627.0)

    def test_model_123_2024(self):
        # Dividends and the other incomes of capital of the first supplier, and
        # interests of a second supplier, so that each box gets its own amount
        self._purchase_invoice(
            "2024-01-10",
            self.supplier,
            [
                ("l10n_es.account_tax_template_p_rrD19", 1000),
                ("account_tax_template_p_irpf24_rdc", 500),
                ("account_tax_template_p_irpf19cs", 2000),
            ],
        )
        self._purchase_invoice(
            "2024-02-10", self.supplier2, [("account_tax_template_p_rp19", 100)]
        )
        bank = self.env["res.partner.bank"].create(
            {
                "partner_id": self.company.partner_id.id,
                "account_number": "ES91 2100 0418 4502 0005 1332",
            }
        )
        model123 = self._create_report(
            2024,
            tipo_declaracion="U",
            partner_bank_id=bank,
            statement_type="C",
            previous_number="1230000000001",
        )
        self.assertEqual(
            model123.export_config_id,
            self.env.ref("l10n_es_aeat_mod123.aeat_mod123_2024_main_export_config"),
        )
        self._check_tax_lines(
            model123,
            {"4": 1000 + 500, "5": 2000 + 100, "7": 190 + 120, "8": 380 + 19},
        )
        _logger.debug("Checking results")
        self.assertEqual(model123.casilla_01_2024, 1)
        self.assertEqual(model123.casilla_02_2024, 2)
        self.assertEqual(model123.casilla_03_2024, 3)
        self.assertEqual(model123.casilla_04_2024, 1500.0)
        self.assertEqual(model123.casilla_05_2024, 2100.0)
        self.assertEqual(model123.casilla_06_2024, 3600.0)
        self.assertEqual(model123.casilla_07_2024, 310.0)
        self.assertEqual(model123.casilla_08_2024, 399.0)
        self.assertEqual(model123.casilla_09_2024, 709.0)
        self.assertEqual(model123.casilla_10_2024, 0)
        self.assertEqual(model123.casilla_12_2024, 709.0)
        self.assertEqual(model123.casilla_14_2024, 709.0)
        self.assertEqual(model123.amount_result, 709.0)
        # Boxes the user fills in by hand once calculated
        with Form(model123, view=self.form_view) as report_form:
            report_form.casilla_11_2024 = 180
        self.assertEqual(model123.casilla_12_2024, 889.0)
        self.assertEqual(model123.amount_result, 889.0)
        with Form(model123, view=self.form_view) as report_form:
            report_form.casilla_13_2024 = 240
        self.assertEqual(model123.casilla_14_2024, 649.0)
        self.assertEqual(model123.amount_result, 649.0)
        # Export to BOE, compared with the AEAT record design of model 123
        # (DR123e24.xls, sede.agenciatributaria.gob.es, sheets "DR 12300" and
        # "DR 12301")
        content = self._export_boe(model123)
        self.assertEqual(len(content), 328 + 600 + 18 + 2)
        expected_header = "".join(
            [
                "<T",  # 1-2 Constante
                "123",  # 3-5 Modelo
                "0",  # 6 Constante
                "2024",  # 7-10 Ejercicio
                "1T",  # 11-12 Periodo
                "0000>",  # 13-17 Constante
                "<AUX>",  # 18-22 Constante
                " " * 70,  # 23-92 Reservado
                "ODOO",  # 93-96 Versión del programa
                " " * 4,  # 97-100 Reservado
                "G87846952",  # 101-109 NIF empresa desarrollo
                " " * 213,  # 110-322 Reservado
                "</AUX>",  # 323-328 Constante
            ]
        )
        self.assertEqual(content[:328], expected_header)
        expected_page = "".join(
            [
                "<T",  # 1-2 Inicio del identificador
                "123",  # 3-5 Modelo
                "01",  # 6-7 Página
                "000>",  # 8-11 Fin de identificador
                " ",  # 12 Indicador de página complementaria
                "U",  # 13 Tipo de declaración
                "123456789",  # 14-22 NIF
                "SPANISH TEST COMPANY".ljust(80),  # 23-102 Razón social
                "2024",  # 103-106 Ejercicio
                "1T",  # 107-108 Periodo
                "000000000000001",  # 109-123 [01]
                "000000000000002",  # 124-138 [02]
                "000000000000003",  # 139-153 [03]
                "00000000000150000",  # 154-170 [04]
                "00000000000210000",  # 171-187 [05]
                "00000000000360000",  # 188-204 [06]
                "00000000000031000",  # 205-221 [07]
                "00000000000039900",  # 222-238 [08]
                "00000000000070900",  # 239-255 [09]
                "00000000000000000",  # 256-272 [10]
                "00000000000018000",  # 273-289 [11]
                "00000000000088900",  # 290-306 [12]
                "00000000000024000",  # 307-323 [13]
                "00000000000064900",  # 324-340 [14]
                "X",  # 341 Declaración complementaria
                "1230000000001",  # 342-354 Justificante de la declaración anterior
                "ES9121000418450200051332".ljust(34),  # 355-388 IBAN
                " " * 200,  # 389-588 Reservado AEAT
                "</T12301000>",  # 589-600 Indicador de fin de registro
            ]
        )
        self.assertEqual(len(expected_page), 600)
        self.assertEqual(content[328:928], expected_page)
