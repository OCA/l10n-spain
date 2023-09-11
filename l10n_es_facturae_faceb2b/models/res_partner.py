# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from odoo import _, api, exceptions, fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    l10n_es_facturae_sending_code = fields.Selection(
        selection_add=[("faceb2b", "FACe B2B")]
    )
    facturae_faceb2b_dire = fields.Char()

    @api.constrains(
        "facturae",
        "vat",
        "country_id",
        "state_id",
        "l10n_es_facturae_sending_code",
    )
    def _constrain_l10n_es_facturae_sending_code_faceb2b(self):
        for record in self:
            if (
                not record.l10n_es_facturae_sending_code
                or record.l10n_es_facturae_sending_code not in ["faceb2b"]
            ):
                continue
            if not record.facturae:
                raise exceptions.ValidationError(
                    _("Facturae must be selected in order to send to FACeB2B")
                )
            if not record.vat:
                raise exceptions.ValidationError(
                    _("Vat must be defined in order to send to FACeB2B")
                )
            if not record.country_id:
                raise exceptions.ValidationError(
                    _("Country must be defined in order to send to FACeB2B")
                )
            if record.country_id.code_alpha3 == "ESP":
                if not record.state_id:
                    raise exceptions.ValidationError(
                        _("State must be defined in Spain in order to send to FACeB2B")
                    )

    def _get_facturae_backend(self):
        if self.l10n_es_facturae_sending_code == "faceb2b":
            return self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend")
        return super()._get_facturae_backend()

    def _get_facturae_exchange_type(self):
        if self.l10n_es_facturae_sending_code == "faceb2b":
            return self.env.ref(
                "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_type"
            )
        return super()._get_facturae_exchange_type()

    def check_faceb2b_information(self):
        self.ensure_one()
        api_key = self.env["ir.config_parameter"].sudo().get_param("dire.ws.apikey")
        ws = self.env["ir.config_parameter"].sudo().get_param("dire.ws")
        if not api_key or not self.vat or self.country_id.code != "ES":
            return
        _country_code, _identifier_type, vat_number = self._parse_aeat_vat_info()
        response = requests.get(
            "%s/%s" % (ws, vat_number), headers={"User-Agent": "", "apikey": api_key}
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            return
        result = response.json()
        self.write(
            {
                "facturae": True,
                "l10n_es_facturae_sending_code": "faceb2b",
                "facturae_faceb2b_dire": result["code"],
            }
        )
