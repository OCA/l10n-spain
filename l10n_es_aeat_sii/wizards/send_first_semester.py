# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import models, fields, api


SII_SEMESTER_DATE_INI = '2017-01-01'
SII_SEMESTER_DATE_END = '2017-06-30'


class L10nEsSiiFirstSemester(models.TransientModel):
    _name = 'l10n.es.sii.first.semester'

    date_to = fields.Date('Date to', default=SII_SEMESTER_DATE_END,
                          required=True)
    out_invoices = fields.Boolean('Send out invoices', default=True)
    in_invoices = fields.Boolean('Send in invoices', default=True)

    @api.multi
    def execute(self):
        self.ensure_one()
        if self.out_invoices:
            out_invoices = self.env['account.invoice'].\
                search([('date_invoice', '<=', self.date_to),
                        ('date_invoice', '>=', SII_SEMESTER_DATE_INI),
                        ('state', 'in', ['open', 'paid']),
                        ('sii_state', 'not in', ['sent', 'cancelled']),
                        ('type', 'in', ['out_invoice', 'out_refund'])])
            sale_key_id = self.env.\
                ref('l10n_es_aeat_sii.aeat_sii_mapping_registration_keys_29').\
                id
            out_invoices.write({'sii_registration_key': sale_key_id,
                                'sii_manual_description': (
                                    "Registro del Primer semestre")})
            out_invoices.with_context(override_eta=0).send_sii()
        if self.in_invoices:
            in_invoices = self.env['account.invoice'].\
                search([('date', '<=', self.date_to),
                        ('date', '>=', SII_SEMESTER_DATE_INI),
                        ('state', 'in', ['open', 'paid']),
                        ('sii_state', 'not in', ['sent', 'cancelled']),
                        ('type', 'in', ['in_invoice', 'in_refund'])])
            purchase_key_id = self.env.\
                ref('l10n_es_aeat_sii.aeat_sii_mapping_registration_keys_30').\
                id
            in_invoices.write({'sii_registration_key': purchase_key_id,
                               'sii_manual_description': (
                                   "Registro del Primer semestre"),
                               'sii_account_registration_date': (
                                   fields.Date.today())})
            in_invoices.with_context(override_eta=0).send_sii()
