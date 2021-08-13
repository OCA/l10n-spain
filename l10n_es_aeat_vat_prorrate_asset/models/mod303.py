# Copyright 2015-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    def _calculate_casilla_44(self):
        super(L10nEsAeatMod303Report, self)._calculate_casilla_44()
        for report in self:
            if report.vat_prorrate_type != "general" or report.period_type not in (
                "4T",
                "12",
            ):
                continue
            assets = self.env["account.asset"].search(
                [("date_start", "like", "{}%".format(report.year))]
            )
            result = report.casilla_44
            for asset in assets.filtered("vat_prorrate_percent"):
                original_taxes = (
                    asset.vat_prorrate_increment
                    * 100
                    / (100 - asset.vat_prorrate_percent)
                )
                real_increment = (
                    original_taxes * (100 - report.vat_prorrate_percent) / 100
                )
                result += asset.vat_prorrate_increment - real_increment
            report.casilla_44 = round(result, 2)
