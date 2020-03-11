# -*- coding: utf-8 -*-
# Copyright 2011 NaN Projectes de Programari Lliure, S.L.
# Copyright 2013-2017 Pedro M. Baeza
# Copyright 2019 Jose F. Fernandez

from odoo import _, api, fields, exceptions, models


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
            journal = self._get_company_journal(company)
            if journal:
                vals['sequence_id'] = journal.sequence_id.id
                vals['refund_sequence'] = False
        return super(AccountJournal, self).create(vals)

    def write(self, vals):
        """Don't change automatically prefix for journal entry sequences."""
        spanish_journals = self.env['account.journal']
        if 'code' in vals:
            spanish_journals = self.filtered(
                lambda x: x.company_id.chart_template_id.is_spanish_chart()
            ).with_context(no_prefix_change=True)
        if spanish_journals:
            super(AccountJournal, spanish_journals).write(vals)
        rest = self - spanish_journals
        if rest:
            super(AccountJournal, rest).write(vals)
        return True

    def _get_invoice_types(self):
        return [
            'sale',
            'purchase',
        ]

    def _get_company_journal(self, company):
        """Get an existing journal in the company to take it's counter."""
        if not company:
            return False
        return self.search([('company_id', '=', company.id)], limit=1)

    @api.model
    def default_get(self, default_fields):
        res = super(AccountJournal, self).default_get(default_fields)
        company = self.env['res.company'].browse(res.get('company_id', False))
        if company.chart_template_id.is_spanish_chart():
            journal = self._get_company_journal(company)
            if journal:
                res['sequence_id'] = journal.sequence_id.id
        return res
