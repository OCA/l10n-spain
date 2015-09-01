# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from .constants import ALLOWED_JOURNAL_TYPES
from . import models
from . import wizard


def fill_invoice_sequences(cr, registry):
    from openerp import SUPERUSER_ID, _
    company_obj = registry['res.company']
    journal_obj = registry['account.journal']
    model_data_obj = registry['ir.model.data']
    sequence_obj = registry['ir.sequence']
    company_ids = company_obj.search(cr, SUPERUSER_ID, [])
    for company in company_obj.browse(cr, SUPERUSER_ID, company_ids):
        if company.country_id and company.country_id.code != 'ES':
            # Discard non spanish companies (by the country of the address)
            # Companies with no country are not discarded
            continue
        journal_ids = journal_obj.search(
            cr, SUPERUSER_ID, [('company_id', '=', company.id)])
        generic_journal_seq_id = model_data_obj.get_object_reference(
            cr, SUPERUSER_ID, 'l10n_es_account_invoice_sequence',
            'sequence_spanish_journal')[1]
        journal_seq_id = sequence_obj.copy(
            cr, SUPERUSER_ID, generic_journal_seq_id,
            {'name': _('Journal Entries Sequence'),
             'company_id': company.id})
        for journal in journal_obj.browse(cr, SUPERUSER_ID, journal_ids):
            vals = {'sequence_id': journal_seq_id}
            if journal.type in ALLOWED_JOURNAL_TYPES:
                vals['invoice_sequence_id'] = journal.sequence_id.id
            journal_obj.write(
                cr, SUPERUSER_ID, journal.id, vals)
