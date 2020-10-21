# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'l10n.es.mod190.mixin']

    @api.model
    def line_get_convert(self, line, part):
        """Copy from invoice to move lines"""
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['aeat_perception_key_id'] = line.get(
            'aeat_perception_key_id', False,
        )
        res['aeat_perception_subkey_id'] = line.get(
            'aeat_perception_subkey_id', False,
        )
        return res

    @api.model
    def invoice_line_move_line_get(self):
        """We pass on the operation key from invoice line to the move line"""
        ml_dicts = super(AccountInvoice, self).invoice_line_move_line_get()
        for ml_dict in ml_dicts:
            if 'invl_id' not in ml_dict:
                continue
            ml_dict['aeat_perception_subkey_id'] = (
                self.aeat_perception_subkey_id.id
            )
            ml_dict['aeat_perception_key_id'] = (
                self.aeat_perception_key_id.id
            )
        return ml_dicts

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.fiscal_position_id.aeat_perception_key_id:
            fp = self.fiscal_position_id
            self.aeat_perception_key_id = fp.aeat_perception_key_id
            self.aeat_perception_subkey_id = fp.aeat_perception_subkey_id
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if (
            res.fiscal_position_id.aeat_perception_key_id and
            'aeat_perception_key_id' not in vals
        ):
            # We need to apply this change in order to make it work when
            # automatic invoices are created (like tests)
            fp = res.fiscal_position_id
            res.aeat_perception_key_id = fp.aeat_perception_key_id
            res.aeat_perception_subkey_id = fp.aeat_perception_subkey_id
        return res
