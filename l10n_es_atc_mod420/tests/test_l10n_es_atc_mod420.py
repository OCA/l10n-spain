# Copyright 2023 Binhex - Nicolás Ramos
# Copyright 2024 Binhex - Christian Ramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl


import logging
import os
import re
import shutil
import subprocess
import zipfile
from contextlib import contextmanager
from io import BytesIO
from typing import ClassVar
from unittest.mock import patch

import requests
from freezegun import freeze_time
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)
from odoo.addons.l10n_es_atc.models import l10n_es_atc_report

_logger = logging.getLogger("atc.420")


@tagged("post_install", "-at_install")
class TestL10nEsAtcMod420Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler atc:DEBUG' in Odoo command line
    debug = False
    # The keys carry the module of the chart template that defines the taxes:
    # without one, `_get_taxes` takes a key with capitals (igic_ISP7) for an
    # old tax code and looks for another XML-ID
    taxes_sale: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "l10n_es.account_tax_template_igic_r_3": (2000, 60),
        "l10n_es.account_tax_template_igic_r_3//neg": (-200, -6),
        "l10n_es.account_tax_template_igic_r_7": (2200, 154),
        "l10n_es.account_tax_template_igic_r_7//neg": (-220, -15.4),
        "l10n_es.account_tax_template_igic_r_9_5": (2400, 228),
        "l10n_es.account_tax_template_igic_r_9_5//neg": (-240, -22.8),
        "l10n_es.account_tax_template_igic_r_15": (2600, 390),
        "l10n_es.account_tax_template_igic_r_15//neg": (-260, -39),
        "l10n_es.account_tax_template_igic_r_20": (2800, 560),
        "l10n_es.account_tax_template_igic_r_20//neg": (-280, -56),
        "l10n_es.account_tax_template_igic_r_0": (1500, 0),
        "l10n_es.account_tax_template_igic_s_ISP0": (1600, 0),
        "l10n_es.account_tax_template_igic_ex_0": (1700, 0),
        "l10n_es.account_tax_template_igic_re_ex": (1800, 0),
        "l10n_es.account_tax_template_igic_cmino": (1900, 0),
    }
    taxes_purchase: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "l10n_es.account_tax_template_igic_p_ex": (100, 0),
        "l10n_es.account_tax_template_igic_sop_0": (200, 0),
        "l10n_es.account_tax_template_igic_sop_3": (300, 9),
        "l10n_es.account_tax_template_igic_sop_3//neg": (-30, -0.9),
        "l10n_es.account_tax_template_igic_sop_7": (400, 28),
        "l10n_es.account_tax_template_igic_sop_7//neg": (-40, -2.8),
        "l10n_es.account_tax_template_igic_sop_9_5": (500, 47.5),
        "l10n_es.account_tax_template_igic_sop_9_5//neg": (-50, -4.75),
        "l10n_es.account_tax_template_igic_sop_15": (600, 90),
        "l10n_es.account_tax_template_igic_sop_15//neg": (-60, -9),
        "l10n_es.account_tax_template_igic_sop_20": (700, 140),
        "l10n_es.account_tax_template_igic_sop_20//neg": (-70, -14),
        "l10n_es.account_tax_template_igic_sop_0_inv": (110, 0),
        "l10n_es.account_tax_template_igic_sop_3_inv": (120, 3.6),
        "l10n_es.account_tax_template_igic_sop_7_inv": (130, 9.1),
        "l10n_es.account_tax_template_igic_sop_9_5_inv": (140, 13.3),
        "l10n_es.account_tax_template_igic_sop_15_inv": (150, 22.5),
        "l10n_es.account_tax_template_igic_sop_20_inv": (160, 32),
        "l10n_es.account_tax_template_igic_sop_i_0": (210, 0),
        "l10n_es.account_tax_template_igic_sop_i_3": (220, 6.6),
        "l10n_es.account_tax_template_igic_sop_i_7": (230, 16.1),
        "l10n_es.account_tax_template_igic_sop_i_9_5": (240, 22.8),
        "l10n_es.account_tax_template_igic_sop_i_15": (250, 37.5),
        "l10n_es.account_tax_template_igic_sop_i_20": (260, 52),
        "l10n_es.account_tax_template_igic_sop_i_0_inv": (270, 0),
        "l10n_es.account_tax_template_igic_sop_i_3_inv": (280, 8.4),
        "l10n_es.account_tax_template_igic_sop_i_7_inv": (290, 20.3),
        "l10n_es.account_tax_template_igic_sop_i_9_5_inv": (310, 29.45),
        "l10n_es.account_tax_template_igic_sop_i_15_inv": (320, 48),
        "l10n_es.account_tax_template_igic_sop_i_20_inv": (330, 66),
        "l10n_es.account_tax_template_igic_ISP0": (340, 0),
        "l10n_es.account_tax_template_igic_ISP3": (350, 10.5),
        "l10n_es.account_tax_template_igic_ISP7": (360, 25.2),
        "l10n_es.account_tax_template_igic_ISP95": (370, 35.15),
        "l10n_es.account_tax_template_igic_ISP15": (380, 57),
        "l10n_es.account_tax_template_igic_ISP20": (390, 78),
        "l10n_es.account_tax_template_igic_p_re0": (410, 0),
        "l10n_es.account_tax_template_igic_p_re03": (420, 1.26),
        "l10n_es.account_tax_template_igic_p_re07": (430, 3.01),
        "l10n_es.account_tax_template_igic_p_re095": (440, 4.18),
        "l10n_es.account_tax_template_igic_p_re15": (450, 6.75),
        "l10n_es.account_tax_template_igic_p_re20": (460, 9.2),
    }
    taxes_result: ClassVar[dict] = {
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
                # account_tax_template_igic_sop_i_3 to igic_sop_i_20
                + (220 + 230 + 240 + 250 + 260)
                # account_tax_template_igic_sop_i_3_inv to igic_sop_i_20_inv
                + (280 + 290 + 310 + 320 + 330)
                # account_tax_template_igic_p_re0 to igic_p_re20
                + (410 + 420 + 430 + 440 + 450 + 460)
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
                # account_tax_template_igic_sop_i_3 to igic_sop_i_20
                + (6.6 + 16.1 + 22.8 + 37.5 + 52)
                # account_tax_template_igic_sop_i_3_inv to igic_sop_i_20_inv
                + (8.4 + 20.3 + 29.45 + 48 + 66)
                # account_tax_template_igic_p_re0 to igic_p_re20
                + (0 + 1.26 + 3.01 + 4.18 + 6.75 + 9.2)
            )
        ),
    }

    # The chart is the one of the base: 20.0 merged the Canary templates into
    # es_common, so es_pymes already carries the IGIC taxes this declaration
    # reads. Odoo core ships them archived and activates them (archiving the
    # IVA ones) when the company gets a Canary province, as a Canary user does.
    @classmethod
    def _chart_of_accounts_create(cls):
        res = super()._chart_of_accounts_create()
        cls.company.sudo().write(
            {
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_gc").id,
            }
        )
        return res

    # The fixtures put taxes of every regime on the same invoice, which no
    # fiscal position of a Canary company allows (each one keeps only its own
    # taxes): the invoices are entered without one.
    @classmethod
    def _invoice_sale_create(cls, dt, extra_vals=None):
        return super()._invoice_sale_create(
            dt, dict(extra_vals or {}, fiscal_position_id=False)
        )

    @classmethod
    def _invoice_purchase_create(cls, dt, extra_vals=None):
        return super()._invoice_purchase_create(
            dt, dict(extra_vals or {}, fiscal_position_id=False)
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create model
        cls.model420 = cls.env["l10n.es.atc.mod420.report"].create(
            {
                "name": "9990000000420",
                "company_id": cls.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2026,
                "period_type": "1T",
                "date_start": "2026-01-01",
                "date_end": "2026-03-31",
                "journal_id": cls.journal_misc.id,
            }
        )
        # Cities and company data are administrator data, and the tests run as
        # the BaseCommon test user since 20.0
        cls.palmas_city = (
            cls.env["res.city"]
            .sudo()
            .create(
                {
                    "name": "Las Palmas de Gran Canaria",
                    "code": "35016",
                    "state_id": cls.env.ref("base.state_es_gc").id,
                    "country_id": cls.env.ref("base.es").id,
                }
            )
        )
        cls.palmas_zip = (
            cls.env["res.city.zip"]
            .sudo()
            .create(
                {
                    "name": "35001",
                    "city_id": cls.palmas_city.id,
                }
            )
        )

    @contextmanager
    def _atc_program(self):
        """Replace only the externals of the file generation: the download of
        the ATC program and the java process. The fake program writes the XML it
        receives as the declaration file, so the tests read what the ATC gets.
        Yields the arguments of each run and the jar java was given.
        """
        zip_content = BytesIO()
        with zipfile.ZipFile(zip_content, "w") as zip_file:
            zip_file.writestr("M420/lib/pa-mod420.jar", b"ATC program")
        response = requests.Response()
        response.status_code = 200
        response._content = zip_content.getvalue()
        runs = []

        def java(cmd, **kwargs):
            run = dict(re.findall(r'/([A-Z]):"([^"]*)"', cmd))
            with open(re.search(r"-cp (\S+)", cmd)[1], "rb") as jar_file:
                run["jar"] = jar_file.read()
            runs.append(run)
            extension = "dec" if run["S"] == "T" else "pdf"
            shutil.copy(run["E"], os.path.join(run["T"], f"{run['P']}.{extension}"))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        externals = l10n_es_atc_report
        with (
            patch.object(externals.requests, "head", return_value=response),
            patch.object(externals.requests, "get", return_value=response),
            patch.object(externals.subprocess, "run", side_effect=java),
        ):
            yield runs

    def _generated_files(self):
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", self.model420._name),
                ("res_id", "=", self.model420.id),
            ]
        )


class TestL10nEsAeatMod420(TestL10nEsAtcMod420Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Purchase invoices
        cls._invoice_purchase_create("2026-01-01")
        cls._invoice_purchase_create("2026-01-02")
        purchase = cls._invoice_purchase_create("2026-01-03")
        cls._invoice_refund(purchase, "2026-01-18")
        # Sale invoices
        cls._invoice_sale_create("2026-01-11")
        cls._invoice_sale_create("2026-01-12")
        sale = cls._invoice_sale_create("2026-01-13")
        cls._invoice_refund(sale, "2026-01-14")

    def _check_tax_lines(self):
        for field, result in iter(self.taxes_result.items()):
            _logger.debug(f"Checking tax line: {field}")
            lines = self.model420.tax_line_ids.filtered(
                lambda x, field=field: x.field_number == int(field)
            )
            self.assertAlmostEqual(
                sum(lines.mapped("amount")),
                result,
                2,
                f"Incorrect result in field {field}",
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
            "475800",
            "477700",
        }
        for code in codes:
            cls.accounts[code] = cls.env["account.account"].search(
                [("company_ids", "in", [cls.company.id]), ("code", "=", code)]
            )
        return True

    def _set_f420_fields(self):
        company = self.model420.company_id.sudo()
        company.street = "Test street"
        self.model420.company_vat = "A58818501"
        company.atc_public_way = "CL"
        with Form(company) as company_form:
            company_form.zip_id = self.palmas_zip

    @freeze_time("2026-04-01")
    def test_model_420(self):
        _logger.debug("Calculate ATC 420 1T 2026")
        self.model420.button_calculate()
        # The counterpart of a result to enter is Hacienda Pública acreedora,
        # as in the model 303
        self.assertEqual(self.model420.counterpart_account_id, self.accounts["475000"])
        self.assertEqual(self.model420.state, "calculated")
        # Fill manual fields
        if self.debug:
            self._print_tax_lines(self.model420.tax_line_ids)
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
        subtotal = round(devengado - deducir, 3)
        # Result shown after calculating, before filling the manual boxes
        self.assertAlmostEqual(self.model420.resultado_autoliquidacion, subtotal, 2)
        self.model420.write(
            {
                "regularizacion_cuotas": 150,
                "a_deducir": 30,
                "cuotas_compensar": 20,
            }
        )
        result = round(subtotal + 150 - 30 - 20, 3)
        self.assertAlmostEqual(self.model420.total_devengado, devengado, 2)
        self.assertAlmostEqual(self.model420.total_deducir, deducir, 2)
        self.assertAlmostEqual(self.model420.resultado_autoliquidacion, result, 2)

        self.assertEqual(self.model420.result_type, "I")
        # The user can choose another counterpart
        with Form(self.model420) as report_form:
            report_form.counterpart_account_id = self.accounts["475800"]
        # The form shows the button that creates the move
        self.assertTrue(self.model420.allow_posting)
        self.model420.button_post()
        self.assertTrue(self.model420.move_id)
        self.assertEqual(self.model420.move_id.ref, self.model420.name)
        self.assertEqual(
            self.model420.move_id.journal_id,
            self.model420.journal_id,
        )
        self.assertEqual(
            self.model420.move_id.line_ids.mapped("partner_id"),
            self.env.ref("l10n_es_atc.res_partner_atc"),
        )
        codes = self.model420.move_id.mapped("line_ids.account_id.code")
        self.assertIn("475800", codes)
        self.assertIn("477700", codes)
        self.assertIn("472700", codes)
        self.model420.button_unpost()
        self.assertFalse(self.model420.move_id)
        self.assertEqual(self.model420.state, "cancelled")
        self.model420.button_recover()
        self.assertEqual(self.model420.state, "draft")
        self.assertEqual(self.model420.calculation_date, False)
        self.model420.button_cancel()
        self.assertEqual(self.model420.state, "cancelled")

    @freeze_time("2026-04-01")
    def test_model_420_declaration_dec(self):
        """The telematic file is the XML of the declaration run through the ATC
        program: amounts in cents, the province by its ATC code and the result.
        Generating it again rewrites the same file.
        """
        self.model420.button_calculate()
        self._check_tax_lines()
        self.assertEqual(self.model420.result_type, "I")
        # check configuration
        with self.assertRaisesRegex(UserError, r".*The company .* has no street.*"):
            self.model420.action_generar_mod420()
        with self.assertRaisesRegex(UserError, r".*Please set the code in the city.*"):
            self.model420.action_generar_mod420()
        with self.assertRaisesRegex(
            UserError, r".*Please set the Public Way in the company.*"
        ):
            self.model420.action_generar_mod420()
        self._set_f420_fields()
        self.assertEqual(self.model420.output_type, "T")
        # Set a payment_type different from 5 (Pago telemático); an error is expected.
        self.model420.payment_type = "1"  # Efectivo
        with self.assertRaisesRegex(
            UserError, r".*payment type is not compatible with the output type.*"
        ):
            self.model420.action_generar_mod420()
        self.model420.payment_type = "5"  # Pago telemático
        # The file to file is generated from the confirmed declaration
        with self.assertRaisesRegex(UserError, "Confirm the declaration"):
            self.model420.action_generar_mod420()
        self.model420.button_confirm()
        with self._atc_program() as runs:
            action = self.model420.action_generar_mod420()
        self.assertEqual(runs[0]["S"], "T")
        self.assertEqual(runs[0]["jar"], b"ATC program")
        generated = self._generated_files()
        self.assertEqual(generated.name, "modelo420.dec")
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], f"/web/content/{generated.id}?download=true")
        dec_node = etree.fromstring(generated.raw.content)
        self.assertEqual(dec_node.tag, "DEC")
        self.assertEqual(dec_node.attrib["MOD"], "420")
        self.assertEqual(dec_node.attrib["ANY"], "2026")
        self.assertEqual(dec_node.attrib["PER"], "1T")
        otp_node = dec_node.xpath("//IDE/OTP")
        self.assertEqual(len(otp_node), 1)
        otp_node = otp_node[0]
        self.assertEqual(otp_node.attrib["NIF"], "A58818501")
        self.assertEqual(otp_node.attrib["PAI"], "ES")
        self.assertEqual(otp_node.attrib["POP"], "35")
        self.assertEqual(otp_node.attrib["CP"], "35001")
        self.assertEqual(otp_node.attrib["SVP"], "CL")
        self.assertEqual(otp_node.attrib["CMU"], "35016")
        igi_dev_node = dec_node.xpath("//IGI_DEV")
        self.assertEqual(len(igi_dev_node), 1)
        self.assertEqual(igi_dev_node[0].attrib["TOT"], "291730")
        # 3 sales at 7 % and a refund of one of them: 3 * 2200 - 3 * 220
        self.assertIn(
            {"BAS": "594000", "CUO": "41580", "TIP": "700"},
            [dict(node.attrib) for node in dec_node.xpath("//IGI_DEV/DEV")],
        )
        igi_ded_node = dec_node.xpath("//IGI_DED")
        self.assertEqual(len(igi_ded_node), 1)
        self.assertEqual(igi_ded_node[0].attrib["TOT"], "180190")
        liq_node = dec_node.xpath("//LIQ")
        self.assertEqual(len(liq_node), 1)
        self.assertEqual(liq_node[0].attrib["DIF"], "111540")
        self.assertEqual(liq_node[0].attrib["RLI"], "111540")
        res_node = dec_node.xpath("//RES")
        self.assertEqual(len(res_node), 1)
        self.assertEqual(res_node[0].attrib["TIP"], "I")
        self.assertEqual(res_node[0].attrib["IMP"], "111540")
        self.assertEqual(res_node[0].attrib["FPA"], "5")
        # Generating it again replaces the content of the same file
        self.model420.company_vat = "B00000000"
        with self._atc_program():
            self.model420.action_generar_mod420()
        self.assertEqual(self._generated_files(), generated)
        self.assertEqual(
            etree.fromstring(generated.raw.content).xpath("//IDE/OTP")[0].attrib["NIF"],
            "B00000000",
        )

    @freeze_time("2026-04-01")
    def test_model_420_declaration_direct_debit(self):
        """Paid by direct debit, as the order of the model 420 allows, the
        file carries the IBAN of the bank account."""
        self.model420.button_calculate()
        self._set_f420_fields()
        self.model420.payment_type = "4"  # Domiciliación bancaria
        with self.assertRaisesRegex(UserError, r".*Select a bank account.*"):
            self.model420.button_confirm()
        self.model420.partner_bank_id = self.env["res.partner.bank"].create(
            {
                "account_number": "ES9121000418450200051332",
                "partner_id": self.model420.company_id.partner_id.id,
            }
        )
        self.model420.button_confirm()
        with self._atc_program():
            self.model420.action_generar_mod420()
        dec_node = etree.fromstring(self._generated_files().raw.content)
        res_node = dec_node.xpath("//RES")[0]
        self.assertEqual(res_node.attrib["FPA"], "4")
        self.assertEqual(res_node.attrib["IBAN"], "ES9121000418450200051332")

    def test_model_420_confirm_checks_the_declaration(self):
        """The declaration is confirmed only with the data the ATC program
        needs, as when generating its file."""
        self.model420.button_calculate()
        with self.assertRaisesRegex(
            UserError, r".*Please set the Public Way in the company.*"
        ):
            self.model420.button_confirm()
        self.assertEqual(self.model420.state, "calculated")
        self._set_f420_fields()
        self.model420.button_confirm()
        self.assertEqual(self.model420.state, "done")

    def test_model_420_counterpart_to_compensate(self):
        """A result to compensate goes to Hacienda Pública deudora of the
        company of the declaration, as in the model 303."""
        self.model420.button_calculate()
        self.model420.a_deducir = self.model420.diferencia + 100
        self.assertEqual(self.model420.result_type, "C")
        self.assertEqual(self.model420.counterpart_account_id.code, "470000")
        self.assertEqual(
            self.model420.counterpart_account_id.company_ids, self.model420.company_id
        )

    def test_model_420_refund_to_a_bank_account(self):
        """A result to return in the last quarter is paid into the bank account
        of the company chosen on the declaration, as in the AEAT models."""
        self.model420.button_calculate()
        self._set_f420_fields()
        self.model420.period_type = "4T"
        self.model420.a_deducir = self.model420.diferencia + 100
        self.assertEqual(self.model420.result_type, "D")
        with self.assertRaisesRegex(UserError, "Select an account for receiving"):
            self.model420.button_confirm()
        report_form = Form(self.model420)
        report_form.partner_bank_id = self.env["res.partner.bank"].create(
            {
                "account_number": "ES9121000418450200051332",
                "partner_id": self.model420.company_id.partner_id.id,
            }
        )
        report_form.save()
        self.model420.button_confirm()
        self.assertEqual(self.model420.state, "done")

    def test_model_420_substitutive(self):
        """The ATC file of the model 420 has the complementary declaration and
        no substitutive one, so the form refuses that type."""
        report_form = Form(self.model420)
        report_form.statement_type = "S"
        report_form.previous_number = "4200000000001"
        with self.assertRaisesRegex(UserError, "substitutive reports"):
            report_form.save()

    @freeze_time("2026-04-01")
    def test_model_420_declaration_manual_boxes(self):
        """The boxes 42 to 44 entered after calculating change the result and
        its type in the file: here, an amount to carry forward."""
        self.model420.button_calculate()
        self._set_f420_fields()
        # The result the form shows after calculating
        self.assertEqual(self.model420.result_type, "I")
        self.model420.write(
            {"regularizacion_cuotas": 150, "cuotas_compensar": 20, "a_deducir": 1300}
        )
        self.assertEqual(self.model420.result_type, "C")
        self.model420.button_confirm()
        with self._atc_program():
            self.model420.action_generar_mod420()
        dec_node = etree.fromstring(self._generated_files().raw.content)
        liq_node = dec_node.xpath("//LIQ")[0]
        self.assertEqual(liq_node.attrib["DIF"], "111540")
        self.assertEqual(liq_node.attrib["RCU"], "15000")
        self.assertEqual(liq_node.attrib["CPA"], "2000")
        self.assertEqual(liq_node.attrib["DAC"], "130000")
        # 1115.40 + 150 - 20 - 1300
        self.assertEqual(liq_node.attrib["RLI"], "-5460")
        res_node = dec_node.xpath("//RES")[0]
        self.assertEqual(res_node.attrib["TIP"], "C")
        self.assertEqual(res_node.attrib["IMP"], "5460")

    @freeze_time("2026-04-01")
    def test_model_420_declaration_pdf(self):
        """A draft is a PDF made by the same program with output type B."""
        self.model420.button_calculate()
        self._set_f420_fields()
        self.model420.output_type = "B"
        self.model420.payment_type = "1"  # Efectivo
        with self._atc_program() as runs:
            self.model420.action_generar_mod420()
        self.assertEqual(runs[0]["S"], "B")
        self.assertEqual(self._generated_files().name, "modelo420.pdf")

    @freeze_time("2026-04-01")
    def test_model_420_declaration_with_attachments_in_database(self):
        """The ATC program also runs when the attachments live in the database."""
        self.env["ir.config_parameter"].sudo().set_str("ir_attachment.location", "db")
        self.model420.button_calculate()
        self._set_f420_fields()
        self.model420.button_confirm()
        with self._atc_program() as runs:
            self.model420.action_generar_mod420()
        jar = self.env["ir.attachment"].search([("name", "=", "pa-mod420.jar")])
        self.assertFalse(jar.store_fname)
        self.assertEqual(runs[0]["jar"], b"ATC program")
        self.assertEqual(self._generated_files().name, "modelo420.dec")

    def test_model_420_atc_sequence_and_payment_type(self):
        """A new 420 takes its number from the ATC sequence of the company and
        is paid telematically when it is filed telematically."""
        Report = self.env["l10n.es.atc.mod420.report"]
        values = {
            "company_id": self.company.id,
            "company_vat": "A58818501",
            "contact_name": "Test owner",
            "contact_phone": "911234455",
            "year": 2026,
            "period_type": "2T",
            "date_start": "2026-04-01",
            "date_end": "2026-06-30",
            "journal_id": self.journal_misc.id,
        }
        # create() writes the number in the values it gets
        telematic = Report.create(dict(values))
        sequence = self.env["ir.sequence"].search(
            [("company_id", "=", self.company.id), ("name", "=", "atc420-sequence")]
        )
        self.assertEqual(sequence.code, "atc.sequence.type")
        self.assertEqual(telematic.name, "4200000000001")
        self.assertEqual(telematic.output_type, "T")
        self.assertEqual(telematic.payment_type, "5")
        draft = Report.create(
            dict(
                values,
                period_type="3T",
                date_start="2026-07-01",
                date_end="2026-09-30",
                output_type="B",
            )
        )
        self.assertFalse(draft.payment_type)


@tagged("post_install", "-at_install")
class TestL10nEsAtcMod420CoreTaxes(TestL10nEsAtcMod420Base):
    """IGIC taxes of the Odoo core chart that the model did not include before."""

    taxes_sale: ClassVar[dict] = {}
    taxes_purchase: ClassVar[dict] = {
        "l10n_es.account_tax_template_igic_sop_3_s": (1000, 30),
        "l10n_es.account_tax_template_igic_ISP5": (1100, 55),
        "l10n_es.account_tax_template_igic_p_re05": (1200, 6),
        "l10n_es.account_tax_template_igic_sop_i_5": (1300, 65),
        "l10n_es.account_tax_template_igic_sop_i_5_inv": (1400, 70),
    }

    def test_model_420_core_taxes(self):
        purchase = self._invoice_purchase_create("2026-01-10")
        self._invoice_refund(purchase, "2026-01-20")
        self.model420.button_calculate()
        expected = {
            "19": 1100,  # reverse charge (output IGIC)
            "20": 55,
            "21": -1100,  # its refund, in the modification boxes
            "22": -55,
            "26": 1000 + 1100 + 1200,  # domestic goods and services
            "27": 30 + 55 + 6,
            "30": 1300,  # imports of goods
            "31": 65,
            "32": 1400,  # imports of investment goods
            "33": 70,
            # The refund rectifies the deductions of all of them
            "34": -(1000 + 1100 + 1200 + 1300 + 1400),
            "35": -(30 + 55 + 6 + 65 + 70),
        }
        for field, amount in expected.items():
            lines = self.model420.tax_line_ids.filtered(
                lambda x, field=field: x.field_number == int(field)
            )
            self.assertAlmostEqual(sum(lines.mapped("amount")), amount, 2, field)


@tagged("post_install", "-at_install")
class TestL10nEsAtcMod420Map(TestL10nEsAtcMod420Base):
    """The map follows the tags of the model 420 boxes that Odoo core puts on
    the IGIC taxes, so a tax that Odoo core adds or moves is caught here."""

    # Odoo core takes the refunds of reverse charge purchases to the boxes of
    # the invoices (19, 20) with the opposite sign; the map of this module takes
    # them to the modification boxes (21, 22) instead
    refund_boxes = {19: 21, 20: 22}  # noqa: RUF012

    def test_map_follows_the_core_tags(self):
        self.model420.button_calculate()
        map_lines = self.model420.tax_line_ids.map_line_id
        taxes = (
            self.env["account.tax"]
            .with_context(active_test=False)
            .search([("company_id", "=", self.company.id)])
        )
        missing = []
        for tax in taxes:
            for document, repartition in (
                ("regular", tax.invoice_repartition_line_ids),
                ("refund", tax.refund_repartition_line_ids),
            ):
                for tag in repartition.tag_ids:
                    box = re.search(r"mod420\[(\d+)\]", tag.name)
                    if not box:
                        continue
                    box = int(box[1])
                    if document == "refund":
                        box = self.refund_boxes.get(box, box)
                    if not map_lines.filtered(
                        lambda line, box=box, document=document, tax=tax: (
                            line.field_number == box
                            and line.move_type in (document, "all")
                            and tax in line.get_taxes_for_company(self.company)
                        )
                    ):
                        missing.append(f"{tax.name} {document} [{box}]")
        self.assertFalse(missing)
