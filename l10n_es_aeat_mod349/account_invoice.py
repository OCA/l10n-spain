# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#        2004-2011: Pexego Sistemas Informáticos. (http://pexego.es)
#        2013:      Top Consultant Software Creations S.L.
#                   (http://www.topconsultant.es/)
#        2014:      Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                   Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#
#    Autores originales: Luis Manuel Angueira Blanco (Pexego)
#                        Omar Castiñeira Saavedra(omar@pexego.es)
#    Migración OpenERP 7.0: Ignacio Martínez y Miguel López.
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
from openerp.tools.translate import _
from openerp.osv import fields, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
import calendar

OPERATION_KEYS = [
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


class AccountInvoice(orm.Model):
    """Inheritance of account invoce to add some fields:
    - operation_key: Operation key of invoice
    """
    _inherit = 'account.invoice'

    def _assign_invoice_operation_keys(self, cr, uid, ids=None,
                                       context=None):
        """On first install of the module, this method is called to
        assign a default value to invoices and fiscal position"""
        # Marcar la posición fiscal intracomunitaria
        fp_obj = self.pool['account.fiscal.position']
        fp_ids = fp_obj.search(cr, uid,
                               [('name', '=', "Régimen Intracomunitario")],
                               context=context)
        if not fp_ids:
            return
        fp_obj.write(cr, uid, fp_ids, {'intracommunity_operations': True},
                     context=context)
        invoice_ids = self.search(cr, uid, [], context=context)
        for invoice in self.browse(cr, uid, invoice_ids, context=context):
            if invoice.fiscal_position:
                op_key = self._get_operation_key(invoice.fiscal_position,
                                                 invoice.type)
                self.write(cr, uid, invoice.id, {'operation_key': op_key},
                           context=context)

    def _get_operation_key(self, fp, invoice_type):
        if not fp.intracommunity_operations:
            return False
        else:
            # TODO: Ver cómo discernir si son prestación de servicios
            if invoice_type in ('out_invoice', 'out_refund'):
                # Establecer a entrega si es de venta
                return 'E'
            else:
                # Establecer a adquisición si es de compra
                return 'A'

    def _get_year_from_fy_month(self, fy, month):
        fy_start = datetime.strptime(fy.date_start,
                                     DEFAULT_SERVER_DATE_FORMAT)
        fy_stop = datetime.strptime(fy.date_stop,
                                    DEFAULT_SERVER_DATE_FORMAT)
        if fy_start.month < month:
            year = fy_start.year
        elif fy_stop.month > month:
            year = fy_stop.year
        else:
            raise orm.except_orm(
                _('Error'), _('Cannot get invoices.\nProvided month is not '
                              'included on selected fiscal year'))
        return year

    def _get_invoices_by_type(self, cr, uid, partner_id, operation_key,
                              fiscalyear_id=None, period_id=None, month=None,
                              period_selection=None, context=None):
        """
        Returns invoices ids by type (supplier/customer) for a fiscal
        year, period or month.
        """
        assert period_selection, 'There is no period selected'
        # Set type of invoice
        invoice_type = ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']
        fy_obj = self.pool['account.fiscalyear']
        fy = fy_obj.browse(cr, uid, fiscalyear_id, context=context)
        domain = [('partner_id', 'child_of', partner_id),
                  ('state', 'in', ['open', 'paid']),
                  ('type', 'in', invoice_type),
                  ('operation_key', '=', operation_key)]
        # Invoices by fiscalyear (Annual)
        if period_selection == '0A':
            if not fiscalyear_id:
                raise orm.except_orm(
                    _('Error'), _('Cannot get invoices.\nThere is no fiscal '
                                  'year selected'))
            domain.append(('period_id', 'in',
                           [period.id for period in fy.period_ids
                            if not period.special]))
        # Invoices by period
        elif period_selection in ['1T', '2T', '3T', '4T']:
            if not period_id:
                raise orm.except_orm(
                    _('Error'), _('Cannot get invoices.\nThere is no period '
                                  'selected'))
            domain.append(('period_id', 'in', period_id))
        # Invoices by month
        else:
            if not month and not fiscalyear_id:
                raise orm.except_orm(
                    _('Error'), _('Cannot get invoices.\nThere is no month '
                                  'and/or fiscal year selected'))
            month = int(month)
            year = self._get_year_from_fy_month(fy, month)
            month_last_day = calendar.monthrange(year, month)[1]
            date_start = datetime(year=year, month=month, day=1)
            date_stop = datetime(year=year, month=month, day=month_last_day)
            domain.append(
                ('date_invoice', '>=',
                 date_start.strftime(DEFAULT_SERVER_DATE_FORMAT)))
            domain.append(('date_invoice', '<=',
                           date_stop.strftime(DEFAULT_SERVER_DATE_FORMAT)))
        return self.search(cr, uid, domain, context=context)

    def clean_refund_invoices(self, cr, uid, ids, partner_id,
                              fiscalyear_id=None, period_id=None,
                              month=None, period_selection=None, context=None):
        """Separate refund invoices"""
        invoice_ids = []
        refund_ids = []
        fy_obj = self.pool['account.fiscalyear']
        fy = fy_obj.browse(cr, uid, fiscalyear_id, context=context)
        for refund in self.browse(cr, uid, ids, context=context):
            if refund.type in ['in_refund', 'out_refund']:
                if not refund.origin_invoices_ids:
                    invoice_ids.append(refund.id)
                    continue
                for origin_line in refund.origin_invoices_ids:
                    if (origin_line.state in ['open', 'paid'] and
                            origin_line.partner_id.id == partner_id):
                        if period_selection == '0A':
                            if (origin_line.period_id.id not in
                                    [period.id for period in
                                     fy.period_ids if not period.special]):
                                refund_ids.append(refund.id)
                            else:
                                invoice_ids.append(refund.id)
                        elif period_selection in ['1T', '2T', '3T', '4T']:
                            if origin_line.period_id.id != period_id:
                                refund_ids.append(refund.id)
                            else:
                                invoice_ids.append(refund.id)
                        else:
                            month = int(month)
                            year = self._get_year_from_fy_month(fy, month)
                            if (datetime.strptime(
                                    origin_line.date_invoice,
                                    DEFAULT_SERVER_DATE_FORMAT) <
                                    datetime(year=year, month=month, day=1)):
                                refund_ids.append(refund.id)
                            else:
                                invoice_ids.append(refund.id)
                        break
            else:
                invoice_ids.append(refund.id)
        return invoice_ids, refund_ids

    def on_change_fiscal_position(self, cr, uid, ids, fiscal_position,
                                  invoice_type, context=None):
        """Suggest an operation key when fiscal position changes."""
        res = {'operation_key': 'Nothing'}
        if fiscal_position and invoice_type:
            fp_obj = self.pool['account.fiscal.position']
            fp = fp_obj.browse(cr, uid, fiscal_position, context=context)
            res['operation_key'] = self._get_operation_key(fp, invoice_type)
        return {'value': res}

    def create(self, cr, uid, vals, context=None):
        """Writes operation key value, if invoice is created in
        backgroud with intracommunity fiscal position defined"""
        if vals.get('fiscal_position') and \
                vals.get('type') and not vals.get('operation_key'):
            fp_obj = self.pool['account.fiscal.position']
            fp = fp_obj.browse(cr, uid, vals['fiscal_position'],
                               context=context)
            vals['operation_key'] = self._get_operation_key(fp, vals['type'])
        return super(AccountInvoice, self).create(cr, uid, vals,
                                                  context=context)

    _columns = {
        'operation_key': fields.selection(OPERATION_KEYS, 'Operation key')
    }
