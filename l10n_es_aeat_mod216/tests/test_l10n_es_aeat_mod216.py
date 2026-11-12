# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from typing import ClassVar

from odoo.tests import Form

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.216")


class TestL10nEsAeatMod216Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "l10n_es.account_tax_template_p_irpfnrnue24p": (1000, 240),
        "l10n_es.account_tax_template_p_irpfnrue19p": (2000, 380),
        "l10n_es.account_tax_template_p_irpfnrnue0p": (3000, 0),
    }
    taxes_result: ClassVar[dict] = {
        # Rentas sometidas a retención - Base
        "2": 12000,
        # Rentas sometidas a retención - Retenciones
        "3": 1240,  # (2 * 240) + (2 * 380) + (2 * 0)
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The view the menu action opens
        cls.form_view = "l10n_es_aeat_mod216.view_l10n_es_aeat_mod216_report_form"
        cls.bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "account_number": "ES91 2100 0418 4502 0005 1332",
            }
        )

    def _create_report(self, year, **values):
        """Fill in the report form as the user does and press 'Calculate'."""
        with Form(self.env["l10n.es.aeat.mod216.report"], view=self.form_view) as f:
            f.company_vat = "123456789"
            f.contact_name = "Test owner"
            f.contact_phone = "911234455"
            f.year = year
            f.period_type = "1T"
            for field, value in values.items():
                setattr(f, field, value)
        report = f.record
        _logger.debug("Calculate AEAT 216 1T %s", year)
        report.button_calculate()
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

    def _check_tax_lines(self, report):
        for box, result in self.taxes_result.items():
            _logger.debug("Checking tax line: %s", box)
            lines = report.tax_line_ids.filtered(
                lambda x, box=box: x.field_number == int(box)
            )
            self.assertEqual(round(sum(lines.mapped("amount")), 2), round(result, 2))

    def test_model_216_before_2024(self):
        # Purchase invoices
        self._invoice_purchase_create("2023-01-01")
        self._invoice_purchase_create("2023-01-02")
        purchase = self._invoice_purchase_create("2023-01-03")
        self._invoice_refund(purchase, "2023-01-18")
        self.model216 = self._create_report(
            2023,
            tipo_declaracion="U",
            partner_bank_id=self.bank,
            statement_type="C",
            previous_number="2160000000001",
        )
        self.assertEqual(
            self.model216.export_config_id,
            self.env.ref("l10n_es_aeat_mod216.aeat_mod216_main_export_config"),
        )
        # Fill manual fields: Resultados a ingresar anteriores
        with Form(self.model216, view=self.form_view) as report_form:
            report_form.casilla_06_pre_2024 = 145
        self._check_tax_lines(self.model216)
        # Check result
        _logger.debug("Checking results")
        retenciones = self.taxes_result.get("3", 0.0)
        result = retenciones - 145
        # Three incomes of the same perceptor; the refund is not an income
        self.assertEqual(self.model216.casilla_01_pre_2024, 3)
        self.assertEqual(
            round(self.model216.casilla_03_pre_2024, 2), round(retenciones, 2)
        )
        self.assertEqual(round(self.model216.casilla_07_pre_2024, 2), round(result, 2))
        # Export to BOE: the direct debit account goes without spaces
        content = self._export_boe(self.model216)
        self.assertTrue(content.startswith("<T216020231T0000><AUX>"))
        self.assertTrue(content.endswith("</T216020231T0000>\r\n"))
        self.assertIn("ES9121000418450200051332", content)

    def test_model_216_2024(self):
        self.taxes_result = {
            # Resto de rentas sometidas a retención - Base
            "9": 12000,
            # Resto de rentas sometidas a retención - Retenciones
            "12": 1240,  # (2 * 240) + (2 * 380) + (2 * 0)
        }
        # Purchase invoices
        self._invoice_purchase_create("2024-01-01")
        self._invoice_purchase_create("2024-01-02")
        purchase = self._invoice_purchase_create("2024-01-03")
        self._invoice_refund(purchase, "2024-01-18")
        self.model216 = self._create_report(
            2024,
            tipo_declaracion="U",
            partner_bank_id=self.bank,
            statement_type="C",
            previous_number="2160000000001",
        )
        self.assertEqual(
            self.model216.export_config_id,
            self.env.ref("l10n_es_aeat_mod216.aeat_mod216_2024_main_export_config"),
        )
        # Fill manual fields in the form of the calculated report
        with Form(self.model216, view=self.form_view) as report_form:
            # Num. rentas dividendos sometidas
            report_form.casilla_05 = 2
            # Base rentas dividendos sometidas
            report_form.casilla_08 = 200
            # Retenciones rentas dividendos sometidas
            report_form.casilla_11 = 38
            # Num. rentas dividendos no sometidas
            report_form.casilla_14 = 1
            # Num. rentas resto rentas no sometidas
            report_form.casilla_15 = 3
            # Base dividendos rentas no sometidas
            report_form.casilla_17 = 180
            # Base resto rentas no sometidas
            report_form.casilla_18 = 125
            # Resultados a ingresar anteriores
            report_form.casilla_20 = 145
        self._check_tax_lines(self.model216)
        # Check result
        _logger.debug("Checking results")
        base = self.taxes_result.get("9", 0.0)
        retenciones = self.taxes_result.get("12", 0.0)
        result = retenciones + 38 - 145
        # Three incomes of the same perceptor; the refund is not an income
        self.assertEqual(self.model216.casilla_06, 3)
        self.assertEqual(self.model216.casilla_07, 5)
        self.assertEqual(round(self.model216.casilla_09, 2), round(base, 2))
        self.assertEqual(round(self.model216.casilla_10, 2), round(base + 200, 2))
        self.assertEqual(round(self.model216.casilla_12, 2), round(retenciones, 2))
        self.assertEqual(round(self.model216.casilla_13, 2), round(retenciones + 38, 2))
        self.assertEqual(self.model216.casilla_16, 4)
        self.assertEqual(round(self.model216.casilla_19, 2), 305)
        self.assertEqual(round(self.model216.casilla_21, 2), round(result, 2))
        # Export to BOE, compared with the AEAT record design of model 216
        # (216e2024.xlsx, sede.agenciatributaria.gob.es, sheets "Pág. 0" and
        # "Pág. 1")
        content = self._export_boe(self.model216)
        self.assertEqual(len(content), 328 + 600 + 18)
        expected_header = "".join(
            [
                "<T",  # 1-2 Inicio del identificador
                "216",  # 3-5 Modelo
                "0",  # 6 Discriminante
                "2024",  # 7-10 Ejercicio
                "1T",  # 11-12 Periodo
                "0000>",  # 13-17 Tipo y cierre
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
                "216",  # 3-5 Modelo
                "01000",  # 6-10 Página
                ">",  # 11 Fin de identificador
                " ",  # 12 Indicador de página complementaria
                "U",  # 13 Tipo de autoliquidación
                "123456789",  # 14-22 NIF
                "SPANISH TEST COMPANY".ljust(80),  # 23-102 Razón social
                "2024",  # 103-106 Ejercicio
                "1T",  # 107-108 Periodo
                "00000000000000002",  # 109-125 [05]
                "00000000000000003",  # 126-142 [06]
                "00000000000000005",  # 143-159 [07]
                "00000000000020000",  # 160-176 [08]
                "00000000001200000",  # 177-193 [09]
                "00000000001220000",  # 194-210 [10]
                "00000000000003800",  # 211-227 [11]
                "00000000000124000",  # 228-244 [12]
                "00000000000127800",  # 245-261 [13]
                "00000000000000001",  # 262-278 [14]
                "00000000000000003",  # 279-295 [15]
                "00000000000000004",  # 296-312 [16]
                "00000000000018000",  # 313-329 [17]
                "00000000000012500",  # 330-346 [18]
                "00000000000030500",  # 347-363 [19]
                "00000000000014500",  # 364-380 [20]
                "00000000000113300",  # 381-397 [21]
                "ES9121000418450200051332".ljust(34),  # 398-431 IBAN
                "X",  # 432 Declaración complementaria
                "2160000000001",  # 433-445 Justificante de la declaración anterior
                " " * 143,  # 446-588 Reservado
                "</T21601000>",  # 589-600 Indicador de fin de registro
            ]
        )
        self.assertEqual(len(expected_page), 600)
        self.assertEqual(content[328:928], expected_page)
        self.assertEqual(content[928:], "</T216020241T0000>")
