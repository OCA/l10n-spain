# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    bank_acc_country_id = fields.Many2one(
        comodel_name='res.country', related='company_id.country_id',
        string='Bank country', readonly=True,
        help='If the country of the bank is Spain, it validates the bank '
             'code or IBAN, formatting it accordingly.')

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.env.user.company_id.id)
        company = self.env['res.company'].browse(company_id)
        if (company.country_id == self.env.ref('base.es') and
                vals.get('type') in ('bank', 'cash') and 'bank_id' in vals and
                not vals.get('name') and 'bank_acc_number' in vals):
            # Write a more complete version of the journal name for Spanish
            # bank and cash journals
            bank = self.env['res.bank'].browse(vals['bank_id'])
            vals['name'] = u"{} {}".format(bank.name, vals['bank_acc_number'])
        return super(AccountJournal, self).create(vals)

    @api.multi
    @api.onchange('bank_acc_country_id', 'bank_acc_number')
    def _onchange_bank_acc_number_l10n_es_partner(self):
        res = self.env['res.partner.bank']._process_onchange_acc_number(
            self.bank_acc_number, self.bank_acc_country_id,
        )
        if res.get('warning_message'):
            warning_dict = {
                'warning': {
                    'title': _('Warning'),
                    'message': res['warning_message'],
                }
            }
            return warning_dict
        if res:
            self.bank_acc_number = res.get('acc_number', False)
            self.bank_id = res.get('bank_id', False)
