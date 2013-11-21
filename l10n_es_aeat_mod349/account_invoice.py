# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
#
#    Migración OpenERP 7.0. Top Consultant Software Creations S.L. (http://www.topconsultant.es/) 2013
#        Ignacio Martínez y Miguel López.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

__author__ = \
"Luis Manuel Angueira Blanco (Pexego),Omar Castiñeira Saavedra(omar@pexego.es)"

from openerp.tools.translate import _
from openerp.osv import fields, orm

OPERATION_KEY = [
    ('Nothing', ''),
    ('E', 'E - Intra-Community supplies'),
    ('A', 'A - Intra-Community acquisition'),
    ('T', 'T - Triangular operations'),
    ('S', 'S - Intra-Community services'),
    ('I', 'I - Intra-Community services acquisitions'),
    ('M', 'M - Intra-Community supplies without taxes'),
    ('H', 'H - Intra-Community supplies without taxes '
     'delivered by legal representative')
]

MONTH_DATES_MAPPING = {
    '01': {'date_start': '%s-01-01', 'date_stop': '%s-01-31'},
    '02': {'date_start': '%s-02-01', 'date_stop': '%s-02-28'},
    '03': {'date_start': '%s-03-01', 'date_stop': '%s-03-31'},
    '04': {'date_start': '%s-04-01', 'date_stop': '%s-04-30'},
    '05': {'date_start': '%s-05-01', 'date_stop': '%s-05-31'},
    '06': {'date_start': '%s-06-01', 'date_stop': '%s-06-30'},
    '07': {'date_start': '%s-07-01', 'date_stop': '%s-07-31'},
    '08': {'date_start': '%s-08-01', 'date_stop': '%s-08-31'},
    '09': {'date_start': '%s-09-01', 'date_stop': '%s-09-30'},
    '10': {'date_start': '%s-10-01', 'date_stop': '%s-10-31'},
    '11': {'date_start': '%s-11-01', 'date_stop': '%s-11-30'},
    '12': {'date_start': '%s-12-01', 'date_stop': '%s-12-31'},
}


class account_invoice(orm.Model):
    """
    Inheritance of account invoce to add some fields
    - operation_key: Operation key of invoice
    """
    _inherit = 'account.invoice'

    #################
    ### FUNCTIONS ###
    #################
    def _get_invoices_by_type(self, cr, uid, partner_id, operation_key,
        fiscalyear_id=None, period_id=None, month=None, period_selection=None, context=None):
        """
        Returns invoices ids by type (supplier/customer)
        for a fiscalyear/period/month
        """
        assert period_selection, 'There is no period selected'

        ## Set type of invoice
        type = ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']

        fiscal_y_obj = self.pool.get('account.fiscalyear')
        fiscalyear_brw = fiscal_y_obj.browse(cr, uid, fiscalyear_id, context)
        search_dict = [
            ('partner_id', '=', partner_id),
            ('state', 'in', ['open', 'paid']),
            ('type', 'in', type),
            ('operation_key', '=', operation_key)]

        ##
        ## Invoices by fiscalyear (Annual)
        if period_selection == '0A':
            if not fiscalyear_id:
                raise orm.except_orm(_('Error'),
                                     _('Cannot get invoices.\nThere is no\
                                     fiscalyear selected'))

            search_dict.append(('period_id', 'in', [period.id for period in
                                                    fiscalyear_brw.period_ids
                                                    if not period.special]))

        ##
        ## Invoices by period
        elif period_selection in ['1T', '2T', '3T', '4T']:
            if not period_id:
                raise orm.except_orm(_('Error'),
                                     _('Cannot get invoices.\nThere is no \
                                     period selected'))

            search_dict.append(('period_id', 'in', period_id))

        ##
        ## Invoices by month
        else:
            year = fiscalyear_brw.code[:4]
            if not month and not fiscalyear_id:
                raise orm.except_orm(_('Error'),
                                     _('Cannot get invoices.\nThere is \
                                     no month and/or fiscalyear selected'))

            search_dict.append(('date_invoice',
                                '>=',
                                MONTH_DATES_MAPPING[month]['date_start'] %
                                                                        year))

            if month == '02':
                #checks if year is leap to can search
                #by last February date in database
                if int(year) % 4 == 0 and \
                (int(year) % 100 != 0 or int(year) % 400 == 0):
                    search_dict.append(('date_invoice',
                                        '<=', "%s-02-29" % year))
                else:
                    search_dict.append(('date_invoice',
                                        '<=',
                                        MONTH_DATES_MAPPING[month]['date' +
                                                                   '_stop']
                                                                   % year))
            else:
                search_dict.append(('date_invoice',
                                    '<=',
                                    MONTH_DATES_MAPPING[month]['date_stop']
                                    % year))

        return self.search(cr, uid, search_dict, context)

    def clean_refund_invoices(self, cr, uid, ids, partner_id,
                              fiscalyear_id=None, period_id=None,
                              month=None, period_selection=None, context=None):
        """separates restitution invoices"""
        invoice_lines = []
        restitution_lines = []
        fiscal_y_obj = self.pool.get('account.fiscalyear')
        fiscalyear_brw = fiscal_y_obj.browse(cr, uid, fiscalyear_id, context)

        for refund in self.browse(cr, uid, ids, context):
            if refund.type in ['in_refund', 'out_refund']:
                if not refund.origin_invoices_ids:
                    invoice_lines.append(refund.id)
                    continue
                for origin_line in refund.origin_invoices_ids:
                    if origin_line.state in ['open', 'paid'] and \
                                    origin_line.partner_id.id == partner_id:
                        if period_selection == '0A':
                            if origin_line.period_id.id not in \
                                        [period.id for period in
                                        fiscalyear_brw.period_ids if not \
                                        period.special]:
                                restitution_lines.append(refund.id)
                                break
                            else:
                                invoice_lines.append(refund.id)
                                break
                        elif period_selection in ['1T', '2T', '3T', '4T']:
                            if origin_line.period_id.id != period_id:
                                restitution_lines.append(refund.id)
                                break
                            else:
                                invoice_lines.append(refund.id)
                                break
                        else:
                            if origin_line.date_invoice < \
                                    MONTH_DATES_MAPPING[month]['date_start'] \
                                    % fiscalyear_brw.code[:4]:
                                restitution_lines.append(refund.id)
                                break
                            else:
                                invoice_lines.append(refund.id)
                                break
            else:
                invoice_lines.append(refund.id)

        return invoice_lines, restitution_lines

    def on_change_fiscal_position(self, cr, uid, ids,
                                  fiscal_position, type, context=None):
        """
        Suggest an operation key when fiscal position changes
        """
        if context is None:
            context = {}

        res = {'value': {'operation_key': 'Nothing'}}
        if fiscal_position and type:
            obj = self.pool.get('account.fiscal.position')
            if obj.browse(cr, uid, fiscal_position, context).intracommunity_operations:
                if type == 'out_invoice':
                    # Set to supplies when type is
                    #'out_invoice' (Customer invoice)
                    res = {'value': {'operation_key': 'E'}}
                else:
                    # Set to acquisition when type is
                    #'in_invoice' (Supplier invoice)
                    res = {'value': {'operation_key': 'A'}}

        return res

    def onchange_partner_id(self, cr, uid, ids,
                            type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False,
                            company_id=False, context=None):
        """
        Inheritance to extend method and return operation key
        """
        ##
        ## Get original data from onchange method
        res = super(account_invoice,
                    self).onchange_partner_id(cr,
                                              uid,
                                              ids,
                                              type,
                                              partner_id,
                                              date_invoice=date_invoice,
                                              payment_term=payment_term,
                                              partner_bank_id=partner_bank_id,
                                              company_id=company_id,
                                              context)

        ##
        ## Get operation key for current record
        operation_key_dict = self.on_change_fiscal_position(cr, uid, ids,
            fiscal_position=res['value']['fiscal_position'], type=type,
            context)

        ##
        ## Add operation key to result
        if operation_key_dict['value'] and \
            operation_key_dict['value']['operation_key']:
            res['value']['operation_key'] = \
            operation_key_dict['value']['operation_key']
        else:
            res['value']['operation_key'] = False

        return res

    def create(self, cr, uid, vals, context=None):
        """Writes operation key value, if invoice is created in
        backgroud with intracommunity fiscal position defined"""
        if context is None:
            context = {}

        if vals.get('fiscal_position') and \
            vals.get('type') and not vals.get('operation_key'):
            obj = self.pool.get('account.fiscal.position')
            if obj.browse(cr, uid,
                          vals.get('fiscal_position'), context
                          ).intracommunity_operations:
                if vals.get('type') == 'out_invoice':
                    vals['operation_key'] = 'E'
                else:
                    vals['operation_key'] = 'A'

        return super(account_invoice, self).create(cr, uid, vals, context)

    _columns = {
        'operation_key': fields.selection(OPERATION_KEY, 'Operation key')
    }

