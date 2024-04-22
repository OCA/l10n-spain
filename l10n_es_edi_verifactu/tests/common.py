# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account_edi.tests.common import AccountEdiTestCommon


class TestEdiVerifactuCommon(AccountEdiTestCommon):
    @classmethod
    def setUpClass(
        cls,
        chart_template_ref="l10n_es.account_chart_template_full",
        edi_format_ref="l10n_es_edi_verifactu.edi_es_verifactu",
    ):
        super().setUpClass(
            chart_template_ref=chart_template_ref, edi_format_ref=edi_format_ref
        )
        cls.company_data["company"].write(
            {
                "name": "Binovo IT Human Project",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_ss").id,
                "vat": "ES93074269P",
                "l10n_es_edi_test_env": True,
            }
        )
        cls.env["ir.attachment"].action_download_xsd_files()
