# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _get_account_vals(self, company, account_template, code_acc, tax_template_ref):
        res = super(AccountChartTemplate, self)._get_account_vals(
            company, account_template, code_acc, tax_template_ref
        )
        search_charts = [
            self.env.ref("l10n_es_coop.account_chart_template_coop_pyme").name,
            self.env.ref("l10n_es_coop.account_chart_template_coop_full").name,
        ]
        if account_template.chart_template_id.name in search_charts:
            search_accounts = [
                self.env.ref("l10n_es_coop.pgc_coop_pyme_1000_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_112_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_113_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_1500_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_1710_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_5020_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_5210_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_526_child").name,
                self.env.ref("l10n_es_coop.pgc_coop_pyme_55850_child").name,
            ]
            if account_template.name in search_accounts:
                account = self.env["account.account"].search(
                    [("code", "=", res["code"])]
                )
                account.unlink()

        return res
