# -*- coding: utf-8 -*-
# Copyright 2015-2017 Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models, tools


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    @api.multi
    def _prepare_all_journals(self, acc_template_ref, company_id,
                              journals_dict=None):
        self.ensure_one()
        journal_data = super(AccountChartTemplate, self)._prepare_all_journals(
            acc_template_ref, company_id, journals_dict=journals_dict,
        )
        if not self.is_spanish_chart():  # pragma: no cover
            return journal_data
        journal_model = self.env['account.journal']
        # Create unified sequence for journal entries
        generic_journal_seq = self.env.ref(
            'l10n_es_account_invoice_sequence.sequence_spanish_journal',
        )
        journal_seq = generic_journal_seq.copy({
            'name': _('Journal Entries Sequence'),
            'active': True,
            'company_id': company_id.id,
        })
        for journal_vals in journal_data:
            journal_vals['refund_sequence'] = False
            journal_vals['sequence_id'] = journal_seq.id
            if journal_vals['type'] in journal_model._get_invoice_types():
                seq = journal_model._create_sequence(journal_vals)
                journal_vals['invoice_sequence_id'] = seq.id
                refund_seq = journal_model._create_sequence(
                    journal_vals, refund=True,
                )
                refund_seq.name += _(' (Refund)')
                journal_vals['refund_inv_sequence_id'] = refund_seq.id
        return journal_data

    @api.model
    def _get_spanish_charts_xml_ids(self):
        return [
            'l10n_es.account_chart_template_common',
            'l10n_es.account_chart_template_assoc',
            'l10n_es.account_chart_template_pymes',
            'l10n_es.account_chart_template_full',
        ]

    @api.multi
    def _get_spanish_charts(self):
        charts = self.env['account.chart.template']
        for chart_id in self._get_spanish_charts_xml_ids():
            charts |= self.env.ref(chart_id)
        return charts

    @api.multi
    @tools.ormcache('self')
    def is_spanish_chart(self):
        return self in self._get_spanish_charts()
