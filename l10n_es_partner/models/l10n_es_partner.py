# -*- coding: utf-8 -*-
# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import _, api, fields, models
from openerp.models import expression


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    acc_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Bank country',
        help='If the country of the bank is Spain, it validates the bank '
             'code or IBAN, formatting it accordingly.')

    def _crc(self, cTexto):
        """Calculo el CRC de un número de 10 dígitos
        ajustados con ceros por la izquierda"""
        factor = (1, 2, 4, 8, 5, 10, 9, 7, 3, 6)
        # Cálculo CRC
        nCRC = 0
        for n in range(10):
            nCRC += int(cTexto[n]) * factor[n]
        # Reducción del CRC a un dígi9to
        nValor = 11 - nCRC % 11
        if nValor == 10:
            nValor = 1
        elif nValor == 11:
            nValor = 0
        return nValor

    def calcCC(self, cBanco, cSucursal, cCuenta):
        """Cálculo del código de control bancario"""
        cTexto = "00%04d%04d" % (int(cBanco), int(cSucursal))
        dc1 = self._crc(cTexto)
        cTexto = "%010d" % long(cCuenta)
        dc2 = self._crc(cTexto)
        return "%1d%1d" % (dc1, dc2)

    def checkBankAccount(self, account):
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
        if dc != self.calcCC(bank, office, account):
            return 'invalid-dc'
        return '%s %s %s %s' % (bank, office, dc, account)

    def _pretty_iban(self, iban_str):
        """return iban_str in groups of four characters separated
        by a single space"""
        res = []
        while iban_str:
            res.append(iban_str[:4])
            iban_str = iban_str[4:]
        return ' '.join(res)

    def onchange_banco(self, cr, uid, ids, account, country_id,
                       state, context=None):
        if account and country_id:
            country = self.pool.get('res.country').browse(cr, uid, country_id,
                                                          context=context)
            if country.code.upper() == 'ES':
                bank_obj = self.pool.get('res.bank')
                if state == 'bank':
                    account = account.replace(' ', '')
                    number = self.checkBankAccount(account)
                    if number == 'invalid-size':
                        return {
                            'warning': {
                                'title': _('Warning'),
                                'message': _('Bank account should have 20 '
                                             'digits.')
                            }
                        }
                    if number == 'invalid-dc':
                        return {
                            'warning': {
                                'title': _('Warning'),
                                'message': _('Invalid bank account.')
                            }
                        }
                    bank_ids = bank_obj.search(cr, uid,
                                               [('code', '=', number[:4])],
                                               context=context)
                    if bank_ids:
                        return {'value': {'acc_number': number,
                                          'bank': bank_ids[0]}}
                    else:
                        return {'value': {'acc_number': number}}
                elif state == 'iban':
                    partner_bank_obj = self.pool['res.partner.bank']
                    if partner_bank_obj.is_iban_valid(cr, uid, account,
                                                      context):
                        number = self._pretty_iban(account.replace(" ", ""))
                        bank_ids = bank_obj.search(
                            cr, uid, [('code', '=', number[5:9])],
                            context=context)
                        if bank_ids:
                            return {'value': {'acc_number': number,
                                              'bank': bank_ids[0]}}
                        else:
                            return {'value': {'acc_number': number}}
                    else:
                        return {'warning': {'title': _('Warning'),
                                'message': _('IBAN account is not valid')}}
        return {'value': {}}


class ResBank(models.Model):
    _inherit = 'res.bank'

    code = fields.Char('Code', size=64)
    lname = fields.Char('Long name', size=128)
    vat = fields.Char('VAT code', size=32, help='Value Added Tax number')
    website = fields.Char('Website', size=64)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    comercial = fields.Char('Trade name', size=128, select=True)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Include commercial name in direct name search."""
        args = expression.normalize_domain(args)
        for arg in args:
            if isinstance(arg, (list, tuple)):
                if arg[0] in ['name', 'display_name']:
                    index = args.index(arg)
                    args = (
                        args[:index] + ['|', ('comercial', arg[1], arg[2])] +
                        args[index:]
                    )
                    break
        return super(ResPartner, self).search(
            args, offset=offset, limit=limit, order=order, count=count,
        )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """Give preference to commercial names on name search, appending
        the rest of the results after. This has to be done this way, as
        Odoo overwrites name_search on res.partner in a non inheritable way."""
        if not args:
            args = []
        partners = self.search(
            [('comercial', operator, name)] + args, limit=limit,
        )
        res = partners.name_get()
        if limit:
            limit_rest = limit - len(partners)
        else:
            # limit can be 0 or None representing infinite
            limit_rest = limit
        if limit_rest or not limit:
            args += [('id', 'not in', partners.ids)]
            res += super(ResPartner, self).name_search(
                name, args=args, operator=operator, limit=limit_rest,
            )
        return res

    @api.multi
    def name_get(self):
        result = []
        name_pattern = self.env['ir.config_parameter'].get_param(
            'l10n_es_partner.name_pattern', default='')
        orig_name = dict(super(ResPartner, self).name_get())
        for partner in self:
            name = orig_name[partner.id]
            comercial = partner.comercial
            if comercial and name_pattern:
                name = name_pattern % {'name': name,
                                       'comercial_name': comercial}
            result.append((partner.id, name))
        return result

    def vat_change(self, cr, uid, ids, value, context=None):
        result = super(ResPartner, self).vat_change(cr, uid, ids, value,
                                                    context=context)
        if value:
            result['value']['vat'] = value.upper()
        return result
