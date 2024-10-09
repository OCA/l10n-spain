from odoo import _, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    ##############
    # Pymes Canary
    ##############

    @template("es_pymes_canary")
    def _get_es_pymes_canary_template_data(self):
        return {
            "name": _("PyMEs (2008) - Islas Canarias"),
            "parent": "es_common",
        }

    @template("es_pymes_canary", "res.company")
    def _get_es_pymes_canary_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.es",
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "57299",
                "account_sale_tax_id": "account_tax_template_s_igic7b",
                "account_purchase_tax_id": "account_tax_template_p_igic7_bc",
            },
        }

    #############
    # Full Canary
    #############

    @template("es_full_canary")
    def _get_es_full_canary_template_data(self):
        return {
            "name": _("Completo (2008) - Islas Canarias"),
            "parent": "es_common",
        }

    @template("es_full_canary", "res.company")
    def _get_es_full_canary_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.es",
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "57299",
                "account_sale_tax_id": "account_tax_template_s_igic7b",
                "account_purchase_tax_id": "account_tax_template_p_igic7_bc",
            },
        }

    #######
    # Assoc
    #######

    @template("es_assoc_canary")
    def _get_es_assoc_canary_template_data(self):
        return {
            "name": _("Entidades sin ánimo de lucro (2008) - Islas Canarias"),
            "parent": "es_common",
        }

    @template("es_assoc_canary", "res.company")
    def _get_es_assoc_canary_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.es",
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "57299",
                "account_sale_tax_id": "account_tax_template_s_igic7b",
                "account_purchase_tax_id": "account_tax_template_p_igic7_bc",
            },
        }
