# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

IGIC_RATES = ("0", "3", "5", "7", "9_5", "15", "20")


def igic_tax_data():
    """Spanish data that the IGIC taxes need for the SII of the Canary tax
    agency and that the core leaves at their defaults (subject, without
    investment good, exempt reason or registration key), so that the SII
    breakdown and keys are built from them as for the VAT taxes."""
    data = {
        # Reverse charge
        "igic_s_ISP0": {"l10n_es_type": "sujeto_isp"},
        **{
            f"igic_ISP{rate}": {"l10n_es_type": "sujeto_isp"}
            for rate in ("0", "3", "5", "7", "95", "15", "20")
        },
        # Import surcharge of the retail traders, who report their imports
        # with the key 15 (ATC FAQ 8.1)
        **{
            f"igic_p_re{rate}": {
                "l10n_es_type": "recargo",
                "l10n_es_regime_code": "15_igic_purchase",
            }
            for rate in ("0", "03", "05", "07", "095", "15", "20")
        },
        # Investment goods (the imported ones already have the flag)
        **{
            f"igic_sop_{rate}_inv": {"l10n_es_bien_inversion": True}
            for rate in IGIC_RATES
        },
        # Imports, documented by the customs declaration (DUA)
        **{
            f"igic_sop_i_{rate}{suffix}": {"l10n_es_type": "dua"}
            for rate in IGIC_RATES
            for suffix in ("", "_inv")
        },
        # Exempt: exports (art. 11 Law 20/1991, key 02, as the ATC rejects E2
        # with the key 01 alone), sales of the retail traders (art. 50 Law
        # 4/2012, key 17) and others
        "igic_ex_0": {
            "l10n_es_type": "exento",
            "l10n_es_exempt_reason": "E2",
            "l10n_es_regime_code": "02_sale",
        },
        "igic_re_ex": {"l10n_es_type": "exento"},
        "igic_cmino": {
            "l10n_es_type": "exento",
            "l10n_es_exempt_reason": "E1",
            "l10n_es_regime_code": "17_igic_sale",
        },
        "igic_p_ex": {"l10n_es_type": "exento"},
        "igic_sop_cmino": {"l10n_es_type": "exento"},
        # Not subject
        "s_igic_ns": {"l10n_es_type": "no_sujeto"},
        "p_igic_ns": {"l10n_es_type": "no_sujeto"},
    }
    return {f"account_tax_template_{xml_id}": vals for xml_id, vals in data.items()}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", "account.tax")
    def _get_es_common_account_tax_atc_sii(self):
        return igic_tax_data()
