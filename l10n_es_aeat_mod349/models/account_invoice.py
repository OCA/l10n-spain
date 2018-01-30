# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2017 Eficent Business & IT Consult. Services <contact@eficent.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    eu_triangular_deal = fields.Boolean(
        string='EU Triangular deal',
        help='This invoice constitutes a triangular operation for the '
             'purposes of intra-community operations.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.model
    def line_get_convert(self, line, part):
        """Copy from invoice to move lines"""
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['l10n_es_aeat_349_operation_key'] = line.get(
            'l10n_es_aeat_349_operation_key', False,
        )
        return res

    @api.model
    def invoice_line_move_line_get(self):
        """We pass on the operation key from invoice line to the move line"""
        ml_dicts = super(AccountInvoice, self).invoice_line_move_line_get()
        for ml_dict in ml_dicts:
            invl = self.env['account.invoice.line'].browse(ml_dict['invl_id'])
            ml_dict['l10n_es_aeat_349_operation_key'] = (
                invl.l10n_es_aeat_349_operation_key
            )
        return ml_dicts


class AccountInvoiceLine(models.Model):
    """Inheritance of account invoice line to add some fields:
    - AEAT_349_operation_key
    """
    _inherit = 'account.invoice.line'

    def _selection_operation_key(self):
        return self.env['account.move.line'].fields_get(
            allfields=['l10n_es_aeat_349_operation_key'],
        )['l10n_es_aeat_349_operation_key']['selection']

    l10n_es_aeat_349_operation_key = fields.Selection(
        selection=_selection_operation_key,
        string='AEAT 349 Operation key',
        compute='_compute_l10n_es_aeat_349_operation_key',
    )

    @api.depends('invoice_line_tax_ids', 'invoice_id.eu_triangular_deal')
    def _compute_l10n_es_aeat_349_operation_key(self):
        for rec in self:
            if rec.invoice_id.eu_triangular_deal:
                rec.l10n_es_aeat_349_operation_key = 'T'
            else:
                rec.l10n_es_aeat_349_operation_key = (
                    rec.invoice_line_tax_ids.filtered(
                        lambda x: x.l10n_es_aeat_349_operation_key
                    )[:1].l10n_es_aeat_349_operation_key
                )
