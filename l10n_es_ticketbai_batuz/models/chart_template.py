# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position.template"

    tbai_vat_regime_purchase_key = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="VAT Regime Key for purchases",
        domain=[("type", "=", "purchase")],
        copy=False,
    )
    tbai_vat_regime_purchase_key2 = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="VAT Regime 2nd Key for purchases",
        domain=[("type", "=", "purchase")],
        copy=False,
    )
    tbai_vat_regime_purchase_key3 = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="VAT Regime 3rd Key for purchases",
        domain=[("type", "=", "purchase")],
        copy=False,
    )
    tbai_vat_regime_key = fields.Many2one(domain=[("type", "=", "sale")])
    tbai_vat_regime_key2 = fields.Many2one(domain=[("type", "=", "sale")])
    tbai_vat_regime_key3 = fields.Many2one(domain=[("type", "=", "sale")])


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    @api.multi
    def _get_fp_vals(self, company, position):
        res = super()._get_fp_vals(company, position)
        res.update({
            "tbai_vat_regime_purchase_key": position.tbai_vat_regime_purchase_key.id,
            "tbai_vat_regime_purchase_key2": position.tbai_vat_regime_purchase_key2.id,
            "tbai_vat_regime_purchase_key3": position.tbai_vat_regime_purchase_key3.id,
        })
        return res
