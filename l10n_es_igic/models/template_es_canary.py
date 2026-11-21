from odoo import _, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common_canary")
    def _get_es_common_canary_template_data(self):
        return {
            "name": _("Común (2008) - Islas Canarias"),
            "visible": 0,
            "parent": "es_common",
        }

    @template("es_common_canary", "account.fiscal.position")
    def _get_es_common_canary_fiscal_position_notes(self):
        """Notas de las posiciones fiscales del regimen minorista. El CSV de
        plantillas de posicion fiscal del addon no usa la columna `note`; se
        aportan por codigo y se fusionan con los registros del CSV (ver
        _get_chart_template_data)."""
        return {
            "fp_retailer_canary": {
                "note": _(
                    "Régimen minorista: ventas (repercutido → exento minorista) "
                    "y compras locales a proveedor minorista (art. 29.3, carga "
                    "implícita 4727). Sin importaciones."
                ),
            },
            "fp_purchase_local_retailer_canary": {
                "note": _(
                    "Escenario B: empresa minorista - compras locales "
                    "(IGIC en coste, sin 4727)"
                ),
            },
            "fp_purchase_import_retailer_canary": {
                "note": _(
                    "Escenario B: empresa minorista - importaciones (IGIC en coste)"
                ),
            },
        }

    @template("es_common_canary", "res.company")
    def _get_es_common_canary_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.es",
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "57299",
                "account_sale_tax_id": "account_tax_template_igic_r_7",
                "account_purchase_tax_id": "account_tax_template_igic_sop_7",
            },
        }

    # The following block of code is needed to force the loading of the data from
    # a different module. The current method of loading charts of accounts allows
    # easy extension of the same chart, but makes it harder to use and extend.

    @template("es_common", "account.tax")
    def _get_es_common_force_account_tax(self):
        tax_data = self._parse_csv("es_common", "account.tax", module="l10n_es")
        self._deref_account_tags("es_full", tax_data)
        return tax_data

    @template("es_common", "account.tax.group")
    def _get_es_common_force_account_tax_group(self):
        return self._parse_csv("es_common", "account.tax.group", module="l10n_es")

    @template("es_common", "account.group")
    def _get_es_common_force_account_group(self):
        return self._parse_csv("es_common", "account.group", module="l10n_es")

    @template("es_common", "account.account")
    def _get_es_common_force_account_account(self):
        return self._parse_csv("es_common", "account.account", module="l10n_es")

    @template("es_common", "account.fiscal.position")
    def _get_es_common_force_account_fiscal_position(self):
        return self._parse_csv("es_common", "account.fiscal.position", module="l10n_es")

    @template("es_full_canary")
    def _get_es_full_canary_template_data(self):
        return {
            "name": _("Completo (2008) - Islas Canarias"),
            "parent": "es_common_canary",
        }

    @template("es_full_canary", "res.company")
    def _get_es_full_canary_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.es",
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "57299",
                "account_sale_tax_id": "account_tax_template_igic_r_7",
                "account_purchase_tax_id": "account_tax_template_igic_sop_7",
            },
        }

    @template("es_assoc_canary")
    def _get_es_assoc_canary_template_data(self):
        return {
            "name": _("Entidades sin ánimo de lucro (2008) - Islas Canarias"),
            "parent": "es_common_canary",
        }

    @template("es_assoc_canary", "res.company")
    def _get_es_assoc_canary_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.es",
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "57299",
                "account_sale_tax_id": "account_tax_template_igic_r_7",
                "account_purchase_tax_id": "account_tax_template_igic_sop_7",
            },
        }

    @template("es_pymes_canary")
    def _get_es_pymes_canary_template_data(self):
        return {
            "name": _("PyMEs (2008) - Islas Canarias"),
            "parent": "es_common_canary",
        }

    @template("es_pymes_canary", "res.company")
    def _get_es_pymes_canary_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.es",
                "bank_account_code_prefix": "572",
                "cash_account_code_prefix": "570",
                "transfer_account_code_prefix": "57299",
                "account_sale_tax_id": "account_tax_template_igic_r_7",
                "account_purchase_tax_id": "account_tax_template_igic_sop_7",
            },
        }
