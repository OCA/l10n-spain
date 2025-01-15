# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv.expression import OR


class PosSession(models.Model):
    _inherit = "pos.session"

    def _pos_ui_models_to_load(self):
        res = super()._pos_ui_models_to_load()
        if self.config_id.tbai_enabled:
            res.extend(["tbai.invoice", "tbai.tax.agency", "tbai.vat.regime.key"])
        return res

    def _loader_params_res_company(self):
        res = super()._loader_params_res_company()
        if self.config_id.tbai_enabled:
            res["search_params"]["fields"] += [
                "tbai_enabled",
                "tbai_test_enabled",
                "tbai_license_key",
                "tbai_developer_id",
                "tbai_software_name",
                "tbai_software_version",
                "tbai_tax_agency_id",
                "tbai_protected_data",
                "tbai_protected_data_txt",
                "tbai_vat_regime_simplified",
            ]
        return res

    def _loader_params_res_partner(self):
        res = super()._loader_params_res_partner()
        if self.config_id.tbai_enabled:
            res["search_params"]["fields"] += [
                "tbai_partner_idtype",
                "tbai_partner_identification_number",
            ]
            tbai_developer = self.config_id.company_id.tbai_developer_id
            if res["search_params"]["domain"]:
                res["search_params"]["domain"] = OR(
                    [
                        res["search_params"]["domain"],
                        [("id", "=", tbai_developer.id), ("customer_rank", "=", 0)],
                    ]
                )
        return res

    def _loader_params_tbai_invoice(self):
        return {
            "search_params": {
                "domain": [("id", "=", self.config_id.tbai_last_invoice_id.id)],
                "fields": [
                    "signature_value",
                    "number_prefix",
                    "number",
                    "expedition_date",
                ],
            },
        }

    def _get_pos_ui_tbai_invoice(self, params):
        return self.env["tbai.invoice"].search_read(**params["search_params"])

    def _pos_data_process_tbai_invoice(self, loaded_data):
        if loaded_data["tbai.invoice"]:
            tbai_last_invoice_data = loaded_data["tbai.invoice"][0]
            tbai_last_invoice_data["order"] = {
                "simplified_invoice": (
                    f"{tbai_last_invoice_data['number_prefix']}"
                    f"{tbai_last_invoice_data['number']}"
                )
            }
            loaded_data["tbai_last_invoice_data"] = tbai_last_invoice_data

    def _loader_params_tbai_tax_agency(self):
        return {
            "search_params": {
                "domain": [
                    ("id", "=", self.config_id.company_id.tbai_tax_agency_id.id)
                ],
                "fields": ["version", "qr_base_url", "test_qr_base_url"],
            },
        }

    def _get_pos_ui_tbai_tax_agency(self, params):
        return self.env["tbai.tax.agency"].search_read(**params["search_params"])

    def _pos_data_process_tbai_tax_agency(self, loaded_data):
        tbai_tax_agency = loaded_data["tbai.tax.agency"][0]
        loaded_data["tbai_version"] = tbai_tax_agency["version"]
        loaded_data["tbai_qr_base_url"] = (
            tbai_tax_agency["test_qr_base_url"]
            if self.config_id.company_id.tbai_test_enabled
            else tbai_tax_agency["qr_base_url"]
        )

    def _loader_params_tbai_vat_regime_key(self):
        return {"search_params": {"fields": ["code"]}}

    def _get_pos_ui_tbai_vat_regime_key(self, params):
        return self.env["tbai.vat.regime.key"].search_read(**params["search_params"])

    def _pos_data_process_tbai_vat_regime_key(self, loaded_data):
        loaded_data["tbai_vat_regime_keys"] = loaded_data["tbai.vat.regime.key"]

    def _pos_data_process(self, loaded_data):
        res = super()._pos_data_process(loaded_data)
        if self.config_id.tbai_enabled:
            self._pos_data_process_tbai_invoice(loaded_data)
            self._pos_data_process_tbai_tax_agency(loaded_data)
            self._pos_data_process_tbai_vat_regime_key(loaded_data)
        return res
