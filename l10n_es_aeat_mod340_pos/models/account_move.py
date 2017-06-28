# -*- coding: utf-8 -*-
# Copyright 2017 - Aselcis Consulting (http://www.aselcis.com)
#                - Miguel Paraíso <miguel.paraiso@aselcis.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.one
    @api.depends('journal_id')
    def _compute_comes_from_pos_order(self):
        # Check if account move comes from pos order through the journal
        for pos_config in self.env['pos.config'].search([]):
            if self.journal_id == pos_config.journal_id:
                self.comes_from_pos_order = True
                break

    @api.one
    @api.depends('line_ids')
    def _compute_mod340_operation_key(self):
        super(AccountMove, self)._compute_mod340_operation_key()
        if self.comes_from_pos_order:
            self.mod340_operation_key = 'J'

    comes_from_pos_order = fields.Boolean(
        compute='_compute_comes_from_pos_order', string='POS Order',
        store=True,
        index=True)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pos_order_id = fields.Many2one('pos.order', string="POS Order")
