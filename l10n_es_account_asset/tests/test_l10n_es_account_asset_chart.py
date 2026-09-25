# Copyright 2026 Binhex System Solutions
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest import mock

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

    def test_hook_keeps_core_data_without_oca_assets(self):
        """The standard asset models must still be seeded when OCA is absent."""
        chart_template = self.env["account.chart.template"]
        self.assertTrue(chart_template._is_oca_asset_management())
        with mock.patch.object(
            type(chart_template), "_is_oca_asset_management", return_value=False
        ):
            for hook in (
                "_get_es_canary_pymes_account_asset",
                "_get_es_canary_full_account_asset",
                "_get_es_canary_assoc_account_asset",
            ):
                data = getattr(chart_template, hook)()
                self.assertIn("asset_common_research", data, hook)
