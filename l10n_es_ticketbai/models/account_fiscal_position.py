# Copyright 2021 Binovo IT Human Project SL
# Copyright 2022 Soluciones Tecnológicas Freedoo S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, _


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    tbai_vat_regime_key = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime Key', copy=False)
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime 2nd Key', copy=False)
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name='tbai.vat.regime.key', string='VAT Regime 3rd Key', copy=False)
