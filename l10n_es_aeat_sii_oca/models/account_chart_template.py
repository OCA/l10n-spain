from odoo import models

from odoo.addons.account.models.chart_template import template

IGIC_TAXES_WITHOUT_APPLICABILITY = [
    *(f"igic_sop_{rate}_s" for rate in ("0", "3", "5", "7", "9_5", "15", "20")),
    "igic_ISP5",
]


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", "account.fiscal.position")
    def _get_es_common_account_fiscal_position_sii(self):
        return self._parse_csv(
            "es_common",
            "account.fiscal.position",
            module="l10n_es_aeat_sii_oca",
        )

    @template("es_common", "account.tax")
    def _get_es_common_account_tax_sii(self):
        # Services to non-EU customers are not subject (location rules), not
        # exports: with the export key 02 the AEAT rejects an invoice of only
        # those services (error 1252) and one that mixes them with exported
        # goods needs 01 + 02 (https://github.com/odoo/odoo/pull/301554).
        taxes = {
            "account_tax_template_s_iva_e": {"l10n_es_regime_code": False},
            # Intra-community purchase of current goods at 10 %, as the 4 % and
            # 21 % ones: the core marks it as an investment good
            "account_tax_template_p_iva10_ic_bc": {"l10n_es_bien_inversion": False},
            # REAGYP compensation of livestock and fishing, as the agriculture
            # one (p_iva12_agr): the core leaves it without type nor key
            "account_tax_template_p_iva105_gan": {
                "l10n_es_type": "sujeto_agricultura",
                "l10n_es_regime_code": "02_purchase",
            },
            # Services from outside the EU are a reverse charge, as the 21 %
            # one (p_iva21_sp_ex) and as the SII map sent them
            "account_tax_template_p_iva0_isc": {"l10n_es_type": "sujeto_isp"},
        }
        # IGIC taxes that the core leaves without applicability, so that they
        # are not reported to the SII of the AEAT, which is only for the VAT
        taxes.update(
            {
                f"account_tax_template_{xml_id}": {"l10n_es_applicability": "03"}
                for xml_id in IGIC_TAXES_WITHOUT_APPLICABILITY
            }
        )
        return taxes
