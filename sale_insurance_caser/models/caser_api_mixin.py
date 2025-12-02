# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

import requests

from odoo import fields, models


class CaserApiMixin(models.AbstractModel):
    _name = "caser.api.mixin"
    _description = "Caser API Integration Mixin"

    def _is_caser_production(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_insurance_caser.is_production")
            == "True"
        )

    def _get_caser_endpoint(self):
        return (
            "https://wm.caser.es/web-services/ServicioPSM"
            if self._is_caser_production()
            else "https://wmtest.caser.es/web-services/ServicioPSM"
        )

    def _get_caser_schema_url(self):
        return (
            "http://wm.caser.es/psm/"
            if self._is_caser_production()
            else "http://wmtest.caser.es/psm/"
        )

    def _wrap_in_soap_envelope(self, xml_content):
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Header/>
    <soapenv:Body>
        <ns0:ejecutar xmlns:ns0="http://tempuri.org/">
            <xmlFile><![CDATA[{xml_content}]]></xmlFile>
        </ns0:ejecutar>
    </soapenv:Body>
</soapenv:Envelope>"""

    def _get_caser_config_params(self):
        config = self.env["ir.config_parameter"].sudo()
        return {
            "agency_code": config.get_param(
                "sale_insurance_caser.agency_code",
            ),
            "agent_code": config.get_param("sale_insurance_caser.agent_code"),
            "sica_code": config.get_param("sale_insurance_caser.sica_code"),
            "web_username": config.get_param("sale_insurance_caser.username"),
        }

    def _get_caser_policy_dates(self):
        effective_date = fields.Datetime.now()
        expiration_date = effective_date + timedelta(days=365)
        return effective_date, expiration_date

    def _send_caser_soap_request(self, endpoint, soap_envelope, timeout=30):
        headers = {"Content-Type": "application/xml; charset=utf-8"}
        return requests.post(
            endpoint,
            data=soap_envelope.encode("utf-8"),
            headers=headers,
            timeout=timeout,
        )
