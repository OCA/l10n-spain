# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c)
#        2013-2014 Servicios Tecnológicos Avanzados (http://serviciosbaeza.com)
#                  Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _


class AccountStatementCompletionRule(orm.Model):
    _inherit = "account.statement.completion.rule"

    def _get_functions(self, cr, uid, context=None):
        res = super(AccountStatementCompletionRule, self)._get_functions(
            cr, uid, context=context)
        res.append(('get_from_caixabank_rules', _('From CaixaBank C43 rules')))
        res.append(('get_from_santander_rules', _('From Santander C43 rules')))
        res.append(('get_from_generic_c43_rules', _('From generic C43 rules')))
        return res

    _columns = {
        'function_to_call': fields.selection(_get_functions, 'Method'),
    }

    def get_from_caixabank_rules(self, cr, uid, st_line, context=None):
        """
        Match the partner based on several criteria extracted from reverse
        engineer of CaixaBank C43 files.

        If more than one partner is matched, raise the ErrorTooManyPartner
        error.
        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
        """
        partner_obj = self.pool['res.partner']
        st_line_obj = self.pool['account.bank.statement.line']
        conceptos = safe_eval(st_line['name'])
        ids = []
        res = {}
        # Try to match from VAT included in concept complementary record #02
        if conceptos.get('02'):
            vat = conceptos['02'][0][:2] + conceptos['02'][0][7:]
            ids = partner_obj.search(cr, uid, [('vat', '=', vat)],
                                     context=context)
        if len(ids) > 1:
            from openerp.addons.account_statement_base_completion.statement \
                import ErrorTooManyPartner
            raise ErrorTooManyPartner(
                _('Line named "%s" (Ref: %s) was matched by more than '
                  'one partner for VAT number "%s".') %
                (st_line['name'], st_line['ref'], vat))
        if not ids:
            # Try to match from partner name
            if conceptos.get('01'):
                name = conceptos['01'][0][4:] + conceptos['01'][1]
                ids = partner_obj.search(cr, uid, [('name', 'ilike', name)],
                                         context=context)
        if ids:
            res['partner_id'] = ids[0]
        st_vals = st_line_obj.get_values_for_line(
            cr, uid, profile_id=st_line['profile_id'],
            master_account_id=st_line['master_account_id'],
            partner_id=res.get('partner_id', False), line_type=st_line['type'],
            amount=st_line['amount'] or 0.0, context=context)
        res.update(st_vals)
        return res

    def get_from_santander_rules(self, cr, uid, st_line, context=None):
        """
        Match the partner based on several criteria extracted from reverse
        engineer of Banco Santander C43 files.

        If more than one partner is matched, raise the ErrorTooManyPartner
        error.
        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
        """
        partner_obj = self.pool['res.partner']
        st_line_obj = self.pool['account.bank.statement.line']
        conceptos = safe_eval(st_line['name'])
        ids = []
        res = {}
        # Try to match from VAT included in concept complementary record #01
        if conceptos.get('01'):
            if conceptos['01'][1]:
                vat = conceptos['01'][1]
                ids = partner_obj.search(cr, uid, [('vat', 'ilike', vat)],
                                         context=context)
        if len(ids) > 1:
            from openerp.addons.account_statement_base_completion.statement \
                import ErrorTooManyPartner
            raise ErrorTooManyPartner(
                _('Line named "%s" (Ref: %s) was matched by more than '
                  'one partner for VAT number "%s".') %
                (st_line['name'], st_line['ref'], vat))
        if not ids:
            # Try to match from partner name
            if conceptos.get('01'):
                name = conceptos['01'][0]
                ids = partner_obj.search(cr, uid, [('name', 'ilike', name)],
                                         context=context)
        if ids:
            res['partner_id'] = ids[0]
        st_vals = st_line_obj.get_values_for_line(
            cr, uid, profile_id=st_line['profile_id'],
            master_account_id=st_line['master_account_id'],
            partner_id=res.get('partner_id', False), line_type=st_line['type'],
            amount=st_line['amount'] or 0.0, context=context)
        res.update(st_vals)
        return res

    def get_from_generic_c43_rules(self, cr, uid, st_line, context=None):
        """
        Match the partner based on invoice amount..

        If more than one partner is matched, raise the ErrorTooManyPartner
        error.
        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
        """
        st_line_obj = self.pool['account.bank.statement.line']
        invoice_obj = self.pool['account.invoice']
        ids = []
        res = {}
        # Finally, try to match from invoice amount
        if st_line['amount'] > 0.0:
            domain = [('type', 'in', ['out_invoice', 'in_refund'])]
        else:
            domain = [('type', 'in', ['in_invoice', 'out_refund'])]
        domain.append(('amount_total', '=', abs(st_line['amount'])))
        domain.append(('state', '=', 'open'))
        invoice_ids = invoice_obj.search(cr, uid, domain,
                                         context=context)
        if invoice_ids:
            invoices = invoice_obj.read(cr, uid, invoice_ids,
                                        ['partner_id'], context=context)
            ids = [x['partner_id'][0] for x in invoices]
            ids = list(set(ids))
        if len(ids) > 1:
            from openerp.addons.account_statement_base_completion.statement \
                import ErrorTooManyPartner
            raise ErrorTooManyPartner(
                _('Line named "%s" (Ref: %s) was matched by more than '
                  'one partner for invoice amount "%s".') %
                (st_line['name'], st_line['ref'], st_line['amount']))
        if ids:
            res['partner_id'] = ids[0]
        st_vals = st_line_obj.get_values_for_line(
            cr, uid, profile_id=st_line['profile_id'],
            master_account_id=st_line['master_account_id'],
            partner_id=res.get('partner_id', False), line_type=st_line['type'],
            amount=st_line['amount'] or 0.0, context=context)
        res.update(st_vals)
        return res
