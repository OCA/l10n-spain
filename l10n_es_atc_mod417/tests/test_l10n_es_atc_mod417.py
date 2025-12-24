# Copyright 2023 Binhex - Nicolás Ramos
# Copyright 2024 Binhex - Christian Ramos
# Copyright 2025 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl


import logging
from datetime import datetime

import requests
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("atc.417")


@tagged("post_install", "-at_install")
class TestL10nEsAtcmod417Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler atc:DEBUG' in Odoo command line
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
        "l10n_es_igic.account_tax_template_igic_ISP3": (350, 10.5),
        "l10n_es_igic.account_tax_template_igic_ISP7": (360, 25.2),
        "l10n_es_igic.account_tax_template_igic_ISP95": (370, 35.15),
        "l10n_es_igic.account_tax_template_igic_ISP15": (380, 57),
        "l10n_es_igic.account_tax_template_igic_ISP20": (390, 78),
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
        # Operaciones con inversión del sujeto pasivo - Base imponible
        "19": (
            (3 * 340)  # account_tax_template_igic_ISP0,
            + (3 * 350)  # account_tax_template_igic_ISP3,
            + (3 * 360)  # account_tax_template_igic_ISP7,
            + (3 * 370)  # account_tax_template_igic_ISP95,
            + (3 * 380)  # account_tax_template_igic_ISP15,
            + (3 * 390)  # account_tax_template_igic_ISP20,
        ),
        # Operaciones con inversión del sujeto pasivo - Cuota
        "20": (
            (3 * 0)  # account_tax_template_igic_ISP0,
            + (3 * 10.5)  # account_tax_template_igic_ISP3,
            + (3 * 25.2)  # account_tax_template_igic_ISP7,
            + (3 * 35.15)  # account_tax_template_igic_ISP95,
            + (3 * 57)  # account_tax_template_igic_ISP15,
            + (3 * 78)  # account_tax_template_igic_ISP20,
        ),
        # Modificación bases y cuotas - Base imponible (Ventas + Compras)
        "21": (
            (-1)
            * (
                (1500)  # account_tax_template_igic_r_0
                + (2000 - 200)  # account_tax_template_igic_r_3
                + (2200 - 220)  # account_tax_template_igic_r_7
                + (2400 - 240)  # account_tax_template_igic_r_9_5
                + (2600 - 260)  # account_tax_template_igic_r_15
                + (2800 - 280)  # account_tax_template_igic_r_20
                + 340  # account_tax_template_igic_ISP0,
                + 350  # account_tax_template_igic_ISP3,
                + 360  # account_tax_template_igic_ISP7,
                + 370  # account_tax_template_igic_ISP95,
                + 380  # account_tax_template_igic_ISP15,
                + 390  # account_tax_template_igic_ISP20,
            )
        ),
        # Modificación bases y cuotas - Cuota (Ventas + Compras)
        "22": (
            (-1)
            * (
                (0)  # account_tax_template_igic_r_0
                + (60 - 6)  # account_tax_template_igic_r_3
                + (154 - 15.4)  # account_tax_template_igic_r_7
                + (228 - 22.8)  # account_tax_template_igic_r_9_5
                + (390 - 39)  # account_tax_template_igic_r_15
                + (560 - 56)  # account_tax_template_igic_r_20
                + 0  # account_tax_template_igic_ISP0,
                + 10.5  # account_tax_template_igic_ISP3,
                + 25.2  # account_tax_template_igic_ISP7,
                + 35.15  # account_tax_template_igic_ISP95,
                + 57  # account_tax_template_igic_ISP15,
                + 78  # account_tax_template_igic_ISP20,
            )
        ),
        # IGIC deducible en operaciones interiores bienes y servicios corrientes - Base
        "26": (
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
        "27": (
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
        "28": (
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
        "29": (
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
        "30": (
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
        "31": (
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
        "32": (
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
        "33": (
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
        "34": (
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
                + 340  # account_tax_template_igic_ISP0,
                + 350  # account_tax_template_igic_ISP3,
                + 360  # account_tax_template_igic_ISP7,
                + 370  # account_tax_template_igic_ISP95,
                + 380  # account_tax_template_igic_ISP15,
                + 390  # account_tax_template_igic_ISP20,
            )
        ),
        # Rectificación de deducciones - Cuota
        "35": (
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
                + 0  # account_tax_template_igic_ISP0,
                + 10.5  # account_tax_template_igic_ISP3,
                + 25.2  # account_tax_template_igic_ISP7,
                + 35.15  # account_tax_template_igic_ISP95,
                + 57  # account_tax_template_igic_ISP15,
                + 78  # account_tax_template_igic_ISP20,
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
        cls.model417 = cls.env["l10n.es.atc.mod417.report"].create(
            {
                "name": "9990000000417",
                "company_id": cls.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "01",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
                "journal_id": cls.journal_misc.id,
            }
        )


class TestL10nEsAeatmod417(TestL10nEsAtcmod417Base):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()
        # Purchase invoices
        cls._invoice_purchase_create("2017-01-01")
        cls._invoice_purchase_create("2017-01-02")
        purchase = cls._invoice_purchase_create("2017-01-03")
        cls._invoice_refund(purchase, "2017-01-18")
        # Sale invoices
        cls._invoice_sale_create("2017-01-11")
        cls._invoice_sale_create("2017-01-12")
        sale = cls._invoice_sale_create("2017-01-13")
        cls._invoice_refund(sale, "2017-01-14")

    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return cls._super_send(s, r, **kw)

    def _check_tax_lines(self):
        for field, result in iter(self.taxes_result.items()):
            _logger.debug("Checking tax line: %s" % field)
            lines = self.model417.tax_line_ids.filtered(
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

    def _set_f417_fields(self):
        self.model417.company_vat = "A58818501"
        self.model417.year = datetime.now().year
        country_spain = self.env.ref("base.es")
        country_spain.enforce_cities = True
        las_palmas_city = self.env["res.city"].create(
            {
                "name": "Las Palmas de Gran Canaria",
                "code": "35016",
                "country_id": country_spain.id,
            }
        )
        self.model417.company_id.write(
            {
                "street": "Test street",
                "zip": "35001",
                "atc_public_way": "CL",
                "state_id": self.env.ref("base.state_es_gc").id,
                "city_id": las_palmas_city.id,
            }
        )

    def test_model_417(self):
        _logger.debug("Calculate ATC 417 01 2017")
        self.model417.button_calculate()
        # Test default counterpart.
        self.assertEqual(
            self.model417.counterpart_account_id.id, self.accounts["475700"].id
        )
        self.assertEqual(self.model417.state, "calculated")
        # Fill manual fields
        if self.debug:
            self._print_tax_lines(self.model417.tax_line_ids)
        self._check_tax_lines()
        # Check result
        _logger.debug("Checking results")
        devengado = sum(
            self.taxes_result.get(b, 0.0)
            for b in ("3", "6", "9", "12", "15", "18", "20", "22", "24")
        )
        deducir = sum(
            self.taxes_result.get(b, 0.0)
            for b in ("27", "29", "31", "33", "35", "36", "37", "38", "39")
        )
        self.model417.write(
            {
                "regularizacion_cuotas": 150,
                "a_deducir": 50,
                "cuotas_compensar": 100,
            }
        )
        subtotal = round(devengado - deducir, 3)
        result = round(subtotal + 150 - 50 - 100, 3)
        self.assertAlmostEqual(self.model417.total_devengado, devengado, 2)
        self.assertAlmostEqual(self.model417.total_deducir, deducir, 2)
        self.assertAlmostEqual(self.model417.resultado_autoliquidacion, result, 2)

        self.assertEqual(self.model417.result_type, "I")

        self.model417.button_post()
        self.assertTrue(self.model417.move_id)
        self.assertEqual(self.model417.move_id.ref, self.model417.name)
        self.assertEqual(
            self.model417.move_id.journal_id,
            self.model417.journal_id,
        )
        self.assertEqual(
            self.model417.move_id.line_ids.mapped("partner_id"),
            self.env.ref("l10n_es_atc.res_partner_atc"),
        )
        codes = self.model417.move_id.mapped("line_ids.account_id.code")
        self.assertIn("475700", codes)
        self.assertIn("477700", codes)
        self.assertIn("472700", codes)
        self.model417.button_unpost()
        self.assertFalse(self.model417.move_id)
        self.assertEqual(self.model417.state, "cancelled")
        self.model417.button_recover()
        self.assertEqual(self.model417.state, "draft")
        self.assertEqual(self.model417.calculation_date, False)
        self.model417.button_cancel()
        self.assertEqual(self.model417.state, "cancelled")

    def test_model_417_declaration_xml(self):
        """
        Test the generation of the .xml file
        Devengado (DEV) = 275960
        Deducible (DED) = 233930
        Resultado (TIP) = I
        Resultado (IMP) = 42030
        Resultado (FPA) = 5
        """
        self.model417.button_calculate()
        self._check_tax_lines()
        self.assertEqual(self.model417.result_type, "I")
        self._set_f417_fields()
        report_name = "l10n_es_atc_mod417.mod417_report_xml"
        xml_data = self.env["ir.actions.report"]._render_qweb_xml(
            report_name, self.model417.ids
        )[0]
        # Parse the XML data and check the values
        doc = etree.XML(xml_data)
        dec_node = doc.xpath("//DEC")
        self.assertEqual(len(dec_node), 1)
        dec_node = dec_node[0]
        self.assertEqual(dec_node.attrib["MOD"], "417")
        self.assertEqual(dec_node.attrib["ANY"], "2025")
        self.assertEqual(dec_node.attrib["PER"], "01")
        otp_node = dec_node.xpath("//IDE/OTP")
        self.assertEqual(len(otp_node), 1)
        otp_node = otp_node[0]
        self.assertEqual(otp_node.attrib["NIF"], "A58818501")
        self.assertEqual(otp_node.attrib["PAI"], "ES")
        igi_dev_node = dec_node.xpath("//IGI_DEV")
        self.assertEqual(len(igi_dev_node), 1)
        self.assertEqual(igi_dev_node[0].attrib["TOT"], "291730")
        igi_ded_node = dec_node.xpath("//IGI_DED")
        self.assertEqual(len(igi_ded_node), 1)
        self.assertEqual(igi_ded_node[0].attrib["TOT"], "213345")
        liq_node = dec_node.xpath("//LIQ")
        self.assertEqual(len(liq_node), 1)
        self.assertEqual(liq_node[0].attrib["DIF"], "78385")
        self.assertEqual(liq_node[0].attrib["RLI"], "78385")
        res_node = dec_node.xpath("//RES")
        self.assertEqual(len(res_node), 1)
        self.assertEqual(res_node[0].attrib["TIP"], "I")
        self.assertEqual(res_node[0].attrib["IMP"], "78385")
        self.assertEqual(res_node[0].attrib["FPA"], "5")

    def test_model_417_declaration_pdf(self):
        """
        Test the generation of the .pdf file
        set the output_type to B (Borrador)
        set the payment_type to 1 - Efectivo
        """
        self.model417.button_calculate()
        self._check_tax_lines()
        self.assertEqual(self.model417.result_type, "I")
        # check configuration
        with self.assertRaisesRegex(UserError, r".*The company .* has no street.*"):
            self.model417.action_generar_mod417()
        self._set_f417_fields()
        self.model417.output_type = "B"
        self.model417.payment_type = "1"  # Efectivo
        # In oca-ci, we have an issue: https://github.com/OCA/oca-ci/issues/94
        # Read the ROADMAP for more information.
        # Therefore, we always expect an error.
        # TODO: Remove the next line once the issue is fixed.
        with self.assertRaisesRegex(
            UserError, r".*Declaracion no generada. Revisa si el XML es válido.*"
        ):
            self.model417.with_context(
                test_l10n_es_atc_report=True
            ).action_generar_mod417()

    def test_model_417_declaration_dec(self):
        """
        Test the generation of the .dec file
        set the output_type to T (Telematic)
        set the payment_type to 5 - Pago telemático
        """
        self.model417.button_calculate()
        self._check_tax_lines()
        self.assertEqual(self.model417.result_type, "I")
        # check configuration
        with self.assertRaisesRegex(UserError, r".*The company .* has no street.*"):
            self.model417.action_generar_mod417()
        self._set_f417_fields()
        self.model417.output_type = "T"
        # Set a payment_type different from 5 (Pago telemático); an error is expected.
        self.model417.payment_type = "1"  # Efectivo
        with self.assertRaisesRegex(
            UserError, r".*payment type is not compatible with the output type.*"
        ):
            self.model417.action_generar_mod417()
        self.model417.payment_type = "5"  # Pago telemático
        # In oca-ci, we have an issue: https://github.com/OCA/oca-ci/issues/94
        # Read the ROADMAP for more information.
        # Therefore, we always expect an error.
        # TODO: Remove the next line once the issue is fixed.
        with self.assertRaisesRegex(
            UserError, r".*Declaracion no generada. Revisa si el XML es válido.*"
        ):
            self.model417.with_context(
                test_l10n_es_atc_report=True
            ).action_generar_mod417()
