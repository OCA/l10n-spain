# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Ting. All Rights Reserved
#    Copyright (c) 2011-2013 Acysos S.L.(http://acysos.com)
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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

from openerp import netsvc
import time
import re
from openerp.tools.translate import _
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class L10nEsAeatMod340CalculateRecords(orm.TransientModel):
    _name = "l10n.es.aeat.mod340.calculate_records"
    _description = u"AEAT Model 340 Wizard - Calculate Records"

    def _wkf_calculate_records(self, cr, uid, ids, context=None):
        self._calculate_records(cr, uid, ids, context, recalculate=False)
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340.report',
                                ids and ids[0], 'calculate', cr)

    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        report_obj = self.pool['l10n.es.aeat.mod340.report']
        mod340 = report_obj.browse(cr, uid, ids)[0]
        invoices340 = self.pool['l10n.es.aeat.mod340.issued']
        invoices340_rec = self.pool['l10n.es.aeat.mod340.received']
        period_obj = self.pool['account.period']
        issued_obj = self.pool['l10n.es.aeat.mod340.tax_line_issued']
        received_obj = self.pool['l10n.es.aeat.mod340.tax_line_received']
        mod340.write({
            'state': 'calculated',
            'calculation_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        })
        if not mod340.company_id.partner_id.vat:
            raise orm.except_orm(mod340.company_id.partner_id.name,
                                 _('This company dont have NIF'))
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod347.report',
                                ids and ids[0], 'calculate', cr)
        code = '340' + mod340.fiscalyear_id.code + ''
        code += mod340.period_to.date_stop[5:7] + '0001'
        account_period_ids = period_obj.build_ctx_periods(
            cr, uid, mod340.period_from.id, mod340.period_to.id)
        if len(account_period_ids) is 0:
            raise orm.except_orm(
                _('Error'),
                _("The periods selected don't belong to the fiscal year %s")
                % (mod340.fiscalyear_id.name))

        # Limpieza de las facturas calculadas anteriormente
        del_ids = invoices340.search(cr, uid, [('mod340_id', '=', mod340.id)])
        if del_ids:
            invoices340.unlink(cr, uid, del_ids, context=context)
        del_ids = invoices340_rec.search(cr, uid,
                                         [('mod340_id', '=', mod340.id)])
        if del_ids:
            invoices340_rec.unlink(cr, uid, del_ids, context=context)
        domain = [
            ('period_id', 'in', account_period_ids),
            ('state', 'in', ('open', 'paid'))
        ]
        invoice_obj = self.pool['account.invoice']
        invoice_ids = invoice_obj.search(cr, uid, domain, context=context)
        warning_mod = False
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
            include = False
            errors = ""
            warning = False
            for tax_line in invoice.tax_line:
                if tax_line.base_code_id and tax_line.base:
                    if tax_line.base_code_id.mod340 is True:
                        include = True
            if include is True:
                if invoice.partner_id.vat_type:
                    if not invoice.partner_id.vat:
                        warning = True
                        warning_mod = True
                        errors += _('La siguiente empresa no tiene asignado '
                                    'nif: %s \n') % (invoice.partner_id.name)
                        country_code = ''
                        nif = ''
                    else:
                        country_code, nif = (re.match(r"([A-Z]{0,2})(.*)",
                                                      invoice.partner_id.vat
                                                      ).groups())
                values = {
                    'mod340_id': mod340.id,
                    'partner_id': invoice.partner_id.id,
                    'partner_vat': nif,
                    'representative_vat': '',
                    'partner_country_code': country_code,
                    'invoice_id': invoice.id,
                    'base_tax': invoice.amount_untaxed,
                    'amount_tax': invoice.amount_tax,
                    'total': invoice.amount_total,
                    'date_invoice': invoice.date_invoice,
                }
                if invoice.type in ['out_refund', 'in_refund']:
                    values['base_tax'] *= -1
                    values['amount_tax'] *= -1
                    values['total'] *= -1
                if invoice.type in ['out_invoice', 'out_refund']:
                    invoice_created = invoices340.create(cr, uid, values)
                if invoice.type in ['in_invoice', 'in_refund']:
                    invoice_created = invoices340_rec.create(cr, uid, values)
                tot_tax_invoice = 0
                check_tax = 0
                check_base = 0
                # Add the invoices detail to the partner record
                for tax_line in invoice.tax_line:
                    if tax_line.base_code_id and tax_line.base:
                        if tax_line.base_code_id.mod340:
                            tax_percentage = tax_line.amount/tax_line.base
                            values = {
                                'name': tax_line.name,
                                'tax_percentage': tax_percentage,
                                'tax_amount': tax_line.tax_amount,
                                'base_amount': tax_line.base_amount,
                                'invoice_record_id': invoice_created,
                            }
                            if invoice.type in ("out_invoice",
                                                "out_refund"):
                                issued_obj.create(cr, uid, values)
                            if invoice.type in ("in_invoice",
                                                "in_refund"):
                                received_obj.create(cr, uid, values)
                            tot_tax_invoice += tax_line.tax_amount
                            check_tax += tax_line.tax_amount
                            if tax_percentage >= 0:
                                check_base += tax_line.base_amount

                sign = 1
                if invoice.type in ('out_refund', 'in_refund'):
                    sign = -1
                if str(invoice.amount_untaxed * sign) != str(check_base):
                    warning = True
                    warning_mod = True
                    errors += _('Invoice  %s, Amount untaxed Lines %.2f do '
                                'not correspond to AmountUntaxed on Invoice'
                                ' %.2f \n') % (invoice.number, check_base,
                                               invoice.amount_untaxed * sign)

                if invoice.type in ['out_invoice', 'out_refund']:
                    invoices340.write(cr, uid, invoice_created,
                                      {'amount_tax': tot_tax_invoice,
                                       'warning': warning,
                                       'warn_message': errors})
                if invoice.type in ['in_invoice', 'in_refund']:
                    invoices340_rec.write(cr, uid, invoice_created,
                                          {'amount_tax': tot_tax_invoice,
                                           'warning': warning,
                                           'warn_message': errors})

        if recalculate:
            mod340.write({
                'state': 'calculated',
                'calculation_date':
                time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'warning': warning_mod
            })
        return True
