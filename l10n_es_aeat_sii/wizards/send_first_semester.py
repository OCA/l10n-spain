# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import models, fields, api


SII_SEMESTER_DATE_INI = '2017-01-01'
SII_SEMESTER_DATE_END = '2017-06-30'


class L10nEsSiiFirstSemester(models.TransientModel):
    _name = 'l10n.es.sii.first.semester'

    date_to = fields.Date('Date to',  default=SII_SEMESTER_DATE_END)

    @api.multi
    def execute(self):
        # Quizás los filtro deberían ser por períodos y no por fecha?
        out_invoices = self.env['account.invoice'].search([
                ('date_invoice', '<=', self.date_to),
                ('date_invoice', '>=', SII_SEMESTER_DATE_INI),
                ('sii_state', 'not in', ['sent', 'cancel']),
                ('type', 'in', ['out_invoice', 'out_refund'])])
        in_invoices = self.env['account.invoice'].search([
                ('date_invoice', '<=', self.date_to),
                ('date_invoice', '>=', SII_SEMESTER_DATE_END),
                ('sii_state', 'not in', ['sent', 'cancel']),
                ('type', 'in', ['in_invoice', 'in_refund'])])
        sii_key_obj = self.env['aeat.sii.mapping.registration.keys']
        sale_key_id = sii_key_obj.sudo().search([('code', '=', '16'),
                                                ('type', '=', 'sale')],
                                                limit=1)[0].id
        purchase_key_id = sii_key_obj.sudo().search([('code', '=', '14'),
                                                    ('type', '=', 'purchase')],
                                                    limit=1)[0].id
        out_invoices.write({'sii_registration_key': sale_key_id})
        out_invoices.with_context(no_eta=True).send_sii()
        in_invoices.write({'sii_registration_key': purchase_key_id})
        in_invoices.with_context(no_eta=True).send_sii()
