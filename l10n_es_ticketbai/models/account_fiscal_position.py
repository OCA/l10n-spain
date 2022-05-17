# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    tbai_vat_regime_key = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime Key", copy=False
    )
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 2nd Key", copy=False
    )
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 3rd Key", copy=False
    )
    tbai_vat_exemption_ids = fields.One2many(
        comodel_name="account.fp.tbai.tax", inverse_name="position_id"
    )


class AccountFiscalPositionTicketBAITax(models.Model):
    _name = "account.fp.tbai.tax"
    _description = "TicketBAI - Fiscal Position Tax Exemptions"
    _rec_name = "tbai_vat_exemption_key"

    position_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        string="Fiscal Position",
        required=True,
        ondelete="cascade",
    )
    tax_id = fields.Many2one(
        comodel_name="account.tax", string="Tax", required=True, ondelete="cascade"
    )
    tbai_vat_exemption_key = fields.Many2one(
        comodel_name="tbai.vat.exemption.key",
        string="VAT Exemption Key",
        required=True,
        ondelete="restrict",
    )

    _sql_constraints = [
        (
            "position_tax_uniq",
            "UNIQUE(position_id,tax_id)",
            _("Tax must be unique per fiscal position!"),
        )
    ]
