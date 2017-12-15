# Copyright 2016 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import \
    TestL10nEsAeatModBase
from odoo import exceptions

_logger = logging.getLogger('aeat.303')


class TestL10nEsAeatMod303Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        'S_IVA4B': (1000, 40),
        'S_IVA4S': (1100, 44),
        'S_IVA10B': (1200, 120),
        'S_IVA10S': (1300, 130),
        'S_IVA21B': (1400, 294),
        'S_IVA21S': (1500, 315),
        'S_IVA21ISP': (1600, 336),
        'S_REQ05': (1700, 8.5),
        'S_REQ014': (1800, 25.2),
        'S_REQ52': (1900, 98.8),
        'S_IVA0_E': (2000, 0),
        'S_IVA_SP_E': (2100, 0),
        'S_IVA_NS': (2200, 0),
        'S_IVA0_ISP': (2300, 0),
        'S_IVA0_IC': (2400, 0),
        'S_IVA0_SP_I': (2500, 0),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        'P_IVA4_IC_BC': (100, 0),
        'P_IVA10_IC_BC': (200, 0),
        'P_IVA21_IC_BC': (300, 0),
        'P_IVA4_SP_IN': (400, 0),
        'P_IVA10_SP_IN': (500, 0),
        'P_IVA21_SP_IN': (600, 0),
        'P_IVA4_IC_BI': (700, 0),
        'P_IVA10_IC_BI': (800, 0),
        'P_IVA21_IC_BI': (900, 0),
        'P_IVA4_SP_EX': (110, 0),
        'P_IVA10_SP_EX': (120, 0),
        'P_IVA21_SP_EX': (130, 0),
        'P_IVA4_ISP': (140, 0),
        'P_IVA10_ISP': (150, 0),
        'P_IVA21_ISP': (160, 0),
        'P_IVA4_SC': (210, 8.4),
        'P_IVA10_SC': (220, 22),
        'P_IVA21_SC': (230, 48.3),
        'P_IVA4_BC': (240, 9.6),
        'P_IVA10_BC': (250, 25),
        'P_IVA21_BC': (260, 54.6),
        'P_REQ05': (270, 1.35),
        'P_REQ014': (280, 3.92),
        'P_REQ5.2': (290, 15.08),
        'P_IVA4_BI': (310, 12.4),
        'P_IVA10_BI': (320, 32),
        'P_IVA21_BI': (330, 69.3),
        'P_IVA4_IBC': (340, 13.6),
        'P_IVA10_IBC': (350, 35),
        'P_IVA21_IBC': (360, 75.6),
        'P_IVA4_IBI': (370, 14.8),
        'P_IVA10_IBI': (380, 38),
        'P_IVA21_IBI': (390, 81.9),
        # 'P_IVA12_AGR': (410, 49.2),
    }
    taxes_result = {
        # Régimen General - Base imponible 4%
        '1': (3 * 1000) + (3 * 1100),  # S_IVA4B, S_IVA4S
        # Régimen General - Cuota 4%
        '3': (3 * 40) + (3 * 44),  # S_IVA4B, S_IVA4S
        # Régimen General - Base imponible 10%
        '4': (3 * 1200) + (3 * 1300),  # S_IVA10B, S_IVA10S
        # Régimen General - Cuota 10%
        '6': (3 * 120) + (3 * 130),  # S_IVA10B, S_IVA10S
        # Régimen General - Base imponible 21%
        '7': (3 * 1400) + (3 * 1500) + (3 * 1600),  # S_IVA21B, S_IVA21S,
                                                    # S_IVA21ISP
        # Régimen General - Cuota 21%
        '9': (3 * 294) + (3 * 315) + (3 * 336),  # S_IVA21B, S_IVA21S,
                                                 # S_IVA21ISP
        # Adq. intracomunitarias de bienes y servicios - Base
        '10': (
            (3 * 100) + (3 * 200) + (3 * 300) +  # P_IVAx_IC_BC_2
            (3 * 400) + (3 * 500) + (3 * 600) +  # P_IVAx_SP_IN_1
            (3 * 700) + (3 * 800) + (3 * 900)    # P_IVAx_IC_BI_2
        ),
        # Adq. intracomunitarias de bienes y servicios - Cuota
        '11': (
            (3 * 4) + (3 * 20) + (3 * 63) +    # P_IVAx_IC_BC_2
            (3 * 16) + (3 * 50) + (3 * 126) +  # P_IVAx_SP_IN_1
            (3 * 28) + (3 * 80) + (3 * 189)    # P_IVAx_IC_BI_2
        ),
        # Op. inv. del suj. pasivo (excepto adq. intracom.) - Base
        '12': (
            (3 * 110) + (3 * 120) + (3 * 130) +  # P_IVAx_SP_EX_1
            (3 * 140) + (3 * 150) + (3 * 160)    # P_IVAx_ISP_2
        ),
        # Op. inv. del suj. pasivo (excepto adq. intracom.) - Cuota
        '13': (
            (3 * 4.4) + (3 * 12) + (3 * 27.3) +  # P_IVAx_SP_EX_1
            (3 * 5.6) + (3 * 15) + (3 * 33.6)    # P_IVAx_ISP_2
        ),
        # Modificación bases y cuotas - Base (Compras y ventas)
        '14': (
            (-1) * (1000 + 1100 +  # S_IVA4B, S_IVA4S
                    1200 + 1300 +  # S_IVA10B, S_IVA10S
                    1400 + 1500 + 1600 +  # S_IVA21B, S_IVA21S, S_IVA21ISP
                    100 + 200 + 300 +  # P_IVAx_IC_BC_2
                    400 + 500 + 600 +  # P_IVAx_SP_IN_1
                    700 + 800 + 900 +  # P_IVAx_IC_BI_2
                    110 + 120 + 130 +  # P_IVAx_SP_EX_1
                    140 + 150 + 160)   # P_IVAx_ISP_2
        ),
        # Modificación bases y cuotas - Cuota (Compras y ventas)
        '15': (
            (-1) * (40 + 44 +    # S_IVA4B, S_IVA4S
                    120 + 130 +  # S_IVA10B, S_IVA10S
                    294 + 315 + 336 +  # S_IVA21B, S_IVA21S, S_IVA21ISP
                    4 + 20 + 63 +      # P_IVAx_IC_BC_2
                    16 + 50 + 126 +    # P_IVAx_SP_IN_1
                    28 + 80 + 189 +    # P_IVAx_IC_BI_2
                    4.4 + 12 + 27.3 +  # P_IVAx_SP_EX_1
                    5.6 + 15 + 33.6)   # P_IVAx_ISP_2
        ),
        # Recargo equivalencia - Base imponible 0.5%
        '16': (3 * 1700),  # S_REQ05
        # Recargo equivalencia - Cuota 0.5%
        '18': (3 * 8.5),  # S_REQ05
        # Recargo equivalencia - Base imponible 1.4%
        '19': (3 * 1800),  # S_REQ014
        # Recargo equivalencia - Cuota 1.4%
        '21': (3 * 25.2),  # S_REQ014
        # Recargo equivalencia - Base imponible 5.2%
        '22': (3 * 1900),  # S_REQ52
        # Recargo equivalencia - Cuota 5.2%
        '24': (3 * 98.8),  # S_REQ52
        # Mod. bases y cuotas del recargo de equivalencia - Base
        '25': (-1) * (1700 + 1800 + 1900),  # S_REQ05, S_REQ014, S_REQ52
        # Mod. bases y cuotas del recargo de equivalencia - Cuota
        '26': (-1) * (8.5 + 25.2 + 98.8),  # S_REQ05, S_REQ014, S_REQ52
        # Cuotas soportadas en op. int. corrientes - Base
        '28': (
            (3 * 110) + (3 * 120) + (3 * 130) +  # P_IVAx_SP_EX_2
            (3 * 140) + (3 * 150) + (3 * 160) +  # P_IVAx_ISP_1
            (3 * 210) + (3 * 220) + (3 * 230) +  # P_IVAx_SC
            (3 * 240) + (3 * 250) + (3 * 260) +  # P_IVAx_BC
            (3 * 270) + (3 * 280) + (3 * 290)    # P_REQ05, P_REQ014, P_REQ5.2
        ),
        # Cuotas soportadas en op. int. corrientes - Cuota
        '29': (
            (3 * 4.4) + (3 * 12) + (3 * 27.3) +  # P_IVAx_SP_EX_2
            (3 * 5.6) + (3 * 15) + (3 * 33.6) +  # P_IVAx_ISP_1
            (3 * 8.4) + (3 * 22) + (3 * 48.3) +  # P_IVAx_SC
            (3 * 9.6) + (3 * 25) + (3 * 54.6) +  # P_IVAx_BC
            (3 * 1.35) + (3 * 3.92) +            # P_REQ05, P_REQ014
            (3 * 15.08)                          # P_REQ5.2
        ),
        # Cuotas soportadas en op. int. bienes de inversión - Base
        '30': (3 * 310) + (3 * 320) + (3 * 330),  # P_IVAx_BI
        # Cuotas soportadas en op. int. bienes de inversión - Cuota
        '31': (3 * 12.4) + (3 * 32) + (3 * 69.3),  # P_IVAx_BI
        # Cuotas soportadas en las imp. bienes corrientes - Base
        '32': (3 * 340) + (3 * 350) + (3 * 360),  # P_IVAx_IBC
        # Cuotas soportadas en las imp. bienes corrientes - Cuota
        '33': (3 * 13.6) + (3 * 35) + (3 * 75.6),  # P_IVAx_IBC
        # Cuotas soportadas en las imp. bienes de inversión - Base
        '34': (3 * 370) + (3 * 380) + (3 * 390),  # P_IVAx_IBI
        # Cuotas soportadas en las imp. bienes de inversión - Cuota
        '35': (3 * 14.8) + (3 * 38) + (3 * 81.9),  # P_IVAx_IBI
        # En adq. intra. de bienes y servicios corrientes - Base
        '36': (
            (3 * 100) + (3 * 200) + (3 * 300) +  # P_IVAx_IC_BC_1
            (3 * 400) + (3 * 500) + (3 * 600)    # P_IVAx_SP_IN_2
        ),
        # En adq. intra. de bienes y servicios corrientes - Cuota
        '37': (
            (3 * 4) + (3 * 20) + (3 * 63) +  # P_IVAx_IC_BC_1
            (3 * 16) + (3 * 50) + (3 * 126)  # P_IVAx_SP_IN_2
        ),
        # En adq. intra. de bienes de inversión - Base
        '38': (3 * 700) + (3 * 800) + (3 * 900),  # P_IVAx_IC_BI_1
        # En adq. intra. de bienes de inversión - Cuota
        '39': (3 * 28) + (3 * 80) + (3 * 189),  # P_IVAx_IC_BI_1
        # Rectificación de deducciones - Base
        '40': ((-1) * (
            270 + 280 + 290 +  # P_REQ05, P_REQ014, P_REQ5.2
            240 + 250 + 260 +  # P_IVAx_BC
            210 + 220 + 230 +  # P_IVAx_SC
            310 + 320 + 330 +  # P_IVAx_BI
            340 + 350 + 360 +  # P_IVAx_IBC
            370 + 380 + 390 +  # P_IVAx_IBI
            100 + 200 + 300 +  # P_IVAx_IC_BC_1
            700 + 800 + 900 +  # P_IVAx_IC_BI_1
            400 + 500 + 600 +  # P_IVAx_SP_IN_2
            110 + 120 + 130 +  # P_IVAx_SP_EX_2
            140 + 150 + 160    # P_IVAx_ISP_1
        )),
        # Rectificación de deducciones - Cuota
        '41': ((-1) * (
            1.35 + 3.92 + 15.08 +  # P_REQ05, P_REQ014, P_REQ5.2
            9.6 + 25 + 54.6 +      # P_IVAx_BC
            8.4 + 22 + 48.3 +      # P_IVAx_SC
            12.4 + 32 + 69.3 +     # P_IVAx_BI
            13.6 + 35 + 75.6 +     # P_IVAx_IBC
            14.8 + 38 + 81.9 +     # P_IVAx_IBI
            4 + 20 + 63 +          # P_IVAx_IC_BC_1
            28 + 80 + 189 +        # P_IVAx_IC_BI_1
            16 + 50 + 126 +        # P_IVAx_SP_IN_2
            4.4 + 12 + 27.3 +      # P_IVAx_SP_EX_2
            5.6 + 15 + 33.6        # P_IVAx_ISP_1
        )),
        # Compensaciones Rég. especial A. G. y P. - Cuota compras
        '42': 0,
        # Regularización bienes de inversión
        '43': 0,
        # Regularización por aplicación del porcentaje definitivo de prorrata
        '44': 0,
        # Entregas intra. de bienes y servicios - Base ventas
        '59': (2 * 2400) + (2 * 2500),  # S_IVA0_IC, S_IVA0_SP_I
        # Exportaciones y operaciones asimiladas - Base ventas
        '60': (2 * 2000),  # S_IVA0_E
        # Op. no sujetas o con inv. del sujeto pasivo - Base ventas
        '61': ((2 * 2100) + (2 * 2200) +   # S_IVA_SP_E, S_IVA_NS
               (2 * 2300)),                # S_IVA0_ISP
        # Importes de las entregas de bienes y prestaciones de servicios
        # a las que habiéndoles sido aplicado el régimen especial del
        # criterio de caja hubieran resultado devengadas conforme a la regla
        # general de devengo contenida en el art. 75 LIVA - Base imponible
        '62': 0,
        # Importes de las entregas de bienes y prestaciones de servicios
        # a las que habiéndoles sido aplicado el régimen especial del
        # criterio de caja hubieran resultado devengadas conforme a la regla
        # general de devengo contenida en el art. 75 LIVA - Cuota
        '63': 0,
        # Importe de las adquisiciones de bienes y servicios a las que sea
        # de aplicación o afecte el régimen especial del criterio de caja
        # conforme a la ley general de devengo contenida en el artículo
        # 75 de LIVA - Base imponible
        '74': 0,
        # Importe de las adquisiciones de bienes y servicios a las que sea
        # de aplicación o afecte el régimen especial del criterio de caja
        # conforme a la ley general de devengo contenida en el artículo
        # 75 de LIVA - Cuota
        '75': 0,
    }

    def test_model_303(self):
        # Purchase invoices
        self._invoice_purchase_create('2017-01-01')
        self._invoice_purchase_create('2017-01-02')
        purchase = self._invoice_purchase_create('2017-01-03')
        self._invoice_refund(purchase, '2017-01-18')
        # Sale invoices
        self._invoice_sale_create('2017-01-11')
        self._invoice_sale_create('2017-01-12')
        sale = self._invoice_sale_create('2017-01-13')
        self._invoice_refund(sale, '2017-01-14')
        # Create model
        export_config = self.env.ref(
            'l10n_es_aeat_mod303.aeat_mod303_main_export_config')
        model303_new = self.env['l10n.es.aeat.mod303.report'].new({
            'name': '9990000000303',
            'company_id': self.company.id,
            'company_vat': '1234567890',
            'contact_name': 'Test owner',
            'type': 'N',
            'support_type': 'T',
            'contact_phone': '911234455',
            'year': 2017,
            'period_type': '1T',
            'date_start': '2017-01-01',
            'date_end': '2017-03-31',
            'export_config_id': export_config.id,
            'journal_id': self.journal_misc.id,
            'counterpart_account_id': self.accounts['475000'].id
        })
        self.assertEqual(model303_new.company_id, self.company.id)
        self.assertEqual(model303_new.counterpart_account_id,
                         self.accounts['475000'].id)
        self.assertEqual(model303_new.journal_id,
                         self.journal_misc.id)
        self.model303 = self.env[
            'l10n.es.aeat.mod303.report'].create(
            model303_new._convert_to_write(model303_new._cache))

        _logger.debug('Calculate AEAT 303 1T 2017')
        self.model303.button_calculate()
        # Fill manual fields
        self.model303.write({
            # % atribuible al Estado
            'porcentaje_atribuible_estado': 95,
            # Cuotas a compensar
            'cuota_compensar': 250,
            # Iva Diferido (Liquidado por aduana)
            'casilla_77': 455,
        })
        if self.debug:
            self._print_tax_lines(self.model303.tax_line_ids)
        # Check tax lines
        for box, result in self.taxes_result.items():
            _logger.debug('Checking tax line: %s' % box)
            lines = self.model303.tax_line_ids.filtered(
                lambda x: x.field_number == int(box))
            self.assertAlmostEqual(sum(lines.mapped('amount')), result, 2)
        # Check result
        _logger.debug('Checking results')
        devengado = sum([self.taxes_result.get(b, 0.) for b in (
            '3', '6', '9', '11', '13', '15', '18', '21', '24', '26')])
        deducir = sum([self.taxes_result.get(b, 0.) for b in (
            '29', '31', '33', '35', '37', '39', '41', '42', '43', '44')])
        subtotal = round(devengado - deducir, 3)
        estado = round(subtotal * 0.95, 3)
        result = round(estado + 455 - 250, 3)
        self.assertAlmostEqual(self.model303.total_devengado, devengado, 2)
        self.assertAlmostEqual(self.model303.total_deducir, deducir, 2)
        self.assertAlmostEqual(self.model303.casilla_46, subtotal, 2)
        self.assertAlmostEqual(self.model303.atribuible_estado, estado, 2)
        self.assertAlmostEqual(self.model303.casilla_69, result, 2)
        self.assertAlmostEqual(self.model303.resultado_liquidacion, result, 2)
        self.assertEqual(self.model303.result_type, 'I')
        self.assertTrue(self.model303.allow_posting)
        with self.assertRaises(exceptions.ValidationError):
            self.model303.cuota_compensar = -250
