# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

IGIC_RATES = ("0", "3", "5", "7", "9_5", "15", "20")


def igic_tax_data():
    """Spanish data of the IGIC taxes that the core leaves at their defaults
    (subject, without investment good), as the SII map of the Canary tax agency
    of the former versions classified them, so that the SII breakdown is built
    from them as for the VAT taxes."""
    data = {
        # Reverse charge
        "igic_s_ISP0": {"l10n_es_type": "sujeto_isp"},
        **{
            f"igic_ISP{rate}": {"l10n_es_type": "sujeto_isp"}
            for rate in ("0", "3", "5", "7", "95", "15", "20")
        },
        # Equivalence surcharge
        **{
            f"igic_p_re{rate}": {"l10n_es_type": "recargo"}
            for rate in ("0", "03", "05", "07", "095", "15", "20")
        },
        # Investment goods (the imported ones already have the flag)
        **{
            f"igic_sop_{rate}_inv": {"l10n_es_bien_inversion": True}
            for rate in IGIC_RATES
        },
        # Exempt: exports, retail traders and others
        "igic_ex_0": {"l10n_es_type": "exento"},
        "igic_re_ex": {"l10n_es_type": "exento"},
        "igic_cmino": {"l10n_es_type": "exento"},
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
