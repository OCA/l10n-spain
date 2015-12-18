# -*- coding: utf-8 -*-
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, exceptions, fields, models, _


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

    @api.model
    def asset_create(self, lines):
        """Increase asset gross value by the vat prorrate percentage."""
        asset_model = self.env['account.asset.asset']
        res = super(AccountInvoiceLine, self).asset_create(lines)
        for line in lines:
            if line.asset_category_id and line.vat_prorrate_percent != 100:
                # There's no other way of finding the created asset
                # It can happen that there are more than one asset found
                # through this method, because there are 2 exact lines in the
                # invoice. In this case, only last prorrate is applied.
                assets = asset_model.search(
                    [('name', '=', line.name),
                     ('category_id', '=', line.asset_category_id.id),
                     ('purchase_value', '=', line.price_subtotal),
                     ('partner_id', '=', line.invoice_id.partner_id.id),
                     ('company_id', '=', line.invoice_id.company_id.id),
                     ('purchase_date', '=', line.invoice_id.date_invoice)])
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                totals = line.invoice_line_tax_id.compute_all(
                    price, line.quantity, product=line.product_id,
                    partner=line.invoice_id.partner_id)
                total_tax = totals['total_included'] - totals['total']
                increment = total_tax * (100 - line.vat_prorrate_percent) / 100
                assets.write({
                    'purchase_value': line.price_subtotal + increment,
                    'vat_prorrate_percent': line.vat_prorrate_percent,
                    'vat_prorrate_increment': increment,
                })
                # Recompute depreciation board for applying new purchase value
                assets.compute_depreciation_board()
        return res
