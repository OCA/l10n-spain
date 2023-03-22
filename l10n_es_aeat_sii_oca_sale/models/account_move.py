# Copyright 2023 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("partner_shipping_id")
    def _onchange_partner_shipping_id(self):
        super()._onchange_partner_shipping_id()
        self.onchange_fiscal_position_id_l10n_es_aeat_sii()

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        super()._onchange_partner_id()
        self.onchange_fiscal_position_id_l10n_es_aeat_sii()
