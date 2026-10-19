# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging
import re

from odoo import exceptions, fields

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.322")


class TestL10nEsAeatMod322Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA4B": (1000, 40),
        "S_IVA4B//neg": (-100, -4),
        "S_IVA4S": (1100, 44),
        "S_IVA10B": (1200, 120),
        "S_IVA10B//neg": (-120, -12),
        "S_IVA10S": (1300, 130),
        "S_IVA21B": (1400, 294),
        "S_IVA21B//neg": (-140, -29.4),
        "S_IVA21S": (1500, 315),
        "S_REQ05": (1700, 8.5),
        "S_REQ014": (1800, 25.2),
        "S_REQ52": (1900, 98.8),
        "S_IVA0_G_E": (2000, 0),
        "S_IVA_E": (2100, 0),
        "S_IVA_NS": (2200, 0),
        "S_IVA0_ISP": (2300, 0),
        "S_IVA0_G_I": (2400, 0),
        "S_IVA0_SP_I": (2500, 0),
        "S_IVA0": (2600, 0),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IVA4_IC_BC": (100, 0),
        "P_IVA10_IC_BC": (200, 0),
        "P_IVA21_IC_BC": (300, 0),
        "P_IVA4_SP_IN": (400, 0),
        "P_IVA10_SP_IN": (500, 0),
        "P_IVA21_SP_IN": (600, 0),
        "P_IVA4_IC_BI": (700, 0),
        "P_IVA10_IC_BI": (800, 0),
        "P_IVA21_IC_BI": (900, 0),
        "P_IVA4_SP_EX": (110, 0),
        "P_IVA10_SP_EX": (120, 0),
        "P_IVA21_SP_EX": (130, 0),
        "P_IVA4_ISP": (140, 0),
        "P_IVA10_ISP": (150, 0),
        "P_IVA21_ISP": (160, 0),
        "P_IVA4_SC": (210, 8.4),
        "P_IVA4_SC//neg": (-21, -0.84),
        "P_IVA10_SC": (220, 22),
        "P_IVA10_SC//neg": (-22, -2.2),
        "P_IVA21_SC": (230, 48.3),
        "P_IVA21_SC//neg": (-23, -4.83),
        "P_IVA4_BC": (240, 9.6),
        "P_IVA10_BC": (250, 25),
        "P_IVA21_BC": (260, 54.6),
        "P_REQ05": (270, 1.35),
        "P_REQ014": (280, 3.92),
        "P_REQ52": (290, 15.08),
        "P_IVA4_BI": (310, 12.4),
        "P_IVA10_BI": (320, 32),
        "P_IVA21_BI": (330, 69.3),
        "P_IVA4_IBC": (340, 13.6),
        "P_IVA10_IBC": (350, 35),
        "P_IVA21_IBC": (360, 75.6),
        "P_IVA4_IBI": (370, 14.8),
        "P_IVA10_IBI": (380, 38),
        "P_IVA21_IBI": (390, 81.9),
        # 'P_IVA12_AGR': (410, 49.2),
    }
    taxes_result = {
        # Régimen General - Base imponible 4% Intragrupo
        "1": 1000 + 1100 - 100,  # S_IVA4B, S_IVA4S
        # Régimen General - Cuota 4% Intragrupo
        "3": 40 + 44 - 4,  # S_IVA4B, S_IVA4S
        # Régimen General - Base imponible 10% Intragrupo
        "4": 1200 + 1300 - 120,  # S_IVA10B, S_IVA10S
        # Régimen General - Cuota 10% Intragrupo
        "6": 120 + 130 - 12,  # S_IVA10B, S_IVA10S
        # Régimen General - Base imponible 21%
        # S_IVA21B, S_IVA21S Intragrupo
        "7": 1400 + 1500 - 140,
        # Régimen General - Cuota 21% Intragrupo
        # S_IVA21B, S_IVA21S
        "9": 294 + 315 - 29.4,
        # Modificación bases y cuotas - Base (Compras y ventas)  Resto
        "19": 0,
        # Modificación bases y cuotas - Cuota (Compras y ventas) Resto
        "11": 0,
        # Adq. intracomunitarias de bienes y servicios - Base
        # Régimen General - Base imponible 4% Resto
        "12": 2 * 1000 + 2 * 1100 - 2 * 100,  # S_IVA4B, S_IVA4S
        # Régimen General - Cuota 4% Resto
        "14": 2 * 40 + 2 * 44 - 2 * 4,  # S_IVA4B, S_IVA4S
        # Régimen General - Base imponible 10% Resto
        "15": 2 * 1200 + 2 * 1300 - 2 * 120,  # S_IVA10B, S_IVA10S
        # Régimen General - Cuota 10% Resto
        "17": 2 * 120 + 2 * 130 - 2 * 12,  # S_IVA10B, S_IVA10S
        # Régimen General - Base imponible 21%
        # S_IVA21B, S_IVA21S Resto
        "18": 2 * 1400 + 2 * 1500 - 2 * 140,
        # Régimen General - Cuota 21% Resto
        # S_IVA21B, S_IVA21S
        "20": 2 * 294 + 2 * 315 - 2 * 29.4,
        "21": (
            (3 * 100)
            + (3 * 200)
            + (3 * 300)
            + (3 * 400)  # P_IVAx_IC_BC_2
            + (3 * 500)
            + (3 * 600)
            + (3 * 700)  # P_IVAx_SP_IN_1
            + (3 * 800)
            + (3 * 900)  # P_IVAx_IC_BI_2
        ),
        # Adq. intracomunitarias de bienes y servicios - Cuota
        "22": (
            (3 * 4)
            + (3 * 20)
            + (3 * 63)
            + (3 * 16)  # P_IVAx_IC_BC_2
            + (3 * 50)
            + (3 * 126)
            + (3 * 28)  # P_IVAx_SP_IN_1
            + (3 * 80)
            + (3 * 189)  # P_IVAx_IC_BI_2
        ),
        # Op. inv. del suj. pasivo (excepto adq. intracom.) - Base
        "23": (
            (3 * 110)
            + (3 * 120)
            + (3 * 130)
            + (3 * 140)  # P_IVAx_SP_EX_1
            + (3 * 150)
            + (3 * 160)  # P_IVAx_ISP_2
        ),
        # Op. inv. del suj. pasivo (excepto adq. intracom.) - Cuota
        "24": (
            (3 * 4.4)
            + (3 * 12)
            + (3 * 27.3)
            + (3 * 5.6)  # P_IVAx_SP_EX_1
            + (3 * 15)
            + (3 * 33.6)  # P_IVAx_ISP_2
        ),
        # Modificación bases y cuotas - Base (Compras y ventas)
        "25": (
            (-1)
            * (
                1000
                + 1100
                - 100
                + 1200  # S_IVA4B, S_IVA4S
                + 1300
                - 120
                + 1400  # S_IVA10B, S_IVA10S
                + 1500
                - 140
                + 100  # S_IVA21B, S_IVA21S
                + 200
                + 300
                + 400  # P_IVAx_IC_BC_2
                + 500
                + 600
                + 700  # P_IVAx_SP_IN_1
                + 800
                + 900
                + 110  # P_IVAx_IC_BI_2
                + 120
                + 130
                + 140  # P_IVAx_SP_EX_1
                + 150
                + 160
            )  # P_IVAx_ISP_2
        ),
        # Modificación bases y cuotas - Cuota (Compras y ventas)
        "26": (
            (-1)
            * (
                40
                + 44
                - 4
                + 120  # S_IVA4B, S_IVA4S
                + 130
                - 12
                + 294  # S_IVA10B, S_IVA10S
                + 315
                - 29.4
                + 4  # S_IVA21B, S_IVA21S
                + 20
                + 63
                + 16  # P_IVAx_IC_BC_2
                + 50
                + 126
                + 28  # P_IVAx_SP_IN_1
                + 80
                + 189
                + 4.4  # P_IVAx_IC_BI_2
                + 12
                + 27.3
                + 5.6  # P_IVAx_SP_EX_1
                + 15
                + 33.6
            )  # P_IVAx_ISP_2
        ),
        # Recargo equivalencia - Base imponible 0.5%
        "27": (3 * 1700),  # S_REQ05
        # Recargo equivalencia - Cuota 0.5%
        "29": (3 * 8.5),  # S_REQ05
        # Recargo equivalencia - Base imponible 1.4%
        "30": (3 * 1800),  # S_REQ014
        # Recargo equivalencia - Cuota 1.4%
        "32": (3 * 25.2),  # S_REQ014
        # Recargo equivalencia - Base imponible 5.2%
        "33": (3 * 1900),  # S_REQ52
        # Recargo equivalencia - Cuota 5.2%
        "35": (3 * 98.8),  # S_REQ52
        # Mod. bases y cuotas del recargo de equivalencia - Base
        "36": (-1) * (1700 + 1800 + 1900),  # S_REQ05, S_REQ014, S_REQ52
        # Mod. bases y cuotas del recargo de equivalencia - Cuota
        "37": (-1) * (8.5 + 25.2 + 98.8),  # S_REQ05, S_REQ014, S_REQ52
        # Cuotas soportadas en op. int. corrientes - Base Intragrupo
        "39": (
            110
            + 120
            + 130
            + 140  # P_IVAx_SP_EX_2
            + 150
            + 160
            + 210  # P_IVAx_ISP_1
            + 220
            + 230
            + -21
            + -22
            + -23
            + 240  # P_IVAx_SC
            + 250
            + 260
            + 270  # P_IVAx_BC
            + 280
            + 290  # P_REQ05, P_REQ014, P_REQ5.2
        ),
        # Cuotas soportadas en op. int. corrientes - Cuota Intragrupo
        "40": (
            4.4
            + 12
            + 27.3
            + 5.6  # P_IVAx_SP_EX_2
            + 15
            + 33.6
            + 8.4  # P_IVAx_ISP_1
            + 22
            + 48.3
            + -0.84
            + -2.2
            + -4.83
            + 9.6  # P_IVAx_SC
            + 25
            + 54.6
            + 1.35  # P_IVAx_BC
            + 3.92
            + 15.08  # P_REQ05, P_REQ014  # P_REQ5.2
        ),
        # Cuotas soportadas en op. int. bienes de inversión - Base Intragrupo
        "41": 310 + 320 + 330,  # P_IVAx_BI
        # Cuotas soportadas en op. int. bienes de inversión - Cuota Intragrupo
        "42": 12.4 + 32 + 69.3,  # P_IVAx_BI
        # Rectificación de deducciones - Base Intragrupo
        "43": 0,
        # Rectificación de deducciones - Cuota intragrupo
        "44": 0,
        # Cuotas soportadas en op. int. corrientes - Base Resto
        "45": (
            (2 * 110)
            + (2 * 120)
            + (2 * 130)
            + (2 * 140)  # P_IVAx_SP_EX_2
            + (2 * 150)
            + (2 * 160)
            + (2 * 210)  # P_IVAx_ISP_1
            + (2 * 220)
            + (2 * 230)
            + (2 * -21)
            + (2 * -22)
            + (2 * -23)
            + (2 * 240)  # P_IVAx_SC
            + (2 * 250)
            + (2 * 260)
            + (2 * 270)  # P_IVAx_BC
            + (2 * 280)
            + (2 * 290)  # P_REQ05, P_REQ014, P_REQ5.2
        ),
        # Cuotas soportadas en op. int. corrientes - Cuota Resto
        "46": (
            (2 * 4.4)
            + (2 * 12)
            + (2 * 27.3)
            + (2 * 5.6)  # P_IVAx_SP_EX_2
            + (2 * 15)
            + (2 * 33.6)
            + (2 * 8.4)  # P_IVAx_ISP_1
            + (2 * 22)
            + (2 * 48.3)
            + (2 * -0.84)
            + (2 * -2.2)
            + (2 * -4.83)
            + (2 * 9.6)  # P_IVAx_SC
            + (2 * 25)
            + (2 * 54.6)
            + (2 * 1.35)  # P_IVAx_BC
            + (2 * 3.92)
            + (2 * 15.08)  # P_REQ05, P_REQ014  # P_REQ5.2
        ),
        # Cuotas soportadas en op. int. bienes de inversión - Base Resto
        "47": (2 * 310) + (2 * 320) + (2 * 330),  # P_IVAx_BI
        # Cuotas soportadas en op. int. bienes de inversión - Cuota Resto
        "48": (2 * 12.4) + (2 * 32) + (2 * 69.3),  # P_IVAx_BI
        # Cuotas soportadas en las imp. bienes corrientes - Base
        "49": (3 * 340) + (3 * 350) + (3 * 360),  # P_IVAx_IBC
        # Cuotas soportadas en las imp. bienes corrientes - Cuota
        "50": (3 * 13.6) + (3 * 35) + (3 * 75.6),  # P_IVAx_IBC
        # Cuotas soportadas en las imp. bienes de inversión - Base
        "51": (3 * 370) + (3 * 380) + (3 * 390),  # P_IVAx_IBI
        # Cuotas soportadas en las imp. bienes de inversión - Cuota
        "52": (3 * 14.8) + (3 * 38) + (3 * 81.9),  # P_IVAx_IBI
        # En adq. intra. de bienes y servicios corrientes - Base
        "53": (
            (3 * 100)
            + (3 * 200)
            + (3 * 300)
            + (3 * 400)  # P_IVAx_IC_BC_1
            + (3 * 500)
            + (3 * 600)  # P_IVAx_SP_IN_2
        ),
        # En adq. intra. de bienes y servicios corrientes - Cuota
        "54": (
            (3 * 4)
            + (3 * 20)
            + (3 * 63)
            + (3 * 16)  # P_IVAx_IC_BC_1
            + (3 * 50)
            + (3 * 126)  # P_IVAx_SP_IN_2
        ),
        # En adq. intra. de bienes de inversión - Base
        "55": (3 * 700) + (3 * 800) + (3 * 900),  # P_IVAx_IC_BI_1
        # En adq. intra. de bienes de inversión - Cuota
        "56": (3 * 28) + (3 * 80) + (3 * 189),  # P_IVAx_IC_BI_1
        # Rectificación de deducciones - Base Resto
        "57": (
            (-1)
            * (
                270
                + 280
                + 290
                + 240  # P_REQ05, P_REQ014, P_REQ5.2
                + 250
                + 260
                + 210  # P_IVAx_BC
                + 220
                + 230
                - 21
                - 22
                - 23
                + 310  # P_IVAx_SC
                + 320
                + 330
                + 340  # P_IVAx_BI
                + 350
                + 360
                + 370  # P_IVAx_IBC
                + 380
                + 390
                + 100  # P_IVAx_IBI
                + 200
                + 300
                + 700  # P_IVAx_IC_BC_1
                + 800
                + 900
                + 400  # P_IVAx_IC_BI_1
                + 500
                + 600
                + 110  # P_IVAx_SP_IN_2
                + 120
                + 130
                + 140  # P_IVAx_SP_EX_2
                + 150
                + 160  # P_IVAx_ISP_1
            )
        ),
        # Rectificación de deducciones - Cuota Resto
        "58": (
            (-1)
            * (
                1.35
                + 3.92
                + 15.08
                + 9.6  # P_REQ05, P_REQ014, P_REQ5.2
                + 25
                + 54.6
                + 8.4  # P_IVAx_BC
                + 22
                + 48.3
                - 0.84
                - 2.2
                - 4.83
                + 12.4  # P_IVAx_SC
                + 32
                + 69.3
                + 13.6  # P_IVAx_BI
                + 35
                + 75.6
                + 14.8  # P_IVAx_IBC
                + 38
                + 81.9
                + 4  # P_IVAx_IBI
                + 20
                + 63
                + 28  # P_IVAx_IC_BC_1
                + 80
                + 189
                + 16  # P_IVAx_IC_BI_1
                + 50
                + 126
                + 4.4  # P_IVAx_SP_IN_2
                + 12
                + 27.3
                + 5.6  # P_IVAx_SP_EX_2
                + 15
                + 33.6  # P_IVAx_ISP_1
            )
        ),
        # Compensaciones Rég. especial A. G. y P. - Cuota compras
        "59": 0,
        # Regularización bienes de inversión
        "60": 0,
        # Regularización por aplicación del porcentaje definitivo de prorrata
        "61": 0,
        # Entregas intra. de bienes y servicios - Base ventas
        # S_IVA0_G_I, S_IVA0_SP_I
        "71": (2 * 2400) + (2 * 2500),
        # Exportaciones y operaciones asimiladas - Base ventas
        # S_IVA0_G_E, S_IVA0
        "72": (2 * 2000) + (2 * 2600),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create model
        cls.company.write({"vat": "ESA12345674"})
        cls.model322 = cls.env["l10n.es.aeat.mod322.report"].create(
            {
                "name": "9990000000322",
                "company_id": cls.company.id,
                "company_vat": "ESA12345674",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2024,
                "period_type": "11",
                "date_start": "2024-11-01",
                "date_end": "2024-11-30",
                "journal_id": cls.journal_misc.id,
            }
        )
        cls.model322_4t = cls.model322.copy(
            {
                "name": "9994000000322",
                "period_type": "12",
                "date_start": "2024-12-01",
                "date_end": "2024-12-31",
            }
        )


class TestL10nEsAeatMod322(TestL10nEsAeatMod322Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Purchase invoices
        cls.related_partner = cls.env["res.partner"].create(
            {
                "name": "Related company",
            }
        )
        cls.env["l10n.es.aeat.mod322.group"].create(
            {
                "name": "IVA/2024/23",
                "main_company_id": cls.company.id,
                "vinculated_partner_ids": [(4, cls.related_partner.id)],
            }
        )
        cls._invoice_purchase_create(
            "2024-11-01", extra_vals={"partner_id": cls.related_partner.id}
        )
        cls._invoice_purchase_create("2024-11-02")
        purchase = cls._invoice_purchase_create("2024-11-03")
        cls._invoice_refund(purchase, "2024-11-18")
        # Sale invoices
        cls._invoice_sale_create(
            "2024-11-11", extra_vals={"partner_id": cls.related_partner.id}
        )
        cls._invoice_sale_create("2024-11-12")
        sale = cls._invoice_sale_create("2024-11-13")
        cls._invoice_refund(sale, "2024-11-14")

    def _check_tax_lines(self):
        for field, result in iter(self.taxes_result.items()):
            _logger.debug("Checking tax line: %s", field)
            lines = self.model322.tax_line_ids.filtered(
                lambda x, field=field: x.field_number == int(field)
            )
            self.assertAlmostEqual(
                sum(lines.mapped("amount")),
                result,
                2,
                f"Incorrect result in field {field}",
            )

    def test_model_322(self):
        _logger.debug("Calculate AEAT 322 11 2024")
        self.model322.button_calculate()
        self.model322.env.invalidate_all()
        # Test default counterpart.
        self.assertEqual(
            self.model322.counterpart_account_id.id, self.accounts["475000"].id
        )
        self.assertEqual(self.model322.state, "calculated")
        # Fill manual fields
        self.model322.write(
            {
                "porcentaje_atribuible_estado": 95,
                "cuota_compensar": 250,
            }
        )
        if self.debug:
            self._print_tax_lines(self.model322.tax_line_ids)
        self._check_tax_lines()
        # Check result
        _logger.debug("Checking results")
        devengado = sum(
            [
                self.taxes_result.get(b, 0.0)
                for b in (
                    "161",
                    "173",
                    "3",
                    "164",
                    "6",
                    "9",
                    "152",
                    "167",
                    "11",
                    "14",
                    "155",
                    "17",
                    "20",
                    "22",
                    "24",
                    "26",
                    "158",
                    "29",
                    "170",
                    "32",
                    "35",
                    "37",
                )
            ]
        )
        deducir = sum(
            [
                self.taxes_result.get(b, 0.0)
                for b in (
                    "40",
                    "42",
                    "44",
                    "46",
                    "48",
                    "50",
                    "52",
                    "54",
                    "56",
                    "58",
                    "59",
                    "60",
                    "61",
                )
            ]
        )
        subtotal = round(devengado - deducir, 3)
        estado = round(subtotal * 0.95, 3)
        result = round(estado - 250, 3)
        self.assertAlmostEqual(self.model322.total_devengado, devengado, 2)
        self.assertAlmostEqual(self.model322.total_deducir, deducir, 2)
        self.assertAlmostEqual(self.model322.casilla_63, subtotal, 2)
        self.assertAlmostEqual(self.model322.atribuible_estado, estado, 2)
        self.assertAlmostEqual(self.model322.cuota_liquidacion, result, 2)
        self.assertAlmostEqual(
            self.model322_4t.tax_line_ids.filtered(
                lambda x: x.field_number == 80
            ).amount,
            0,
        )
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_config_xml_ids = [
            "l10n_es_aeat_mod322.aeat_mod322_2024_10_main_export_config",
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(export_to_boe._export_config(self.model322, export_config))
        with self.assertRaises(exceptions.ValidationError):
            self.model322.cuota_compensar = -250
        self.model322.button_post()
        self.assertTrue(self.model322.move_id)
        self.assertEqual(self.model322.move_id.ref, self.model322.name)
        self.assertEqual(
            self.model322.move_id.journal_id,
            self.model322.journal_id,
        )
        self.assertEqual(
            self.model322.move_id.line_ids.mapped("partner_id"),
            self.env.ref("l10n_es_aeat.res_partner_aeat"),
        )
        codes = self.model322.move_id.mapped("line_ids.account_id.code")
        self.assertIn("475000", codes)
        self.assertIn("477000", codes)
        self.assertIn("472000", codes)
        self.model322.button_unpost()
        self.assertFalse(self.model322.move_id)
        self.assertEqual(self.model322.state, "cancelled")
        self.model322.button_recover()
        self.assertEqual(self.model322.state, "draft")
        self.assertEqual(self.model322.calculation_date, False)
        self.model322.button_cancel()
        self.assertEqual(self.model322.state, "cancelled")

    # Oracle for the boxes most sensitive to core tax renames, per Orden
    # HAC/1167/2024, de 17 de octubre (BOE-A-2024-21961), applicable to the
    # 322 statements from October 2024 onwards. When AEAT publishes a new
    # format, update this dict together with data/ files and taxes_result.
    BOE_BOX_TAXES = {
        71: {
            "account_tax_template_s_iva0_g_i",
            "account_tax_template_s_iva0_sp_i",
        },
        72: {"account_tax_template_s_iva0_g_e", "account_tax_template_s_iva0"},
        93: {
            "account_tax_template_s_iva0_g_i",
            "account_tax_template_s_iva0_sp_i",
        },
        94: {"account_tax_template_s_iva0_g_e"},
    }

    def _get_mod322_map_lines(self):
        return (
            self.env["l10n.es.aeat.map.tax"]
            .sudo()
            .search([("model", "=", 322)])
            .map_line_ids
        )

    def test_map_lines_taxes_resolve(self):
        """Guardian: every mapped tax template must resolve for the company.

        Catches core template renames/removals like s_iva0_ic -> s_iva0_g_i.
        """
        for map_line in self._get_mod322_map_lines().filtered("tax_xmlid_ids"):
            self.assertTrue(
                map_line.get_taxes_for_company(self.company),
                f"Box {map_line.field_number}: mapped taxes do not resolve "
                f"({', '.join(map_line.tax_xmlid_ids.mapped('name'))})",
            )

    def test_map_box_oracle_boe_2024_10(self):
        """Guardian: hardcoded oracle that breaks on purpose when the BOE
        mapping for these boxes changes in a future format."""
        lines_by_field = {
            line.field_number: line
            for line in self._get_mod322_map_lines()
            if line.field_number in self.BOE_BOX_TAXES
        }
        for field, expected in self.BOE_BOX_TAXES.items():
            self.assertIn(field, lines_by_field)
            self.assertEqual(
                set(lines_by_field[field].tax_xmlid_ids.mapped("name")),
                expected,
                f"Box {field} mapping differs from BOE 2024-10 oracle",
            )

    def test_company_type(self):
        """The dominant company is 'D' and its dependents are 'P'."""
        self.assertEqual(self.model322.company_type, "D")
        self.assertEqual(self.model322.dominant_company_vat, "A12345674")
        group = self.env["l10n.es.aeat.mod322.group"].search(
            [("main_company_id", "=", self.company.id)]
        )
        dominant = self.env["res.company"].create({"name": "Dominant company"})
        group.write(
            {
                "main_company_id": dominant.id,
                "company_ids": [(6, 0, self.company.ids)],
            }
        )
        dependent_report = self.model322.copy(
            {
                "name": "9990000000323",
                "date_start": "2024-11-01",
                "date_end": "2024-11-30",
            }
        )
        self.assertEqual(dependent_report.company_type, "P")
        self.assertFalse(dependent_report.dominant_company_vat)

    def test_transitional_boxes_zero_from_2025(self):
        """Boxes 153-155 and 162-173 (transitional reduced rates) are 0 from
        2025 on, even if invoices use the 5%, 2% or 7.5% taxes."""
        taxes = self._get_taxes("S_IVA5B,S_IVA2B,S_IVA7-5S")
        self.assertEqual(len(taxes), 3)
        for partner in (self.customer, self.related_partner):
            invoice = self.env["account.move"].create(
                {
                    "company_id": self.company.id,
                    "partner_id": partner.id,
                    "invoice_date": "2026-11-10",
                    "move_type": "out_invoice",
                    "journal_id": self.journal_sale.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": f"Test for tax {tax.name}",
                                "account_id": self.accounts["700000"].id,
                                "price_unit": 1000,
                                "quantity": 1,
                                "tax_ids": [(6, 0, tax.ids)],
                            },
                        )
                        for tax in taxes
                    ],
                }
            )
            invoice.action_post()
            self.assertTrue(invoice.amount_tax)
        report = self.model322.copy(
            {
                "name": "9990000002026",
                "year": 2026,
                "period_type": "11",
                "date_start": "2026-11-01",
                "date_end": "2026-11-30",
            }
        )
        report.button_calculate()
        transitional = report.tax_line_ids.filtered(
            lambda x: 153 <= x.field_number <= 155 or 162 <= x.field_number <= 173
        )
        self.assertTrue(transitional)
        for line in transitional:
            self.assertFalse(line.move_line_ids, f"Box {line.field_number}")
            self.assertEqual(line.amount, 0, f"Box {line.field_number}")

    def test_resultado_liquidacion_casilla_112(self):
        """[70] = [68] - [69] - [112], with [112] only when the taxpayer is
        entitled to deduct it, and the counterpart account follows [70]."""
        self.model322.button_calculate()
        cuota = self.model322.cuota_liquidacion
        self.assertGreater(cuota, 0)
        self.assertAlmostEqual(self.model322.resultado_liquidacion, cuota, 2)
        self.model322.casilla_112 = cuota + 100
        self.assertAlmostEqual(self.model322.resultado_liquidacion, cuota, 2)
        self.assertEqual(self.model322.counterpart_account_id, self.accounts["475000"])
        self.model322.deduct_payment_petrol_delivery = True
        self.assertAlmostEqual(self.model322.resultado_liquidacion, -100, 2)
        self.assertTrue(self.model322.counterpart_account_id.code.startswith("4700"))
        with self.assertRaises(exceptions.ValidationError):
            self.model322.casilla_112 = -1

    def _create_report_2026(self, period, date_start, date_end):
        # Not a copy: export_config_id is copied and would not follow the dates
        return self.env["l10n.es.aeat.mod322.report"].create(
            {
                "name": f"9992026{period}0322",
                "company_id": self.company.id,
                "company_vat": "ESA12345674",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2026,
                "period_type": period,
                "date_start": date_start,
                "date_end": date_end,
                "journal_id": self.journal_misc.id,
            }
        )

    def _export_pages_2026(self, report):
        report.button_calculate()
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe_2026.txt"}
        )
        content = export_to_boe._export_config(report, report.export_config_id)
        content = content.decode("iso-8859-1")
        pages = {}
        for page in ("01", "02", "03"):
            match = re.search(f"<T322{page}000>.*?</T322{page}000>", content)
            pages[page] = match and match.group()
        return pages

    def test_export_boe_2026(self):
        """Format DR322e26v11 (Orden HAC/27/2026) applies from February 2026."""
        config_2024 = self.env.ref(
            "l10n_es_aeat_mod322.aeat_mod322_2024_10_main_export_config"
        )
        config_2026 = self.env.ref(
            "l10n_es_aeat_mod322.aeat_mod322_2026_02_main_export_config"
        )
        report_01 = self._create_report_2026("01", "2026-01-01", "2026-01-31")
        self.assertEqual(report_01.export_config_id, config_2024)
        report_02 = self._create_report_2026("02", "2026-02-01", "2026-02-28")
        self.assertEqual(report_02.export_config_id, config_2026)
        report_02.write({"deduct_payment_petrol_delivery": True, "casilla_112": 100})
        pages = self._export_pages_2026(report_02)
        self.assertEqual(len(pages["01"]), 1800)
        self.assertEqual(len(pages["02"]), 2300)
        self.assertFalse(pages["03"])
        # Page 1: declaration type (13) and flags (129-136), notes 3 to 8
        self.assertEqual(pages["01"][12], " ")
        self.assertEqual(pages["01"][128:136], " 1220001")
        # Page 2: [68] (120), [112] (154) and [70] = [68] - [69] - [112] (171)
        self.assertEqual(pages["02"][119:136], "00000000000000000")
        self.assertEqual(pages["02"][153:170], "00000000000010000")
        self.assertEqual(pages["02"][170:187], "N0000000000010000")
        # Last period: page 3 and the year-end flags
        report_12 = self._create_report_2026("12", "2026-12-01", "2026-12-31")
        self.assertEqual(report_12.export_config_id, config_2026)
        pages = self._export_pages_2026(report_12)
        self.assertEqual(len(pages["01"]), 1800)
        self.assertEqual(len(pages["03"]), 1600)
        self.assertEqual(pages["01"][128:136], " 1223202")


class TestL10nEsAeatMod322Map2023(TestL10nEsAeatMod322Base):
    """The 2023 map and export config must be kept for periods up to 09/2024."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model322_2023 = cls._create_report(
            "9990000000325", 2023, "01", "2023-01-01", "2023-01-31"
        )

    @classmethod
    def _create_report(cls, name, year, period_type, date_start, date_end):
        return cls.env["l10n.es.aeat.mod322.report"].create(
            {
                "name": name,
                "company_id": cls.company.id,
                "company_vat": "ESA12345674",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": year,
                "period_type": period_type,
                "date_start": date_start,
                "date_end": date_end,
                "journal_id": cls.journal_misc.id,
            }
        )

    def _get_map_for_report(self, report):
        """Reuse the same map search than the one done in ``calculate``."""
        return (
            self.env["l10n.es.aeat.map.tax"]
            .sudo()
            .with_context(active_test=False)
            .search(
                [
                    ("model", "=", report.number),
                    "|",
                    ("date_from", "<=", report.date_start),
                    ("date_from", "=", False),
                    "|",
                    ("date_to", ">=", report.date_end),
                    ("date_to", "=", False),
                ],
                limit=1,
            )
        )

    def test_2023_map_and_export_config_dates(self):
        map_2023 = self.env.ref("l10n_es_aeat_mod322.aeat_mod322_2023_map")
        self.assertEqual(map_2023.date_from, fields.Date.to_date("2023-01-01"))
        self.assertEqual(map_2023.date_to, fields.Date.to_date("2024-09-30"))
        export_config = self.env.ref(
            "l10n_es_aeat_mod322.aeat_mod322_2023_main_export_config"
        )
        self.assertEqual(export_config.date_start, fields.Date.to_date("2023-01-01"))
        self.assertEqual(export_config.date_end, fields.Date.to_date("2024-09-30"))

    def test_2023_map_lines(self):
        map_2023 = self.env.ref("l10n_es_aeat_mod322.aeat_mod322_2023_map")
        self.assertEqual(len(map_2023.map_line_ids), 76)
        for xmlid in (
            "aeat_mod322_2023_map_line_10_purchase",
            "aeat_mod322_2023_map_line_21",
            "aeat_mod322_2023_map_line_22",
            "aeat_mod322_2023_map_line_42",
            "aeat_mod322_2023_map_line_48",
            "aeat_mod322_2023_map_line_50",
            "aeat_mod322_2023_map_line_61",
        ):
            line = self.env.ref(f"l10n_es_aeat_mod322.{xmlid}")
            self.assertEqual(line.map_parent_id, map_2023)

    def test_2023_report_calculates_with_2023_map(self):
        map_2023 = self.env.ref("l10n_es_aeat_mod322.aeat_mod322_2023_map")
        self.model322_2023.calculate()
        self.env.invalidate_all()
        self.assertEqual(len(self.model322_2023.tax_line_ids), 76)
        self.assertEqual(
            self.model322_2023.tax_line_ids.map_line_id.map_parent_id, map_2023
        )

    def test_period_selects_map_and_export_config(self):
        map_2023 = self.env.ref("l10n_es_aeat_mod322.aeat_mod322_2023_map")
        map_2024_10 = self.env.ref("l10n_es_aeat_mod322.aeat_mod322_2024_10_map")
        config_2023 = self.env.ref(
            "l10n_es_aeat_mod322.aeat_mod322_2023_main_export_config"
        )
        config_2024_10 = self.env.ref(
            "l10n_es_aeat_mod322.aeat_mod322_2024_10_main_export_config"
        )
        report_09 = self._create_report(
            "9990900000322", 2024, "09", "2024-09-01", "2024-09-30"
        )
        report_10 = self._create_report(
            "9991000000322", 2024, "10", "2024-10-01", "2024-10-31"
        )
        self.assertEqual(self._get_map_for_report(report_09), map_2023)
        self.assertEqual(self._get_map_for_report(report_10), map_2024_10)
        self.assertEqual(report_09.export_config_id, config_2023)
        self.assertEqual(report_10.export_config_id, config_2024_10)
        self.assertEqual(
            report_09._get_export_config(report_09.date_start), config_2023
        )
        self.assertEqual(
            report_10._get_export_config(report_10.date_start), config_2024_10
        )


class TestL10nEsAeatMod322CompanyInfo(TestL10nEsAeatMod322Base):
    """``calculate`` must refresh the stored company info.

    These stored fields are only triggered by ``company_id``, so a group
    created or modified after the report would otherwise stay stale.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.second_company = (
            cls.env["res.company"]
            .with_context(no_vat_validation=True)
            .create({"name": "Dominant company", "vat": "ESB98765432"})
        )
        cls.related_partner = cls.env["res.partner"].create({"name": "Related company"})

    def _create_group(self):
        return self.env["l10n.es.aeat.mod322.group"].create(
            {
                "name": "IVA/2024/24",
                "main_company_id": self.second_company.id,
                "company_ids": [(6, 0, self.company.ids)],
                "vinculated_partner_ids": [(6, 0, self.related_partner.ids)],
            }
        )

    def test_calculate_refreshes_company_info(self):
        # The report was created before the group, so its info is stale.
        self.assertEqual(self.model322.company_type, "D")
        self.assertFalse(self.model322.group_number)
        group = self._create_group()
        self.assertEqual(self.model322.company_type, "D")
        self.assertFalse(self.model322.group_number)
        self.model322.calculate()
        self.env.invalidate_all()
        self.assertEqual(self.model322.company_type, "P")
        self.assertEqual(self.model322.group_number, group.name)
        self.assertEqual(self.model322.dominant_company_vat, "B98765432")
        self.assertEqual(
            self.model322.vinculated_partner_ids,
            self.second_company.partner_id
            | self.company.partner_id
            | self.related_partner,
        )
        # The report company becomes the dominant one again.
        group.write(
            {
                "main_company_id": self.company.id,
                "company_ids": [(6, 0, [])],
            }
        )
        self.model322.calculate()
        self.env.invalidate_all()
        self.assertEqual(self.model322.company_type, "D")
        self.assertEqual(self.model322.dominant_company_vat, "A12345674")

    def test_calculate_refreshes_company_info_in_batch(self):
        self._create_group()
        reports = self.model322 | self.model322_4t
        reports.calculate()
        self.env.invalidate_all()
        for report in reports:
            self.assertEqual(report.company_type, "P")
            self.assertEqual(report.dominant_company_vat, "B98765432")
