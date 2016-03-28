# -*- coding: utf-8 -*-
# Copyright 2011 NaN Projectes de Programari Lliure, S.L.
# Copyright 2013-2017 Pedro M. Baeza

from openerp import _, api, fields, exceptions, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    invoice_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Invoice sequence',
        domain="[('company_id', '=', company_id)]", ondelete='restrict',
        help="The sequence used for invoice numbers in this journal.",
    )
    refund_inv_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Refund sequence',
        domain="[('company_id', '=', company_id)]", ondelete='restrict',
        help="The sequence used for refund invoices numbers in this journal.",
    )

    @api.multi
    @api.constrains('invoice_sequence_id')
    def _check_company(self):
        for journal in self:
            sequence_company = journal.invoice_sequence_id.company_id
            if sequence_company and sequence_company != journal.company_id:
                raise exceptions.Warning(
                    _("Journal company and invoice sequence company do not "
                      "match."))

    @api.multi
    @api.constrains('refund_inv_sequence_id')
    def _check_company_refund(self):
        for journal in self:
            sequence_company = journal.refund_inv_sequence_id.company_id
            if sequence_company and sequence_company != journal.company_id:
                raise exceptions.Warning(
                    _("Journal company and refund sequence company do not "
                      "match."))

    @api.model
    def create(self, vals):
        """Use the existing sequence for new Spanish journals."""
        if not vals.get('company_id') or vals.get('sequence_id'):
            return super(AccountJournal, self).create(vals)
        company = self.env['res.company'].browse(vals['company_id'])
        if company.chart_template_id.is_spanish_chart():
            journal = self.search([('company_id', '=', company.id)], limit=1)
            if journal:
                vals['sequence_id'] = journal.sequence_id.id
                vals['refund_sequence'] = False
        return super(AccountJournal, self).create(vals)

    def _get_invoice_types(self):
        return [
            'sale',
            'purchase',
        ]
