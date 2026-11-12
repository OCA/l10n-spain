# Copyright 2023 Binhex - Nicolás Ramos
# Copyright 2024 Binhex - Christian Ramos
# Copyright 2025 Tecnativa - Carlos Lopez
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
from odoo.tests import tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)
from odoo.addons.l10n_es_atc.models import l10n_es_atc_report

_logger = logging.getLogger("atc.417")


@tagged("post_install", "-at_install")
class TestL10nEsAtcmod417Base(TestL10nEsAeatModBase):
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
        cls.model417 = cls.env["l10n.es.atc.mod417.report"].create(
            {
                "name": "9990000000417",
                "company_id": cls.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2026,
                "period_type": "01",
                "date_start": "2026-01-01",
                "date_end": "2026-01-31",
                "journal_id": cls.journal_misc.id,
            }
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
            zip_file.writestr("M417/lib/pa-mod417.jar", b"ATC program")
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
                ("res_model", "=", self.model417._name),
                ("res_id", "=", self.model417.id),
            ]
        )


class TestL10nEsAeatmod417(TestL10nEsAtcmod417Base):
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
        cls.bank_account = cls.env["res.partner.bank"].create(
            {
                "account_number": "ES9121000418450200051332",
                "partner_id": cls.model417.company_id.partner_id.id,
            }
        )

    def _check_tax_lines(self):
        for field, result in iter(self.taxes_result.items()):
            _logger.debug(f"Checking tax line: {field}")
            lines = self.model417.tax_line_ids.filtered(
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
            "477700",
        }
        for code in codes:
            cls.accounts[code] = cls.env["account.account"].search(
                [("company_ids", "in", [cls.company.id]), ("code", "=", code)]
            )
        return True

    def _set_f417_fields(self):
        self.model417.company_vat = "A58818501"
        # Countries, cities and company data are administrator data, and the
        # tests run as the BaseCommon test user since 20.0
        country_spain = self.env.ref("base.es")
        country_spain.sudo().enforce_cities = True
        las_palmas_city = (
            self.env["res.city"]
            .sudo()
            .create(
                {
                    "name": "Las Palmas de Gran Canaria",
                    "code": "35016",
                    "country_id": country_spain.id,
                }
            )
        )
        self.model417.company_id.sudo().write(
            {
                "street": "Test street",
                "zip": "35001",
                "atc_public_way": "CL",
                "city_id": las_palmas_city.id,
            }
        )

    @freeze_time("2026-02-01")
    def test_model_417(self):
        _logger.debug("Calculate ATC 417 01 2026")
        self.model417.button_calculate()
        # Test default counterpart.
        self.assertEqual(
            self.model417.counterpart_account_id.id, self.accounts["475000"].id
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
        subtotal = round(devengado - deducir, 3)
        # Result shown after calculating, before filling the manual boxes
        self.assertAlmostEqual(self.model417.resultado_autoliquidacion, subtotal, 2)
        self.model417.write(
            {
                "regularizacion_cuotas": 150,
                "a_deducir": 30,
                "cuotas_compensar": 20,
            }
        )
        result = round(subtotal + 150 - 30 - 20, 3)
        self.assertAlmostEqual(self.model417.total_devengado, devengado, 2)
        self.assertAlmostEqual(self.model417.total_deducir, deducir, 2)
        self.assertAlmostEqual(self.model417.resultado_autoliquidacion, result, 2)

        self.assertEqual(self.model417.result_type, "I")
        # The form shows the button that creates the move
        self.assertTrue(self.model417.allow_posting)
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
        self.assertIn("475000", codes)
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

    def test_model_417_result_type(self):
        """A negative result is carried forward to the next month, except in
        December, when it is refunded."""
        self.model417.button_calculate()
        self.model417.a_deducir = self.model417.diferencia + 100
        self.assertAlmostEqual(self.model417.resultado_autoliquidacion, -100, 2)
        self.assertEqual(self.model417.result_type, "C")
        self.model417.period_type = "12"
        self.assertEqual(self.model417.result_type, "D")

    @freeze_time("2026-02-01")
    def test_model_417_declaration_dec(self):
        """The telematic file is the XML of the declaration run through the ATC
        program: amounts in cents, the province by its ATC code and the result.
        """
        self.model417.button_calculate()
        self._check_tax_lines()
        self.assertEqual(self.model417.result_type, "I")
        # check configuration
        with self.assertRaisesRegex(UserError, r".*The company .* has no street.*"):
            self.model417.action_generar_mod417()
        self._set_f417_fields()
        self.assertEqual(self.model417.output_type, "T")
        # Set a payment_type different from 5 (Pago telemático); an error is expected.
        self.model417.payment_type = "1"  # Efectivo
        with self.assertRaisesRegex(
            UserError, r".*payment type is not compatible with the output type.*"
        ):
            self.model417.action_generar_mod417()
        self.model417.payment_type = "5"  # Pago telemático
        with self._atc_program() as runs:
            action = self.model417.action_generar_mod417()
        self.assertEqual(runs[0]["S"], "T")
        self.assertEqual(runs[0]["jar"], b"ATC program")
        generated = self._generated_files()
        self.assertEqual(generated.name, "modelo417.dec")
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], f"/web/content/{generated.id}?download=true")
        dec_node = etree.fromstring(generated.raw.content)
        self.assertEqual(dec_node.tag, "DEC")
        self.assertEqual(dec_node.attrib["MOD"], "417")
        self.assertEqual(dec_node.attrib["ANY"], "2026")
        self.assertEqual(dec_node.attrib["PER"], "01")
        otp_node = dec_node.xpath("//IDE/OTP")
        self.assertEqual(len(otp_node), 1)
        otp_node = otp_node[0]
        self.assertEqual(otp_node.attrib["NIF"], "A58818501")
        self.assertEqual(otp_node.attrib["PAI"], "ES")
        self.assertEqual(otp_node.attrib["POP"], "35")
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
        self.assertFalse(res_node[0].attrib.get("IBAN"))

    @freeze_time("2026-02-01")
    def test_model_417_declaration_direct_debit(self):
        """Paid by direct debit, the file carries the IBAN of the bank account."""
        self.model417.button_calculate()
        self._set_f417_fields()
        self.model417.payment_type = "4"  # Domiciliación bancaria
        with self.assertRaisesRegex(UserError, r".*Select a bank account.*"):
            self.model417.action_generar_mod417()
        self.model417.partner_bank_id = self.bank_account
        with self._atc_program():
            self.model417.action_generar_mod417()
        dec_node = etree.fromstring(self._generated_files().raw.content)
        res_node = dec_node.xpath("//RES")[0]
        self.assertEqual(res_node.attrib["FPA"], "4")
        self.assertEqual(res_node.attrib["IBAN"], "ES9121000418450200051332")

    @freeze_time("2026-02-01")
    def test_model_417_declaration_pdf(self):
        """A draft is a PDF made by the same program with output type B."""
        self.model417.button_calculate()
        self._set_f417_fields()
        self.model417.output_type = "B"
        self.model417.payment_type = "1"  # Efectivo
        with self._atc_program() as runs:
            self.model417.action_generar_mod417()
        self.assertEqual(runs[0]["S"], "B")
        self.assertEqual(self._generated_files().name, "modelo417.pdf")
