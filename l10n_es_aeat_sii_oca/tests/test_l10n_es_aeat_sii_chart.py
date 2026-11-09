# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestL10nEsAeatSiiChart(BaseCommon):
    def test_new_company_sii_chart_data(self):
        """A company created with the Spanish chart gets the forced SII keys of
        the business premises lease fiscal positions, and no export key on the
        services to non-EU customers."""
        company = (
            self.env["res.company"]
            .sudo()
            .create(
                {"name": "SII chart company", "country_id": self.env.ref("base.es").id}
            )
        )
        self.env["account.chart.template"].sudo().try_loading(
            "es_full", company=company, install_demo=False
        )
        chart = self.env["account.chart.template"].sudo().with_company(company)
        domestic = chart.ref("l10n_es_domestic_fiscal_position")
        self.assertFalse(domestic.sii_regime_code_sale)
        self.assertFalse(domestic.sii_regime_code_purchase)
        self.assertFalse(chart.ref("fp_extra").sii_regime_code_sale)
        lease = chart.ref("fp_irpf19a")
        self.assertEqual(lease.sii_regime_code_sale, "11")
        self.assertEqual(lease.sii_regime_code_purchase, "12_purchase")
        self.assertFalse(chart.ref("account_tax_template_s_iva_e").l10n_es_regime_code)
        self.assertEqual(
            chart.ref("account_tax_template_s_iva0_g_e").l10n_es_regime_code, "02_sale"
        )
