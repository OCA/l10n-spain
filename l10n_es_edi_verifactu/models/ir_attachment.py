# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api
from odoo.tools import xml_utils


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def action_download_xsd_files(self):
        xml_utils.load_xsd_files_from_url(
            self.env,
            "http://schemas.xmlsoap.org/soap/envelope/",
            "soap-envelope.xsd",
            xsd_name_prefix="l10n_es_verifactu",
        )
        xml_utils.load_xsd_files_from_url(
            self.env,
            "https://prewww2.aeat.es/static_files/common/internet/dep/aplicaciones/es/aeat/tikeV1.0/cont/ws/SuministroLR.xsd",
            "SuministroLR.xsd",
            xsd_name_prefix="l10n_es_verifactu",
        )
        xml_utils.load_xsd_files_from_url(
            self.env,
            "https://prewww2.aeat.es/static_files/common/internet/dep/aplicaciones/es/aeat/tikeV1.0/cont/ws/SuministroInformacion.xsd",
            "SuministroInformacion.xsd",
            xsd_name_prefix="l10n_es_verifactu",
        )
        return super().action_download_xsd_files()
