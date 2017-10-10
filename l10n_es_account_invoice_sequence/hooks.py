# -*- coding: utf-8 -*-
# Copyright 2015-2016 Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, SUPERUSER_ID


def post_init_hook(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        for company in env['res.company'].search([]):
            if not company.chart_template_id.is_spanish_chart():
                continue  # pragma: no cover
            journals = env['account.journal'].search([
                ('company_id', '=', company.id),
            ])
            generic_journal_seq = env.ref(
                'l10n_es_account_invoice_sequence.sequence_spanish_journal'
            )
            journal_seq = generic_journal_seq.copy({
                'name': _('Journal Entries Sequence'),
                'active': True,
                'company_id': company.id,
            })
            journal_invoice_types = journals._get_invoice_types()
            for journal in journals:
                vals = {
                    'sequence_id': journal_seq.id,
                    'refund_sequence': False,
                }
                if journal.type in journal_invoice_types:
                    vals['invoice_sequence_id'] = journal.sequence_id.id
                    vals['refund_inv_sequence_id'] = (
                        journal.refund_sequence_id.id
                    )
                journal.write(vals)
