# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2018 Valentin Vinagre <valentin.vinagre@qubiq.es>
# Copyright Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging
from typing import ClassVar

from odoo.fields import Command

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.296")


class TestL10nEsAeatMod296Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "l10n_es.account_tax_template_p_irpfnrnue24p": (1000, 240),
        "l10n_es.account_tax_template_p_irpfnrue19p": (2000, 380),
    }
    taxes_result: ClassVar[dict] = {
        # Rendimientos del trabajo (dinerarios) - Base
        "2": 6000,
        # Rendimientos del trabajo (dinerarios) - Retenciones
        "3": 1240,  # (2 * 240) + (2 * 380)
    }

    def test_model_296(self):
        self.supplier.write(
            {
                "street": "Main Street 1",
                "street2": "Suite 2",
                "city": "Los Angeles",
                "zip": "90001",
                "country_id": self.env.ref("base.us").id,
                "state_id": self.env.ref("base.state_us_5").id,
            }
        )
        # Purchase invoices
        self._invoice_purchase_create("2025-01-01")
        self._invoice_purchase_create("2025-01-02")
        self._invoice_purchase_create("2027-01-02")
        # Create model
        self.model296 = self.env["l10n.es.aeat.mod296.report"].create(
            {
                "name": "2960000000001",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2025,
                "period_type": "0A",
                "date_start": "2025-01-01",
                "date_end": "2025-12-31",
                "journal_id": self.journal_misc.id,
            }
        )
        _logger.debug("Calculate AEAT 296 0A 2025")
        self.model296.button_calculate()
        self.assertEqual(self.model296.casilla_02, self.taxes_result["2"])
        self.assertEqual(self.model296.casilla_03, self.taxes_result["3"])
        self.assertEqual(len(self.model296.lines296), 1)
        # The line keeps the base and retention move lines of its partner
        tax_move_lines = self.model296.tax_line_ids.filtered(
            lambda x: x.field_number in (2, 3)
        ).move_line_ids
        line = self.model296.lines296
        self.assertEqual(line.move_line_ids, tax_move_lines)
        self.assertEqual(line.partner_id, tax_move_lines.partner_id)
        # Data the user fills in by hand on the report and on the line
        self.model296.casilla_04 = 1240
        line.write(
            {
                "fisica_juridica": "J",
                "fecha_devengo": "2024-12-15",
                "naturaleza": "D",
                "clave": "2",
                "subclave": "1",
                "porcentaje_retencion": 19,
                "mediador": True,
                "codigo": "2",
                "codigo_emisor": "ES0000012345",
                "pago": "1",
                "tipo_codigo": "C",
                "cuenta_valores": self.env["res.partner.bank"]
                .create(
                    {
                        "partner_id": self.supplier.id,
                        "account_number": "ES91 2100 0418 4502 0005 1332",
                    }
                )
                .id,
                "nif_pais_residencia": "US123456789",
                "pais_residencia_fiscal": self.env.ref("base.us").id,
            }
        )
        # Export to BOE through the report button
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=self.model296.id, active_model=self.model296._name)
            .create({})
        )
        wizard.action_get_file()
        content = wizard.data.content.decode("iso-8859-1")
        # One declarant record and one perceptor record of 500 positions each
        # (AEAT record design of model 296, DR 2024)
        self.assertEqual(len(content), 1000)
        declarant, perceptor = content[:500], content[500:]
        expected_declarant = "".join(
            [
                "1",  # 1 Tipo de registro
                "296",  # 2-4 Modelo
                "2025",  # 5-8 Ejercicio
                "123456789",  # 9-17 NIF declarante
                "SPANISH TEST COMPANY".ljust(40),  # 18-57 Razón social
                "T",  # 58 Tipo de soporte
                "911234455",  # 59-67 Teléfono
                "TEST OWNER".ljust(40),  # 68-107 Persona de contacto
                "2960000000001",  # 108-120 Número identificativo
                "  ",  # 121-122 Complementaria / sustitutiva
                "0" * 13,  # 123-135 Declaración anterior
                "000000001",  # 136-144 [01] Número de perceptores
                " 00000000600000",  # 145-159 [02] Base: signo y 12+2
                "000000000124000",  # 160-174 [03] Retenciones: 13+2
                "000000000124000",  # 175-189 [04] Ingresados: 13+2
                " " * 201,  # 190-390 Blancos
                " " * 9,  # 391-399 NIF representante legal
                " " * 88,  # 400-487 Blancos
                " " * 13,  # 488-500 Sello electrónico
            ]
        )
        self.assertEqual(len(expected_declarant), 500)
        self.assertEqual(declarant, expected_declarant)
        expected_perceptor = "".join(
            [
                "2",  # 1 Tipo de registro
                "296",  # 2-4 Modelo
                "2025",  # 5-8 Ejercicio
                "123456789",  # 9-17 NIF declarante
                " " * 9,  # 18-26 NIF perceptor (no Spanish NIF)
                " " * 9,  # 27-35 NIF representante legal
                "J",  # 36 F/J
                "TEST SUPPLIER".ljust(40),  # 37-76 Perceptor
                " " * 8,  # 77-84 Identificador de registro
                " " * 6,  # 85-90 Código BIC del perceptor mediador
                "15122024",  # 91-98 Fecha de devengo DDMMAAAA
                "D",  # 99 Naturaleza
                "02",  # 100-101 Clave
                "01",  # 102-103 Subclave
                " 000000600000",  # 104-116 Base: signo y 10+2
                "1900",  # 117-120 % retención: 2+2
                "0000000124000",  # 121-133 Retenciones: 11+2
                "1",  # 134 Perceptor mediador residente en España
                "2",  # 135 Código: ISIN
                "ES0000012345",  # 136-147 Código emisor
                "1",  # 148 Declarante: pago como emisor
                "C",  # 149 Tipo código
                "21000418450200051332",  # 150-169 Código cuenta valores
                " ",  # 170 Pendiente
                "2024",  # 171-174 Ejercicio de devengo
                "0" * 8,  # 175-182 Fecha de inicio del préstamo
                "0" * 8,  # 183-190 Fecha de vencimiento del préstamo
                "0" * 12,  # 191-202 Remuneración al prestamista
                "0" * 12,  # 203-214 Compensaciones
                "0" * 12,  # 215-226 Garantías
                "MAIN STREET 1".ljust(50),  # 227-276 Domicilio
                "SUITE 2".ljust(40),  # 277-316 Complemento del domicilio
                "LOS ANGELES".ljust(30),  # 317-346 Población
                "CALIFORNIA".ljust(30),  # 347-376 Provincia/región/estado
                "90001".ljust(10),  # 377-386 Código postal
                "US",  # 387-388 Código país
                "0" * 13,  # 389-401 Ingresos a cuenta repercutidos
                " " * 9,  # 402-410 NIF del pagador anterior
                " ",  # 411 Procedimiento especial de retenciones
                " ",  # 412 Clave de mercado
                " " * 20,  # 413-432 Código LEI del perceptor
                "US123456789".ljust(20),  # 433-452 NIF en el país de residencia
                "0" * 8,  # 453-460 Fecha de nacimiento
                " " * 35,  # 461-495 Lugar de nacimiento: ciudad
                "  ",  # 496-497 Lugar de nacimiento: código país
                "US",  # 498-499 País de residencia fiscal
                " ",  # 500 Blanco
            ]
        )
        self.assertEqual(len(expected_perceptor), 500)
        self.assertEqual(perceptor, expected_perceptor)

    def _purchase_invoice(self, date, lines):
        """Post a vendor bill of the supplier with one line per (tax, price)."""
        return self._invoice_purchase_create(
            date,
            extra_vals={
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

    def test_model_296_recalculate(self):
        """The withholding rate comes from the tax of the perceptor, and the
        data entered on its line is kept when the report is recalculated."""
        tax = "l10n_es.account_tax_template_p_irpfnrnue24p"
        self._purchase_invoice("2025-03-01", [(tax, 1000)])
        model296 = self.env["l10n.es.aeat.mod296.report"].create(
            {
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2025,
                "period_type": "0A",
                "date_start": "2025-01-01",
                "date_end": "2025-12-31",
            }
        )
        model296.button_calculate()
        line = model296.lines296
        self.assertEqual(line.porcentaje_retencion, 24)
        self.assertEqual(line.base_retenciones_ingresos, 1000)
        line.write(
            {
                "fisica_juridica": "J",
                "clave": "2",
                "subclave": "2",
                "porcentaje_retencion": 10,
                "nif_pais_residencia": "US123456789",
            }
        )
        # A new bill of the perceptor arrives and the report is recalculated
        self._purchase_invoice("2025-04-01", [(tax, 500)])
        model296.button_recalculate()
        line = model296.lines296
        self.assertEqual(len(line), 1)
        self.assertEqual(line.base_retenciones_ingresos, 1500)
        self.assertEqual(line.retenciones_ingresos, 360)
        self.assertEqual(line.fisica_juridica, "J")
        self.assertEqual(line.clave, "2")
        self.assertEqual(line.subclave, "2")
        self.assertEqual(line.porcentaje_retencion, 10)
        self.assertEqual(line.nif_pais_residencia, "US123456789")

    def _create_report(self):
        return self.env["l10n.es.aeat.mod296.report"].create(
            {
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "contact_phone": "911234455",
                "year": 2025,
                "period_type": "0A",
                "date_start": "2025-01-01",
                "date_end": "2025-12-31",
            }
        )

    def _export_boe(self, report):
        """Export the report through its 'Export to BOE' button."""
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=report.id, active_model=report._name)
            .create({})
        )
        wizard.action_get_file()
        return wizard.data.content.decode("iso-8859-1")

    def test_model_296_exempt(self):
        """An income exempt by treaty is declared with subkey 04, a 0 % rate,
        no withholding and its base (DR 296 2024, positions 102-133)."""
        self._purchase_invoice(
            "2025-05-01", [("l10n_es.account_tax_template_p_irpfnrue0p", 3000)]
        )
        model296 = self._create_report()
        model296.button_calculate()
        self.assertEqual(model296.casilla_01, 1)
        self.assertEqual(model296.casilla_02, 3000)
        self.assertEqual(model296.casilla_03, 0)
        line = model296.lines296
        self.assertEqual(len(line), 1)
        self.assertEqual(line.partner_id, self.supplier)
        self.assertEqual(line.base_retenciones_ingresos, 3000)
        self.assertEqual(line.retenciones_ingresos, 0)
        self.assertEqual(line.porcentaje_retencion, 0)
        self.assertEqual(line.subclave, "4")
        # An internal exemption is set by hand and kept on recalculation
        line.subclave = "3"
        model296.button_recalculate()
        self.assertEqual(model296.lines296.subclave, "3")
        model296.lines296.subclave = "4"
        content = self._export_boe(model296)
        self.assertEqual(len(content), 1000)
        perceptor = content[500:]
        self.assertEqual(perceptor[101:103], "04")  # 102-103 Subclave
        self.assertEqual(perceptor[103:116], " 000000300000")  # 104-116 Base
        self.assertEqual(perceptor[116:120], "0000")  # 117-120 % retención
        self.assertEqual(perceptor[120:133], "0" * 13)  # 121-133 Retenciones
