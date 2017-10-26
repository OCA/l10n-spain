# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    bank_acc_country_id = fields.Many2one(
        comodel_name='res.country', related='company_id.country_id',
        string='Bank country', readonly=True,
        help='If the country of the bank is Spain, it validates the bank '
             'code or IBAN, formatting it accordingly.'
    )

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
            if self.bank_id:
                self.name = "{} {}".format(
                    self.bank_id.name, self.bank_acc_number,
                )
