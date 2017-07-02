# -*- coding: utf-8 -*-
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, exceptions, fields, models, _


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    vat_prorrate_percent = fields.Float(string="Prorrate perc.", default=100)

    @api.multi
    @api.constrains('vat_prorrate_percent')
    def check_vat_prorrate_percent(self):
        for line in self:
            if not (0 < line.vat_prorrate_percent <= 100):
                raise exceptions.ValidationError(
                    _('VAT prorrate percent must be between 0.01 and 100'))

    @api.one
    def asset_create(self):
        """Increase asset gross value by the vat prorrate percentage."""
        # HACK: There's no way to inherit method knowing the created asset
        prev_assets = self.env['account.asset.asset'].search([])
        res = super(AccountInvoiceLine, self).asset_create()
        if self.vat_prorrate_percent == 100 or not self.asset_category_id:
            return res
        current_assets = self.env['account.asset.asset'].search([])
        asset = current_assets - prev_assets
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        totals = self.invoice_line_tax_ids.compute_all(
            price, currency=self.invoice_id.currency_id,
            quantity=self.quantity, product=self.product_id,
            partner=self.invoice_id.partner_id,
        )
        total_tax = totals['total_included'] - totals['total_excluded']
        increment = total_tax * (100 - self.vat_prorrate_percent) / 100
        asset.write({
            'value': self.price_subtotal + increment,
            'vat_prorrate_percent': self.vat_prorrate_percent,
            'vat_prorrate_increment': increment,
        })
        # Recompute depreciation board for applying new purchase value
        asset.compute_depreciation_board()
        return res
