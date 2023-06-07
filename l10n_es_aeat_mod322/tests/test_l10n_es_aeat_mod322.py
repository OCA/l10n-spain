# Copyright 2016-2019 Tecnativa - Pedro M. Baeza
# Copyright 2022 QubiQ - Jan Tugores
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging

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
        "l10n_es_aeat_mod322.account_tax_template_s_iva4b_intragroup": (100, 4),
        "l10n_es_aeat_mod322.account_tax_template_s_iva4s_intragroup": (200, 8),
        "S_IVA10B": (1200, 120),
        "S_IVA10B//neg": (-120, -12),
        "S_IVA10S": (1300, 130),
        "l10n_es_aeat_mod322.account_tax_template_s_iva10b_intragroup": (100, 10),
        "l10n_es_aeat_mod322.account_tax_template_s_iva10s_intragroup": (200, 20),
        "S_IVA21B": (1400, 294),
        "S_IVA21B//neg": (-140, -29.4),
        "S_IVA21S": (1500, 315),
        "S_IVA21ISP": (1600, 336),
        "l10n_es_aeat_mod322.account_tax_template_s_iva21b_intragroup": (100, 21),
        "l10n_es_aeat_mod322.account_tax_template_s_iva21s_intragroup": (200, 42),
        "S_REQ05": (1700, 8.5),
        "S_REQ014": (1800, 25.2),
        "S_REQ52": (1900, 98.8),
        "S_IVA0_E": (2000, 0),
        "S_IVA_E": (2100, 0),
        "S_IVA_NS": (2200, 0),
        "S_IVA0_ISP": (2300, 0),
        "S_IVA0_IC": (2400, 0),
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
        "l10n_es_aeat_mod322.account_tax_template_p_iva4_bc_intragroup": (100, 4),
        "l10n_es_aeat_mod322.account_tax_template_p_iva10_bc_intragroup": (100, 10),
        "l10n_es_aeat_mod322.account_tax_template_p_iva21_bc_intragroup": (100, 21),
        "l10n_es_aeat_mod322.account_tax_template_p_iva4_sc_intragroup": (200, 8),
        "l10n_es_aeat_mod322.account_tax_template_p_iva10_sc_intragroup": (200, 20),
        "l10n_es_aeat_mod322.account_tax_template_p_iva21_sc_intragroup": (200, 42),
        "l10n_es_aeat_mod322.account_tax_template_p_iva4_bi_intragroup": (300, 12),
        "l10n_es_aeat_mod322.account_tax_template_p_iva10_bi_intragroup": (300, 30),
        "l10n_es_aeat_mod322.account_tax_template_p_iva21_bi_intragroup": (300, 63),
    }
    taxes_result = {
        # Operaciones intragrupo - Base imponible 4%
        "1": (3 * 100) + (3 * 200),
        # Operaciones intragrupo - Cuota 4%
        "3": (3 * 4) + (3 * 8),
        # Operaciones intragrupo - Base imponible 10%
        "4": (3 * 100) + (3 * 200),
        # Operaciones intragrupo - Cuota 10%
        "6": (3 * 10) + (3 * 20),
        # Operaciones intragrupo - Base imponible 21%
        "7": (3 * 100) + (3 * 200),
        # Operaciones intragrupo - Cuota 21%
        "9": (3 * 21) + (3 * 42),
        # Modificación bases y cuotas de operaciones intragrupo - Base imponible
        "10": (-1) * ((3 * 100) + (3 * 200)),
        # Modificación bases y cuotas de operaciones intragrupo - Cuota
        "11": (-1) * (1 * 105),
        # Régimen General - Base imponible 4%
        "12": (3 * 1000) + (3 * 1100) - 3 * 100,  # S_IVA4B, S_IVA4S
        # Régimen General - Cuota 4%
        "14": (3 * 40) + (3 * 44) - 3 * 4,  # S_IVA4B, S_IVA4S
        # Régimen General - Base imponible 10%
        "15": (3 * 1200) + (3 * 1300) - 3 * 120,  # S_IVA10B, S_IVA10S
        # Régimen General - Cuota 10%
        "17": (3 * 120) + (3 * 130) - 3 * 12,  # S_IVA10B, S_IVA10S
        # Régimen General - Base imponible 21%
        # S_IVA21B, S_IVA21S, S_IVA21ISP
        "18": (3 * 1400) + (3 * 1500) + (3 * 1600) - 3 * 140,
        # Régimen General - Cuota 21%
        # S_IVA21B, S_IVA21S, S_IVA21ISP
        "20": (3 * 294) + (3 * 315) + (3 * 336) - 3 * 29.4,
        # Adq. intracomunitarias de bienes y servicios - Base
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
                + 1600
                - 140
                + 100  # S_IVA21B,S_IVA21S,S_IVA21ISP
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
                + 336
                - 29.4
                + 4  # S_IVA21B, S_IVA21S, S_IVA21ISP
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
        "36": (1700 + 1800 + 1900),  # S_REQ05, S_REQ014, S_REQ52
        # Mod. bases y cuotas del recargo de equivalencia - Cuota
        "37": (8.5 + 25.2 + 98.8),  # S_REQ05, S_REQ014, S_REQ52
        # Por cuotas soportadas en operaciones intragrupo corrientes - Base
        "39": ((3 * 100) + (3 * 100) + (3 * 100) + (3 * 200) + (3 * 200) + (3 * 200)),
        # Por cuotas soportadas en operaciones intragrupo corrientes - Cuota
        "40": ((3 * 4) + (3 * 10) + (3 * 21) + (3 * 8) + (3 * 20) + (3 * 42)),
        # Por cuotas soportadas en operaciones intragrupo con bienes de inversión - Base
        "41": ((3 * 300) + (3 * 300) + (3 * 300)),
        # Por cuotas soportadas en operaciones intragrupo con bienes de inversión - Cuota
        "42": ((3 * 12) + (3 * 30) + (3 * 63)),
        # Rectificación de deducciones por operaciones intragrupo - Base
        "43": ((-1) * (100 + 100 + 100 + 200 + 200 + 200 + 300 + 300 + 300)),
        # Rectificación de deducciones por operaciones intragrupo - Cuota
        "44": ((-1) * (4 + 10 + 21 + 8 + 20 + 42 + 12 + 30 + 63)),
        # Cuotas soportadas en op. int. corrientes - Base
        "45": (
            (3 * 110)
            + (3 * 120)
            + (3 * 130)
            + (3 * 140)  # P_IVAx_SP_EX_2
            + (3 * 150)
            + (3 * 160)
            + (3 * 210)  # P_IVAx_ISP_1
            + (3 * 220)
            + (3 * 230)
            + (3 * -21)
            + (3 * -22)
            + (3 * -23)
            + (3 * 240)  # P_IVAx_SC
            + (3 * 250)
            + (3 * 260)
            + (3 * 270)  # P_IVAx_BC
            + (3 * 280)
            + (3 * 290)  # P_REQ05, P_REQ014, P_REQ5.2
        ),
        # Cuotas soportadas en op. int. corrientes - Cuota
        "46": (
            (3 * 4.4)
            + (3 * 12)
            + (3 * 27.3)
            + (3 * 5.6)  # P_IVAx_SP_EX_2
            + (3 * 15)
            + (3 * 33.6)
            + (3 * 8.4)  # P_IVAx_ISP_1
            + (3 * 22)
            + (3 * 48.3)
            + (3 * -0.84)
            + (3 * -2.2)
            + (3 * -4.83)
            + (3 * 9.6)  # P_IVAx_SC
            + (3 * 25)
            + (3 * 54.6)
            + (3 * 1.35)  # P_IVAx_BC
            + (3 * 3.92)
            + (3 * 15.08)  # P_REQ05, P_REQ014  # P_REQ5.2
        ),
        # Cuotas soportadas en op. int. bienes de inversión - Base
        "47": (3 * 310) + (3 * 320) + (3 * 330),  # P_IVAx_BI
        # Cuotas soportadas en op. int. bienes de inversión - Cuota
        "48": (3 * 12.4) + (3 * 32) + (3 * 69.3),  # P_IVAx_BI
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
        # Rectificación de deducciones - Base
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
        # Rectificación de deducciones - Cuota
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
        "71": (2 * 2400) + (2 * 2500),  # S_IVA0_IC, S_IVA0_SP_I
        # Exportaciones y operaciones asimiladas - Base ventas
        "72": (2 * 2000) + (2 * 2200) + (2 * 2600),
        # S_IVA0_E + S_IVA_NS + S_IVA0
        # Importes de las entregas de bienes y prestaciones de servicios
        # a las que habiéndoles sido aplicado el régimen especial del
        # criterio de caja hubieran resultado devengadas conforme a la regla
        # general de devengo contenida en el art. 75 LIVA - Base imponible
        "74": 0,
        # Importes de las entregas de bienes y prestaciones de servicios
        # a las que habiéndoles sido aplicado el régimen especial del
        # criterio de caja hubieran resultado devengadas conforme a la regla
        # general de devengo contenida en el art. 75 LIVA - Cuota
        "75": 0,
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create model
        cls.model322 = cls.env["l10n.es.aeat.mod322.report"].create(
            {
                "name": "9990000000322",
                "company_id": cls.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2022,
                "period_type": "1T",
                "date_start": "2022-01-01",
                "date_end": "2022-03-31",
                "journal_id": cls.journal_misc.id,
                "company_type": "D",
            }
        )
        cls.model322_4t = cls.model322.copy(
            {
                "name": "9994000000322",
                "period_type": "4T",
                "date_start": "2022-09-01",
                "date_end": "2022-12-31",
                "company_type": "D",
            }
        )


class TestL10nEsAeatMod322(TestL10nEsAeatMod322Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Purchase invoices
        cls._invoice_purchase_create("2022-01-01")
        cls._invoice_purchase_create("2022-01-02")
        purchase = cls._invoice_purchase_create("2022-01-03")
        cls._invoice_refund(purchase, "2022-01-18")
        # Sale invoices
        cls._invoice_sale_create("2022-01-11")
        cls._invoice_sale_create("2022-01-12")
        sale = cls._invoice_sale_create("2022-01-13")
        cls._invoice_refund(sale, "2022-01-14")

    def _check_tax_lines(self):
        for field, result in iter(self.taxes_result.items()):
            _logger.debug("Checking tax line: %s" % field)
            lines = self.model322.tax_line_ids.filtered(
                lambda x: x.field_number == int(field)
            )
            self.assertAlmostEqual(
                sum(lines.mapped("amount")),
                result,
                2,
                "Incorrect result in field %s" % field,
            )

    def test_model_322(self):
        _logger.debug("Calculate AEAT 322 1T 2022")
        self.model322.button_calculate()
        # Test default counterpart.
        self.assertEqual(
            self.model322.counterpart_account_id.id, self.accounts["475000"].id
        )
        self.assertEqual(self.model322.state, "calculated")
        # Fill manual fields
        self.model322.write(
            {
                "state_percentage_attributable": 95,
                "state_attributable": 250,
                "field_66": 250,
                "field_77": 455,
            }
        )
        if self.debug:
            self._print_tax_lines(self.model322.tax_line_ids)
        self._check_tax_lines()
        # Check result
        _logger.debug("Checking results")
        devengado = sum(
            self.taxes_result.get(b, 0.0)
            for b in (
                "3",
                "6",
                "9",
                "11",
                "14",
                "17",
                "20",
                "22",
                "24",
                "26",
                "29",
                "32",
                "35",
                "37",
            )
        )
        deducir = sum(
            self.taxes_result.get(b, 0.0)
            for b in ("40", "42", "44", "46", "48", "50", "52", "54", "56", "58")
        )
        subtotal = round(devengado - deducir, 3)
        estado = round(subtotal * 0.95, 3)
        result = round(estado + 455 - 250, 3)
        self.assertAlmostEqual(self.model322.total_earned, devengado, 2)
        self.assertAlmostEqual(self.model322.total_to_deduct, deducir, 2)
        self.assertAlmostEqual(self.model322.field_63, subtotal, 2)
        self.assertAlmostEqual(self.model322.state_attributable, estado, 2)
        self.assertAlmostEqual(self.model322.selfsettlement_result, result, 2)
        self.assertAlmostEqual(
            self.model322_4t.tax_line_ids.filtered(
                lambda x: x.field_number == 80
            ).amount,
            0,
        )
        self.assertEqual(self.model322.result_type, "I")
        # Export to BOE
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_config_xml_ids = [
            "l10n_es_aeat_mod322.aeat_mod322_main_export_config",
        ]
        for xml_id in export_config_xml_ids:
            export_config = self.env.ref(xml_id)
            self.assertTrue(export_to_boe._export_config(self.model322, export_config))
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
        # Check 4T without exonerated
        self.model322_4t.button_calculate()
        self.assertAlmostEqual(
            self.model322_4t.tax_line_ids.filtered(
                lambda x: x.field_number == 80
            ).amount,
            0,
        )
        # Check 4T with exonerated
        self.model322_4t.exonerated_390 = "1"
        self.model322_4t.button_calculate()
        # Check change of period type
        self.model322_4t.period_type = "1T"
        self.assertEqual(self.model322_4t.exonerated_390, "2")
