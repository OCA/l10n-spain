# Copyright 2025 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl


import logging

import requests
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("atc.425")


@tagged("post_install", "-at_install")
class TestL10nEsAtcMod425Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        "l10n_es_igic.account_tax_template_igic_r_3": (2000, 60),
        "l10n_es_igic.account_tax_template_igic_r_3//neg": (-200, -6),
        "l10n_es_igic.account_tax_template_igic_r_7": (2200, 154),
        "l10n_es_igic.account_tax_template_igic_r_7//neg": (-220, -15.4),
        "l10n_es_igic.account_tax_template_igic_r_9_5": (2400, 228),
        "l10n_es_igic.account_tax_template_igic_r_9_5//neg": (-240, -22.8),
        "l10n_es_igic.account_tax_template_igic_r_15": (2600, 390),
        "l10n_es_igic.account_tax_template_igic_r_15//neg": (-260, -39),
        "l10n_es_igic.account_tax_template_igic_r_20": (2800, 560),
        "l10n_es_igic.account_tax_template_igic_r_20//neg": (-280, -56),
        "l10n_es_igic.account_tax_template_igic_r_0": (1500, 0),
        "l10n_es_igic.account_tax_template_igic_s_ISP0": (1600, 0),
        "l10n_es_igic.account_tax_template_igic_ex_0": (1700, 0),
        "l10n_es_igic.account_tax_template_igic_re_ex": (1800, 0),
        "l10n_es_igic.account_tax_template_igic_cmino": (1900, 0),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "l10n_es_igic.account_tax_template_igic_p_ex": (100, 0),
        "l10n_es_igic.account_tax_template_igic_sop_0": (200, 0),
        "l10n_es_igic.account_tax_template_igic_sop_3": (300, 9),
        "l10n_es_igic.account_tax_template_igic_sop_3//neg": (-30, -0.9),
        "l10n_es_igic.account_tax_template_igic_sop_7": (400, 28),
        "l10n_es_igic.account_tax_template_igic_sop_7//neg": (-40, -2.8),
        "l10n_es_igic.account_tax_template_igic_sop_9_5": (500, 47.5),
        "l10n_es_igic.account_tax_template_igic_sop_9_5//neg": (-50, -4.75),
        "l10n_es_igic.account_tax_template_igic_sop_15": (600, 90),
        "l10n_es_igic.account_tax_template_igic_sop_15//neg": (-60, -9),
        "l10n_es_igic.account_tax_template_igic_sop_20": (700, 140),
        "l10n_es_igic.account_tax_template_igic_sop_20//neg": (-70, -14),
        "l10n_es_igic.account_tax_template_igic_sop_0_inv": (110, 0),
        "l10n_es_igic.account_tax_template_igic_sop_3_inv": (120, 3.6),
        "l10n_es_igic.account_tax_template_igic_sop_7_inv": (130, 9.1),
        "l10n_es_igic.account_tax_template_igic_sop_9_5_inv": (140, 13.3),
        "l10n_es_igic.account_tax_template_igic_sop_15_inv": (150, 22.5),
        "l10n_es_igic.account_tax_template_igic_sop_20_inv": (160, 32),
        "l10n_es_igic.account_tax_template_igic_sop_i_0": (210, 0),
        "l10n_es_igic.account_tax_template_igic_sop_i_3": (220, 6.6),
        "l10n_es_igic.account_tax_template_igic_sop_i_7": (230, 16.1),
        "l10n_es_igic.account_tax_template_igic_sop_i_9_5": (240, 22.8),
        "l10n_es_igic.account_tax_template_igic_sop_i_15": (250, 37.5),
        "l10n_es_igic.account_tax_template_igic_sop_i_20": (260, 52),
        "l10n_es_igic.account_tax_template_igic_sop_i_0_inv": (270, 0),
        "l10n_es_igic.account_tax_template_igic_sop_i_3_inv": (280, 8.4),
        "l10n_es_igic.account_tax_template_igic_sop_i_7_inv": (290, 20.3),
        "l10n_es_igic.account_tax_template_igic_sop_i_9_5_inv": (310, 29.45),
        "l10n_es_igic.account_tax_template_igic_sop_i_15_inv": (320, 48),
        "l10n_es_igic.account_tax_template_igic_sop_i_20_inv": (330, 66),
        "l10n_es_igic.account_tax_template_igic_ISP0": (340, 0),
        "l10n_es_igic.account_tax_template_igic_ISP3": (350, 0),
        "l10n_es_igic.account_tax_template_igic_ISP7": (360, 0),
        "l10n_es_igic.account_tax_template_igic_ISP95": (370, 0),
        "l10n_es_igic.account_tax_template_igic_ISP15": (380, 0),
        "l10n_es_igic.account_tax_template_igic_ISP20": (390, 0),
        "l10n_es_igic.account_tax_template_igic_p_re0": (410, 0),
        "l10n_es_igic.account_tax_template_igic_p_re03": (420, 1.26),
        "l10n_es_igic.account_tax_template_igic_p_re07": (430, 3.01),
        "l10n_es_igic.account_tax_template_igic_p_re095": (440, 4.18),
        "l10n_es_igic.account_tax_template_igic_p_re15": (450, 6.75),
        "l10n_es_igic.account_tax_template_igic_p_re20": (460, 9.2),
    }
    taxes_result = {
        # IGIC Tipo cero - Base imponible 0%
        "1": (3 * 1500),  # account_tax_template_igic_r_0
        # IGIC Tipo cero - Cuota 0%
        "3": 0,  # account_tax_template_igic_r_0
        # IGIC Tipo reducido - Base imponible 3%
        "4": (3 * 2000) - 3 * 200,  # account_tax_template_igic_r_3
        # IGIC Tipo reducido - Cuota 3%
        "6": (3 * 60) - 3 * 6,  # account_tax_template_igic_r_3
        # IGIC Tipo general - Base imponible 7%
        "7": (3 * 2200) - 3 * 220,  # account_tax_template_igic_r_7
        # IGIC Tipo general - Cuota 7%
        "9": (3 * 154) - 3 * 15.4,  # account_tax_template_igic_r_7
        # IGIC Tipo incrementado - Base imponible 9,5%
        "10": (3 * 2400) - 3 * 240,  # account_tax_template_igic_r_9_5
        # IGIC Tipo incrementado - Cuota 9,5%
        "12": (3 * 228) - 3 * 22.8,  # account_tax_template_igic_r_9_5
        # IGIC Tipo incrementado - Base imponible 15%
        "13": (3 * 2600) - 3 * 260,  # account_tax_template_igic_r_15
        # IGIC Tipo incrementado - Cuota 15%
        "15": (3 * 390) - 3 * 39,  # account_tax_template_igic_r_15
        # IGIC Tipo especial - Base imponible 20%
        "16": (3 * 2800) - 3 * 280,  # account_tax_template_igic_r_20
        # IGIC Tipo especial - Cuota 20%
        "18": (3 * 560) - 3 * 56,  # account_tax_template_igic_r_20
        # Modificación bases y cuotas - Base imponible (Ventas + Compras)
        "70": (
            (-1)
            * (
                (1500)  # account_tax_template_igic_r_0
                + (2000 - 200)  # account_tax_template_igic_r_3
                + (2200 - 220)  # account_tax_template_igic_r_7
                + (2400 - 240)  # account_tax_template_igic_r_9_5
                + (2600 - 260)  # account_tax_template_igic_r_15
                + (2800 - 280)  # account_tax_template_igic_r_20
                + (200)  # account_tax_template_igic_sop_0
                + (300 - 30)  # account_tax_template_igic_sop_3
                + (400 - 40)  # account_tax_template_igic_sop_7
                + (500 - 50)  # account_tax_template_igic_sop_9_5
                + (600 - 60)  # account_tax_template_igic_sop_15
                + (700 - 70)  # account_tax_template_igic_sop_20
                + (110)  # account_tax_template_igic_sop_0_inv
                + (120)  # account_tax_template_igic_sop_3_inv
                + (130)  # account_tax_template_igic_sop_7_inv
                + (140)  # account_tax_template_igic_sop_9_5_inv
                + (150)  # account_tax_template_igic_sop_15_inv
                + (160)
            )  # account_tax_template_igic_sop_20_inv
        ),
        # Modificación bases y cuotas - Cuota (Ventas + Compras)
        "71": (
            (-1)
            * (
                (0)  # account_tax_template_igic_r_0
                + (60 - 6)  # account_tax_template_igic_r_3
                + (154 - 15.4)  # account_tax_template_igic_r_7
                + (228 - 22.8)  # account_tax_template_igic_r_9_5
                + (390 - 39)  # account_tax_template_igic_r_15
                + (560 - 56)  # account_tax_template_igic_r_20
                + (0)  # account_tax_template_igic_sop_0
                + (9 - 0.9)  # account_tax_template_igic_sop_3
                + (28 - 2.8)  # account_tax_template_igic_sop_7
                + (47.5 - 4.75)  # account_tax_template_igic_sop_9_5
                + (90 - 9)  # account_tax_template_igic_sop_15
                + (140 - 14)  # account_tax_template_igic_sop_20
                + (0)  # account_tax_template_igic_sop_0_inv
                + (3.6)  # account_tax_template_igic_sop_3_inv
                + (9.1)  # account_tax_template_igic_sop_7_inv
                + (13.3)  # account_tax_template_igic_sop_9_5_inv
                + (22.5)  # account_tax_template_igic_sop_15_inv
                + (32)
            )  # account_tax_template_igic_sop_20_inv
        ),
        # IGIC deducible en operaciones interiores bienes y servicios corrientes - Base
        "80": (
            (3 * 300 - 3 * 30)  # account_tax_template_igic_sop_3
            + (3 * 400 - 3 * 40)  # account_tax_template_igic_sop_7
            + (3 * 500 - 3 * 50)  # account_tax_template_igic_sop_9_5
            + (3 * 600 - 3 * 60)  # account_tax_template_igic_sop_15
            + (3 * 700 - 3 * 70)  # account_tax_template_igic_sop_20
            # account_tax_template_igic_ISP0
            + (3 * 340)
            # account_tax_template_igic_ISP3
            + (3 * 350)
            # account_tax_template_igic_ISP7
            + (3 * 360)
            # account_tax_template_igic_ISP95
            + (3 * 370)
            # account_tax_template_igic_ISP15
            + (3 * 380)
            # account_tax_template_igic_ISP20
            + (3 * 390)
            # account_tax_template_igic_p_re0
            + (3 * 410)
            # account_tax_template_igic_p_re03
            + (3 * 420)
            # account_tax_template_igic_p_re07
            + (3 * 430)
            # account_tax_template_igic_p_re095
            + (3 * 440)
            # account_tax_template_igic_p_re15
            + (3 * 450)
            # account_tax_template_igic_p_re20
            + (3 * 460)
        ),
        # IGIC deducible en operaciones interiores bienes y servicios corrientes - Cuota
        "81": (
            (3 * 9 - 3 * 0.9)  # account_tax_template_igic_sop_3
            + (3 * 28 - 3 * 2.8)  # account_tax_template_igic_sop_7
            + (3 * 47.5 - 3 * 4.75)  # account_tax_template_igic_sop_9_5
            + (3 * 90 - 3 * 9)  # account_tax_template_igic_sop_15
            + (3 * 140 - 3 * 14)  # account_tax_template_igic_sop_20
            # account_tax_template_igic_ISP3
            + (3 * 10.5)
            # account_tax_template_igic_ISP7
            + (3 * 25.2)
            # account_tax_template_igic_ISP95
            + (3 * 35.15)
            # account_tax_template_igic_ISP15
            + (3 * 57)
            # account_tax_template_igic_ISP20
            + (3 * 78)
            # account_tax_template_igic_p_re03
            + (3 * 1.26)
            # account_tax_template_igic_p_re07
            + (3 * 3.01)
            # account_tax_template_igic_p_re095
            + (3 * 4.18)
            # account_tax_template_igic_p_re15
            + (3 * 6.75)
            # account_tax_template_igic_p_re20
            + (3 * 9.2)
        ),
        # IGIC deducible en operaciones interiores bienes de inversión - Base
        "82": (
            # account_tax_template_igic_sop_0_inv
            (3 * 110)
            # account_tax_template_igic_sop_3_inv
            + (3 * 120)
            # account_tax_template_igic_sop_7_inv
            + (3 * 130)
            # account_tax_template_igic_sop_9_5_inv
            + (3 * 140)
            # account_tax_template_igic_sop_15_inv
            + (3 * 150)
            # account_tax_template_igic_sop_20_inv
            + (3 * 160)
        ),
        # IGIC deducible en operaciones interiores bienes de inversión - Cuota
        "83": (
            # account_tax_template_igic_sop_0_inv
            (3 * 0)
            # account_tax_template_igic_sop_3_inv
            + (3 * 3.6)
            # account_tax_template_igic_sop_7_inv
            + (3 * 9.1)
            # account_tax_template_igic_sop_9_5_inv
            + (3 * 13.3)
            # account_tax_template_igic_sop_15_inv
            + (3 * 22.5)
            # account_tax_template_igic_sop_20_inv
            + (3 * 32)
        ),
        # IGIC deducible por importaciones de bienes corrientes - Base
        "84": (
            # account_tax_template_igic_sop_i_0
            (3 * 210)
            # account_tax_template_igic_sop_i_3
            + (3 * 220)
            # account_tax_template_igic_sop_i_7
            + (3 * 230)
            # account_tax_template_igic_sop_i_9_5
            + (3 * 240)
            # account_tax_template_igic_sop_i_15
            + (3 * 250)
            # account_tax_template_igic_sop_i_20
            + (3 * 260)
        ),
        # IGIC deducible por importaciones de bienes corrientes - Cuota
        "85": (
            # account_tax_template_igic_sop_i_0
            (3 * 0)
            # account_tax_template_igic_sop_i_3
            + (3 * 6.6)
            # account_tax_template_igic_sop_i_7
            + (3 * 16.1)
            # account_tax_template_igic_sop_i_9_5
            + (3 * 22.8)
            # account_tax_template_igic_sop_i_15
            + (3 * 37.5)
            # account_tax_template_igic_sop_i_20
            + (3 * 52)
        ),
        # IGIC deducible por importaciones de bienes de inversión - Base
        "86": (
            # account_tax_template_igic_sop_i_0_inv
            (3 * 270)
            # account_tax_template_igic_sop_i_3_inv
            + (3 * 280)
            # account_tax_template_igic_sop_i_7_inv
            + (3 * 290)
            # account_tax_template_igic_sop_i_9_5_inv
            + (3 * 310)
            # account_tax_template_igic_sop_i_15_inv
            + (3 * 320)
            # account_tax_template_igic_sop_i_20_inv
            + (3 * 330)
        ),
        # IGIC deducible por importaciones de bienes de inversión - Cuota
        "87": (
            # account_tax_template_igic_sop_i_0_inv
            (3 * 0)
            # account_tax_template_igic_sop_i_3_inv
            + (3 * 8.4)
            # account_tax_template_igic_sop_i_7_inv
            + (3 * 20.3)
            # account_tax_template_igic_sop_i_9_5_inv
            + (3 * 29.45)
            # account_tax_template_igic_sop_i_15_inv
            + (3 * 48)
            # account_tax_template_igic_sop_i_20_inv
            + (3 * 66)
        ),
        # Rectificación de deducciones - Base
        "88": (
            # account_tax_template_igic_sop_0
            (-1)
            * (
                (200)
                # account_tax_template_igic_sop_3
                + (300 - 30)
                # account_tax_template_igic_sop_7
                + (400 - 40)
                # account_tax_template_igic_sop_9_5
                + (500 - 50)
                # account_tax_template_igic_sop_15
                + (600 - 60)
                # account_tax_template_igic_sop_20
                + (700 - 70)
                # account_tax_template_igic_sop_0_inv
                + (110)
                # account_tax_template_igic_sop_3_inv
                + (120)
                # account_tax_template_igic_sop_7_inv
                + (130)
                # account_tax_template_igic_sop_9_5_inv
                + (140)
                # account_tax_template_igic_sop_15_inv
                + (150)
                # account_tax_template_igic_sop_20_inv
                + (160)
            )
        ),
        # Rectificación de deducciones - Cuota
        "89": (
            # account_tax_template_igic_sop_0
            (-1)
            * (
                (0)
                # account_tax_template_igic_sop_3
                + (9 - 0.9)
                # account_tax_template_igic_sop_7
                + (28 - 2.8)
                # account_tax_template_igic_sop_9_5
                + (47.5 - 4.75)
                # account_tax_template_igic_sop_15
                + (90 - 9)
                # account_tax_template_igic_sop_20
                + (140 - 14)
                # account_tax_template_igic_sop_0_inv
                + (0)
                # account_tax_template_igic_sop_3_inv
                + (3.6)
                # account_tax_template_igic_sop_7_inv
                + (9.1)
                # account_tax_template_igic_sop_9_5_inv
                + (13.3)
                # account_tax_template_igic_sop_15_inv
                + (22.5)
                # account_tax_template_igic_sop_20_inv
                + (32)
            )
        ),
    }

    @classmethod
    def _chart_of_accounts_create(cls):
        _logger.debug("Creating chart of account")
        cls.company = cls.env["res.company"].create(
            {"name": "Canary test company", "currency_id": cls.env.ref("base.EUR").id}
        )
        cls.env["account.chart.template"].try_loading(
            "es_pymes_canary", company=cls.company, install_demo=False
        )
        cls.env.ref("base.group_multi_company").write({"users": [(4, cls.env.uid)]})
        cls.env.user.write(
            {"company_ids": [(4, cls.company.id)], "company_id": cls.company.id}
        )
        cls.with_context(company_id=cls.company.id)
        return True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create model
        cls.model425 = cls.env["l10n.es.atc.mod425.report"].create(
            {
                "name": "9990000000420",
                "company_id": cls.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2024,
                "period_type": "0A",
                "date_start": "2024-01-01",
                "date_end": "2024-03-31",
                "journal_id": cls.journal_misc.id,
            }
        )
        cls.palmas_city = cls.env["res.city"].create(
            {
                "name": "Las Palmas de Gran Canaria",
                "code": "35016",
                "state_id": cls.env.ref("base.state_es_gc").id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.palmas_zip = cls.env["res.city.zip"].create(
            {
                "name": "35001",
                "city_id": cls.palmas_city.id,
            }
        )


class TestL10nEsAeatMod425(TestL10nEsAtcMod425Base):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()
        # Purchase invoices
        cls._invoice_purchase_create("2024-01-01")
        cls._invoice_purchase_create("2024-01-02")
        purchase = cls._invoice_purchase_create("2024-01-03")
        cls._invoice_refund(purchase, "2024-01-18")
        # Sale invoices
        cls._invoice_sale_create("2024-01-11")
        cls._invoice_sale_create("2024-01-12")
        sale = cls._invoice_sale_create("2024-01-13")
        cls._invoice_refund(sale, "2024-01-14")

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return cls._super_send(s, r, **kw)

    def _check_tax_lines(self):
        for field, result in iter(self.taxes_result.items()):
            _logger.debug("Checking tax line: %s" % field)
            lines = self.model425.tax_line_ids.filtered(
                lambda x, field=field: x.field_number == int(field)
            )
            self.assertAlmostEqual(
                sum(lines.mapped("amount")),
                result,
                2,
                "Incorrect result in field %s" % field,
            )

    @classmethod
    def _accounts_search(cls):
        _logger.debug("Searching accounts")
        codes = {
            "472000",
            "473000",
            "477000",
            "475100",
            "475000",
            "600000",
            "700000",
            "430000",
            "410000",
            "475700",
            "477700",
        }
        for code in codes:
            cls.accounts[code] = cls.env["account.account"].search(
                [("company_id", "=", cls.company.id), ("code", "=", code)]
            )
        return True

    def _set_f425_fields(self):
        self.model425.company_id.street = "Test street"
        self.model425.company_vat = "A58818501"
        self.model425.company_id.atc_public_way = "CL"
        self.model425.main_activity_code = (
            "1"
        )  # 1 - Actividades sujetas al Impuesto sobre Actividades Económicas
        self.model425.main_activity_iae = (
            "1011"
        )  # 1011 - EXPLOTACIÓN EXTENSIVA GANADO BOVINO
        self.model425.main_regime_code = "1"  # 1 - Régimen ordinario
        self.model425.first_representative_name = "Primer Representante"
        self.model425.first_representative_vat = "B12345674"
        self.model425.first_representative_notary = "01"
        self.model425.first_representative_date = "2024-01-01"
        self.model425.casilla_118 = "1"  # Valor a compensar
        with Form(self.model425.company_id) as company_form:
            company_form.zip_id = self.palmas_zip

    def test_model_425(self):
        _logger.debug("Calculate ATC 425 1T 2024")
        self.model425.button_calculate()
        self.assertEqual(self.model425.state, "calculated")
        # Fill manual fields
        if self.debug:
            self._print_tax_lines(self.model425.tax_line_ids)
        self._check_tax_lines()
        # Check result
        _logger.debug("Checking results")
        self.assertAlmostEqual(self.model425.casilla_74, 21340, 2)
        self.assertAlmostEqual(self.model425.casilla_79, 2142.05, 2)
        self.assertAlmostEqual(self.model425.casilla_94, 2339.30, 2)
        self.assertAlmostEqual(self.model425.casilla_95, -197.25, 2)
        self.assertAlmostEqual(self.model425.casilla_120, 21340, 2)
        self.model425.button_confirm()
        self.assertEqual(self.model425.state, "done")
        self.model425.button_unpost()
        self.assertEqual(self.model425.state, "cancelled")
        self.model425.button_recover()
        self.assertEqual(self.model425.state, "draft")
        self.assertEqual(self.model425.calculation_date, False)
        self.model425.button_cancel()
        self.assertEqual(self.model425.state, "cancelled")

    def test_model_425_declaration_xml(self):
        """
        Test the generation of the .xml file
        Devengado (DEV) = 275960
        Deducible (DED) = 233930
        Resultado (TIP) = I
        Resultado (IMP) = 42030
        Resultado (FPA) = 5
        """
        self.model425.button_calculate()
        self._check_tax_lines()
        self._set_f425_fields()
        report_name = "l10n_es_atc_mod425.mod425_report_xml"
        xml_data = self.env["ir.actions.report"]._render_qweb_xml(
            report_name, self.model425.ids
        )[0]
        # Parse the XML data and check the values
        doc = etree.XML(xml_data)
        dec_node = doc.xpath("//DEC")
        self.assertEqual(len(dec_node), 1)
        dec_node = dec_node[0]
        self.assertEqual(dec_node.attrib["MOD"], "425")
        self.assertEqual(dec_node.attrib["ANY"], "2024")
        self.assertEqual(dec_node.attrib["PER"], "0A")
        act_node = dec_node.xpath("//EST/ACT")
        self.assertEqual(len(act_node), 1)
        act_node = act_node[0]
        self.assertEqual(act_node.attrib["CLA"], "1")
        self.assertEqual(act_node.attrib["EPI"], "1011")
        self.assertEqual(act_node.attrib["REG"], "1")
        rep_node = dec_node.xpath("//REP")
        self.assertEqual(len(rep_node), 1)
        rep_node = rep_node[0]
        self.assertEqual(rep_node.attrib["TIP"], "PJ")
        self.assertEqual(rep_node.attrib["NOT"], "01")
        self.assertEqual(rep_node.attrib["FPO"], "01/01/2024")
        person_node = rep_node.xpath("//OTP/PER")
        self.assertEqual(len(person_node), 1)
        person_node = person_node[0]
        self.assertEqual(person_node.attrib["NIF"], "B12345674")
        self.assertEqual(person_node.attrib["NRS"], "Primer Representante".upper())
        otp_node = dec_node.xpath("//IDE/OTP")
        self.assertEqual(len(otp_node), 1)
        otp_node = otp_node[0]
        self.assertEqual(otp_node.attrib["NIF"], "A58818501")
        self.assertEqual(otp_node.attrib["PAI"], "ES")
        igi_dev_node = dec_node.xpath("//REG//DEV")
        self.assertEqual(len(igi_dev_node), 1)
        self.assertEqual(igi_dev_node[0].attrib["TBA"], "2134000")
        igi_ded_node = dec_node.xpath("//REG//DED")
        self.assertEqual(len(igi_ded_node), 1)
        self.assertEqual(igi_ded_node[0].attrib["TOT"], "233930")
        liq_node = dec_node.xpath("//LIQ")
        self.assertEqual(len(liq_node), 1)
        self.assertEqual(liq_node[0].attrib["SUT"], "-19725")
        self.assertEqual(liq_node[0].attrib["RLI"], "-19725")
        res_node = dec_node.xpath("//OPE")
        self.assertEqual(len(res_node), 1)
        self.assertEqual(res_node[0].attrib["TOT"], "2134000")

    def test_model_425_declaration_pdf(self):
        """
        Test the generation of the .pdf file
        set the output_type to B (Borrador)
        set the payment_type to 1 - Efectivo
        """
        self.model425.button_calculate()
        self._check_tax_lines()
        # check configuration
        with self.assertRaisesRegex(UserError, r".*The company .* has no street.*"):
            self.model425.action_generar_mod425()
        with self.assertRaisesRegex(UserError, r".*Please set the code in the city.*"):
            self.model425.action_generar_mod425()
        with self.assertRaisesRegex(
            UserError, r".*Please set the Public Way in the company.*"
        ):
            self.model425.action_generar_mod425()
        self._set_f425_fields()
        self.model425.output_type = "B"
        # In oca-ci, we have an issue: https://github.com/OCA/oca-ci/issues/94
        # Read the ROADMAP for more information.
        # Therefore, we always expect an error.
        # TODO: Remove the next line once the issue is fixed.
        with self.assertRaisesRegex(
            UserError, r".*Declaracion no generada. Revisa si el XML es válido.*"
        ):
            self.model425.with_context(
                test_l10n_es_atc_report=True
            ).action_generar_mod425()

    def test_model_425_declaration_dec(self):
        """
        Test the generation of the .dec file
        set the output_type to T (Telematic)
        set the payment_type to 5 - Pago telemático
        """
        self.model425.button_calculate()
        self._check_tax_lines()
        # check configuration
        with self.assertRaisesRegex(UserError, r".*The company .* has no street.*"):
            self.model425.action_generar_mod425()
        with self.assertRaisesRegex(UserError, r".*Please set the code in the city.*"):
            self.model425.action_generar_mod425()
        with self.assertRaisesRegex(
            UserError, r".*Please set the Public Way in the company.*"
        ):
            self.model425.action_generar_mod425()
        self._set_f425_fields()
        self.model425.output_type = "T"
        # In oca-ci, we have an issue: https://github.com/OCA/oca-ci/issues/94
        # Read the ROADMAP for more information.
        # Therefore, we always expect an error.
        # TODO: Remove the next line once the issue is fixed.
        with self.assertRaisesRegex(
            UserError, r".*Declaracion no generada. Revisa si el XML es válido.*"
        ):
            self.model425.with_context(
                test_l10n_es_atc_report=True
            ).action_generar_mod425()
