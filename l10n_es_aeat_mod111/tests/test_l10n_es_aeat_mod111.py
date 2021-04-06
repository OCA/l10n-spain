# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

import logging

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.111")


class TestL10nEsAeatMod111Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IRPF21T": (1000, 150),
        "P_IRPF21TD": (2000, 300),
        "P_IRPF21TE": (3000, 450),
        "P_IRPF1": (4000, 40),
        "P_IRPF2": (5000, 100),
        "P_IRPF7": (6000, 420),
        "P_IRPF9": (7000, 630),
        "P_IRPF15": (8000, 1200),
        "P_IRPF18": (9000, 1620),
        "P_IRPF19": (100, 19),
        "P_IRPF20": (200, 40),
        "P_IRPF21P": (300, 63),
        "P_IRPF24": (400, 96),
    }
    taxes_result = {
        # Rendimientos del trabajo (dinerarios) - Base
        "2": (2 * 1000) + (2 * 2000),  # P_IRPF21T, P_IRPF21TD
        # Rendimientos del trabajo (dinerarios) - Retenciones
        "3": (2 * 150) + (2 * 300),  # P_IRPF21T, P_IRPF21TD
        # Rendimientos del trabajo (en especie) - Base
        "5": (2 * 3000),  # P_IRPF21TE
        # Rendimientos del trabajo (en especie) - Retenciones
        "6": (2 * 450),  # P_IRPF21TE
        # Rendimientos de actividades económicas (dinerarios) - Base
        "8": (
            (2 * 4000)  # P_IRPF1
            + (2 * 5000)  # P_IRPF2
            + (2 * 6000)  # P_IRPF7
            + (2 * 7000)  # P_IRPF9
            + (2 * 8000)  # P_IRPF15
            + (2 * 9000)  # P_IRPF18
            + (2 * 100)  # P_IRPF19
            + (2 * 200)  # P_IRPF20
            + (2 * 300)  # P_IRPF21P
            + (2 * 400)  # P_IRPF24
        ),
        # Rendimientos de actividades económicas (dinerarios) - Retenciones
        "9": (
            (2 * 40)  # P_IRPF1
            + (2 * 100)  # P_IRPF2
            + (2 * 420)  # P_IRPF7
            + (2 * 630)  # P_IRPF9
            + (2 * 1200)  # P_IRPF15
            + (2 * 1620)  # P_IRPF18
            + (2 * 19)  # P_IRPF19
            + (2 * 40)  # P_IRPF20
            + (2 * 63)  # P_IRPF21P
            + (2 * 96)  # P_IRPF24
        ),
    }

    def test_model_111(self):
        # Purchase invoices
        self._invoice_purchase_create("2015-01-01")
        self._invoice_purchase_create("2015-01-02")
        purchase = self._invoice_purchase_create("2015-01-03")
        self._invoice_refund(purchase, "2015-01-18")

        # Create model
        export_config = self.env.ref(
            "l10n_es_aeat_mod111.aeat_mod111_main_export_config"
        )
        self.model111 = self.env["l10n.es.aeat.mod111.report"].create(
            {
                "name": "9990000000111",
                "company_id": self.company.id,
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
                "journal_id": self.journal_misc.id,
                "counterpart_account_id": self.accounts["475000"].id,
            }
        )

        # Calculate
        _logger.debug("Calculate AEAT 111 1T 2015")
        self.model111.button_calculate()

        # Fill manual fields
        self.model111.write(
            {
                # Act. Economica
                "casilla_11": 1000,  # En especie - Base
                "casilla_12": 180,  # En especie - Retenciones (18%)
                # Premios
                "casilla_14": 1100,  # Dinerarios - Base
                "casilla_15": 209,  # Dinerarios - Retenciones (19%)
                "casilla_17": 1200,  # En especie - Base
                "casilla_18": 228,  # En especie - Retenciones (19%)
                # Ganancias patrimoniales derivadas de los aprov. forestales
                "casilla_20": 1300,  # Dinerarios - Base
                "casilla_21": 26,  # Dinerarios - Retenciones (2%)
                "casilla_23": 1400,  # En especie - Base
                "casilla_24": 28,  # En especie - Retenciones (2%)
                # Contraprestaciones por la cesión de derechos de imagen
                "casilla_26": 1500,  # Dinerarios y en especie - Base
                "casilla_27": 285,  # Dinerarios y en especie - Retenciones (19%)
                # Resultados a ingresar anteriores
                "casilla_29": 145,
            }
        )

        if self.debug:
            self._print_tax_lines(self.model111.tax_line_ids)

        # Check tax lines
        for box, result in self.taxes_result.items():
            _logger.debug("Checking tax line: %s" % box)
            lines = self.model111.tax_line_ids.filtered(
                lambda x: x.field_number == int(box)
            )
            self.assertEqual(
                round(sum(lines.mapped("amount")), 2), round(result, 2), box
            )

        # Check result
        _logger.debug("Checking results")
        # ([03] + [06] + [09] + [12] + [15] + [18] + [21] + [24] + [27])
        retenciones = sum([self.taxes_result.get(b, 0.0) for b in ("3", "6", "9")])
        retenciones += sum([180 + 209 + 228 + 26 + 28 + 285])
        # ([28] - [29])
        result = retenciones - 145
        self.assertEqual(self.model111.casilla_01, 1)
        self.assertEqual(self.model111.casilla_04, 1)
        self.assertEqual(self.model111.casilla_07, 1)
        self.assertEqual(round(self.model111.casilla_28, 2), round(retenciones, 2))
        self.assertEqual(round(self.model111.casilla_30, 2), round(result, 2))
