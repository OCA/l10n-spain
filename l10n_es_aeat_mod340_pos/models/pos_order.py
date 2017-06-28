# -*- coding: utf-8 -*-
# Copyright 2017 - Aselcis Consulting (http://www.aselcis.com)
#                - Miguel Paraíso <miguel.paraiso@aselcis.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _create_account_move_line(self, session=None, move=None):
        res = super(PosOrder, self)._create_account_move_line(session, move)
        used_product_move_lines = []
        used_tax_move_lines = []
        used_receivables_move_lines = []
        for order in self:
            current_company = order.sale_journal.company_id
            account_def = self.env['ir.property'].get(
                'property_account_receivable_id', 'res.partner')
            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
            partner_id = self.env['res.partner']._find_accounting_partner(
                order.partner_id).id or False

            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'pos.closing.journal_id_%s' % current_company.id,
                default=order.sale_journal.id)
            date_tz_user = fields.Datetime.context_timestamp(self,
                                                             fields.Datetime.from_string(
                                                                 order.session_id.start_at))
            date_tz_user = fields.Date.to_string(date_tz_user)
            move = self.env['account.move'].search(
                [('ref', '=', session.name), ('date', '=', date_tz_user),
                 ('journal_id', '=', int(journal_id))])
            cur = order.pricelist_id.currency_id
            for order_line in order.lines:
                amount = order_line.price_subtotal

                # Search for the income account
                if order_line.product_id.property_account_income_id.id:
                    income_account = order_line.product_id.property_account_income_id.id
                elif order_line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = order_line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '
                                      'account for this product: "%s" (id:%d).')
                                    % (order_line.product_id.name,
                                       order_line.product_id.id))

                name = order_line.product_id.name
                if order_line.notice:
                    # add discount reason in move
                    name = name + ' (' + order_line.notice + ')'

                product_move_lines = self.env['account.move.line'].search([
                    ('id', 'not in', used_product_move_lines),
                    ('move_id', '=', move.id),
                    ('name', '=', name),
                    ('quantity', '=', order_line.qty),
                    ('product_id', '=', order_line.product_id.id),
                    ('account_id', '=', income_account),
                    ('analytic_account_id', '=',
                     self._prepare_analytic_account(order_line)),
                    ('credit', '=', ((amount > 0) and amount) or 0.0),
                    ('debit', '=', ((amount < 0) and -amount) or 0.0),
                    ('partner_id', '=', partner_id)
                ])
                if product_move_lines:
                    # Add origin POS Order
                    product_move_lines[0].write({'pos_order_id': order.id})
                    used_product_move_lines.append(product_move_lines[0].id)

                taxes = order_line.tax_ids_after_fiscal_position.filtered(
                    lambda t: t.company_id.id == current_company.id)
                if not taxes:
                    continue
                for tax in taxes.compute_all(order_line.price_unit * (
                            100.0 - order_line.discount) / 100.0, cur,
                                             order_line.qty)[
                    'taxes']:
                    tax_move_lines = self.env['account.move.line'].search([
                        ('id', 'not in', used_tax_move_lines),
                        ('move_id', '=', move.id),
                        ('name', '=', _('Tax') + ' ' + tax['name']),
                        ('quantity', '=', order_line.qty),
                        ('product_id', '=', order_line.product_id.id),
                        ('account_id', '=',
                         tax['account_id'] or income_account),
                        ('credit', '=',
                         ((tax['amount'] > 0) and tax['amount']) or 0.0),
                        ('debit', '=',
                         ((tax['amount'] < 0) and -tax['amount']) or 0.0),
                        ('tax_line_id', '=', tax['id']),
                        ('partner_id', '=', partner_id)
                    ])
                    if tax_move_lines:
                        # Add origin POS Order
                        tax_move_lines[0].write({'pos_order_id': order.id})
                        used_tax_move_lines.append(tax_move_lines[0].id)
            receivables_move_lines = self.env['account.move.line'].search([
                ('id', 'not in', used_receivables_move_lines),
                ('name', '=', _("Trade Receivables")),  # order.name,
                ('move_id', '=', move.id),
                ('account_id', '=', order_account),
                ('credit', '=',
                 ((order.amount_total < 0) and -order.amount_total) or 0.0),
                ('debit', '=',
                 ((order.amount_total > 0) and order.amount_total) or 0.0),
                ('partner_id', '=', partner_id)
            ])
            if receivables_move_lines:
                # Add origin POS Order
                receivables_move_lines[0].write({'pos_order_id': order.id})
                used_receivables_move_lines.append(
                    receivables_move_lines[0].id)
        return res
