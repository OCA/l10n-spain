# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import _, api, exceptions, models
from odoo.addons.base_iban.models.res_partner_bank import \
    normalize_iban, validate_iban, pretty_iban


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def _crc(self, texto):
        """Cálculo del CRC de un número de 10 dígitos ajustados con ceros por
        la izquierda.
        """
        factor = (1, 2, 4, 8, 5, 10, 9, 7, 3, 6)
        # Cálculo CRC
        nCRC = 0
        for n in range(10):
            nCRC += int(texto[n]) * factor[n]
        # Reducción del CRC a un dígito
        nValor = 11 - nCRC % 11
        if nValor == 10:  # pragma: no cover
            nValor = 1
        elif nValor == 11:  # pragma: no cover
            nValor = 0
        return nValor

    @api.model
    def _calc_cc(self, banco, sucursal, cuenta):
        """Cálculo del código de control bancario"""
        texto = "00%04d%04d" % (int(banco), int(sucursal))
        dc1 = self._crc(texto)
        texto = "%010d" % int(cuenta)
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
                number = pretty_iban(acc_number)
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
        res['acc_number'] = number.upper()
        res['bank_id'] = bank.id
        return res

    @api.multi
    @api.onchange('acc_number', 'bank_id')
    def _onchange_acc_number_l10n_es_partner(self):
        context = self.env.context
        if not context.get('default_partner_id'):  # pragma: no cover
            return
        partner = self.env['res.partner'].browse(context['default_partner_id'])
        res = self._process_onchange_acc_number(
            self.acc_number, partner.country_id,
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
            self.acc_number = res.get('acc_number', False)
            self.bank_id = res.get('bank_id', False)
