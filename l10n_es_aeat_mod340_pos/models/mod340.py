# -*- coding: utf-8 -*-
# Copyright 2017 - Aselcis Consulting (http://www.aselcis.com)
#                - Miguel Paraíso <miguel.paraiso@aselcis.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _
from odoo.exceptions import Warning
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import re


class L10nEsAeatMod340Report(models.Model):
    _inherit = "l10n.es.aeat.mod340.report"

    @api.multi
    def calculate(self):
        super(L10nEsAeatMod340Report, self).calculate()

        account_move = self.env['account.move']
        invoices340 = self.env['l10n.es.aeat.mod340.issued']
        invoices340_rec = self.env['l10n.es.aeat.mod340.received']
        issued_obj = self.env['l10n.es.aeat.mod340.tax_line_issued']
        received_obj = self.env['l10n.es.aeat.mod340.tax_line_received']
        default_pos_partner_id = self.env.ref(
            'l10n_es_partner.default_res_partner_simplified')

        for report in self:
            if not report.company_id.partner_id.vat:
                raise Warning(_("Company [%s] don't have NIF") % (
                    report.company_id.partner_id.name))

            move_domain = [
                ('state', '=', 'posted'),
                ('date', '>=', report.date_start),
                ('date', '<=', report.date_end),
            ]
            move_pos_order_ids = []
            # Search other account moves
            for move in account_move.search(move_domain):
                include_move = False
                if move.comes_from_pos_order:
                    for move_line in move.line_ids:
                        for tax_id in move_line.tax_ids:
                            if tax_id.mod340:
                                include_move = True
                                if move_line.pos_order_id and \
                                        move_line.pos_order_id.id not in move_pos_order_ids:
                                    move_pos_order_ids.append(
                                        move_line.pos_order_id.id)
                                break
                if include_move and move_pos_order_ids:
                    if move.partner_id.vat_type == '1':
                        if not move.partner_id.vat:
                            raise Warning(_(
                                "Partner [%s] don't have NIF") % move.partner_id.name)
                    if move.partner_id.vat:
                        country_code, nif = (re.match(r"([A-Z]{0,2})(.*)",
                                                      move.partner_id.vat).groups())
                    else:
                        country_code = False
                    while move_pos_order_ids:
                        values = {
                            'mod340_id': report.id,
                            'partner_id': move.partner_id.id,
                            'partner_vat': nif if default_pos_partner_id != move.partner_id else False,
                            'representative_vat': '',
                            'partner_country_code': country_code,
                            'account_move_id': move.id,
                            'date_invoice': move.date,
                        }
                        sign = 1
                        """if move.type in ['out_refund', 'in_refund']:
                            sign = -1
                            values['base_tax'] *= -1
                            values['amount_tax'] *= -1
                            values['total'] *= -1"""
                        if move.move_type == 'receivable':
                            invoice_created = invoices340.create(values)
                        elif move.move_type == 'payable':
                            invoice_created = invoices340_rec.create(values)

                        base_taxes = {}
                        used_base_taxes = []
                        amount_base = 0
                        total_base = 0
                        total_taxes = 0
                        total_amount = 0
                        simplified_invoice_ref = False
                        # Get base amount
                        for move_line in move.line_ids.filtered(
                                lambda m: m.pos_order_id.id ==
                                        move_pos_order_ids[0]):
                            for tax_id in move_line.tax_ids:
                                if tax_id.mod340:
                                    if move.move_type == 'receivable':
                                        amount_base = move_line.credit
                                        total_amount += move_line.credit
                                    elif move.move_type == 'payable':
                                        amount_base = move_line.debit
                                        total_amount += move_line.debit
                                    if tax_id.id in base_taxes:
                                        base_taxes[tax_id.id] += amount_base
                                    else:
                                        base_taxes[tax_id.id] = amount_base
                        # Get taxes amount
                        for move_line in move.line_ids.filtered(
                                lambda m: m.pos_order_id.id ==
                                        move_pos_order_ids[0]):
                            if move_line.tax_line_id:
                                tax_id = move_line.tax_line_id
                                if move.move_type == 'receivable':
                                    total_amount += move_line.credit
                                elif move.move_type == 'payable':
                                    total_amount += move_line.debit
                                if tax_id.mod340:
                                    if move.move_type == 'receivable':
                                        tax_amount = move_line.credit
                                    elif move.move_type == 'payable':
                                        tax_amount = move_line.debit
                                    tax_percentage = tax_amount / base_taxes[
                                        tax_id.id]
                                    if not simplified_invoice_ref:
                                        simplified_invoice_ref = move_line.pos_order_id.simplified_invoice
                                    values = {
                                        'name': move_line.name,
                                        'tax_percentage': tax_percentage,
                                        'tax_amount': tax_amount * sign,
                                        'base_amount': base_taxes[
                                                           tax_id.id] * sign,
                                        'invoice_record_id': invoice_created.id,
                                    }
                                    if move.move_type == 'receivable':
                                        issued_obj.create(values)
                                    elif move.move_type == 'payable':
                                        received_obj.create(values)
                                    total_taxes += tax_amount * sign
                                    if tax_id.id not in used_base_taxes and tax_percentage >= 0:
                                        total_base += base_taxes[tax_id.id]
                                        used_base_taxes.append(tax_id.id)
                        if move.move_type in ['receivable', 'payable']:
                            invoice_created.write({
                                'simplified_invoice_ref': simplified_invoice_ref,
                                'base_tax': total_base,
                                'amount_tax': total_taxes,
                                'total': total_amount,
                            })
                        move_pos_order_ids.pop(0)

            report.write({
                'state': 'calculated',
                'calculation_date':
                    time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })


class L10nEsAeatMod340Issued(models.Model):
    _inherit = 'l10n.es.aeat.mod340.issued'

    simplified_invoice_ref = fields.Char(string='Simplified Invoice', size=32,
                                         help="Simplified Invoice reference")
    account_move_id = fields.Many2one('account.move', string='Account move')
    invoice_name = fields.Char(string='Invoice', size=32,
                               compute='_compute_invoice_name')

    @api.multi
    def _compute_invoice_name(self):
        for record in self:
            if not record.simplified_invoice_ref:
                record.invoice_name = record.invoice_id.number
            else:
                record.invoice_name = record.simplified_invoice_ref
