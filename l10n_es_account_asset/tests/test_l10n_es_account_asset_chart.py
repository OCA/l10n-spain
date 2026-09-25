# Copyright 2026 Binhex System Solutions
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import odoo.tests.common as common


class TestL10nEsAccountAssetChart(common.TransactionCase):
    def test_load_canary_chart(self):
        """Canary charts must load with the OCA asset model installed."""
        company = self.env["res.company"].create(
            {
                "name": "Canary test company",
                "currency_id": self.env.ref("base.EUR").id,
            }
        )
        # `_load` is the entry point already used by the shared AEAT test base
        # (see l10n_es_aeat/tests/test_l10n_es_aeat_mod_base.py): `try_loading`
        # warns when the registry is not fully loaded, which fails OCA's log
        # check.
        self.env["account.chart.template"]._load(
            template_code="es_canary_pymes", company=company, install_demo=False
        )
        self.assertEqual(company.chart_template, "es_canary_pymes")
