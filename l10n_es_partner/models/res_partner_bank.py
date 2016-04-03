# -*- coding: utf-8 -*-
# © 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# © 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import api, exceptions, fields, models, _
from openerp.addons.base_iban.base_iban import normalize_iban, validate_iban


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    acc_country_id = fields.Many2one(
        comodel_name='res.country', related='partner_id.country_id',
        string='Bank country', readonly=True,
        help='If the country of the bank is Spain, it validates the bank '
             'code or IBAN, formatting it accordingly.')

    @api.model
    def _crc(self, texto):
        """Calculo el CRC de un número de 10 dígitos
        ajustados con ceros por la izquierda"""
        factor = (1, 2, 4, 8, 5, 10, 9, 7, 3, 6)
        # Cálculo CRC
        nCRC = 0
        for n in range(10):
            nCRC += int(texto[n]) * factor[n]
        # Reducción del CRC a un dígi9to
        nValor = 11 - nCRC % 11
        if nValor == 10:
            nValor = 1
        elif nValor == 11:
            nValor = 0
        return nValor

    @api.model
    def _calc_cc(self, banco, sucursal, cuenta):
        """Cálculo del código de control bancario"""
        texto = "00%04d%04d" % (int(banco), int(sucursal))
        dc1 = self._crc(texto)
        texto = "%010d" % long(cuenta)
        dc2 = self._crc(texto)
        return "%1d%1d" % (dc1, dc2)

    @api.model
    def check_bank_account(self, account):
        number = ""
        for i in account:
            if i.isdigit():
                number += i
        if len(number) != 20:
            return 'invalid-size'
        bank = number[0:4]
        office = number[4:8]
        dc = number[8:10]
        account = number[10:20]
        if dc != self._calc_cc(bank, office, account):
            return 'invalid-dc'
        return '%s %s %s %s' % (bank, office, dc, account)

    @api.model
    def _pretty_iban(self, iban_str):
        """return iban_str in groups of four characters separated
        by a single space"""
        res = []
        while iban_str:
            res.append(iban_str[:4])
            iban_str = iban_str[4:]
        return ' '.join(res)

    @api.model
    def _process_onchange_acc_number(self, acc_number, country):
        res = {}
        if not acc_number or country != self.env.ref('base.es'):
            return res  # pragma: no cover
        bank_obj = self.env['res.bank']
        acc_number = normalize_iban(acc_number)
        if len(acc_number) > 20:
            # It's an IBAN account
            try:
                validate_iban(acc_number)
                bank = bank_obj.search(
                    [('code', '=', acc_number[4:8])], limit=1)
                number = self._pretty_iban(acc_number)
            except exceptions.ValidationError:
                res['warning_message'] = _('IBAN account is not valid')
                return res
        else:
            number = self.check_bank_account(acc_number)
            if number == 'invalid-size':
                res['warning_message'] = _(
                    'Bank account should have 20 digits.')
                return res
            elif number == 'invalid-dc':
                res['warning_message'] = _('Invalid bank account.')
                return res
            bank = bank_obj.search([('code', '=', number[:4])], limit=1)
        res['acc_number'] = number
        res['bank_id'] = bank.id
        return res

    @api.multi
    @api.onchange('acc_country_id', 'acc_number')
    def onchange_acc_number_l10n_es_partner(self):
        warning_dict = {'warning': {'title': _('Warning')}}
        res = self._process_onchange_acc_number(
            self.acc_number, self.acc_country_id)
        if res.get('warning_message'):
            warning_dict['warning']['message'] = res['warning_message']
            return warning_dict
        self.acc_number = res.get('acc_number', False)
        self.bank_id = res.get('bank_id', False)
