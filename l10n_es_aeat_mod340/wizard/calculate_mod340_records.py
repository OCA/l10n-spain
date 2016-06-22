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

import time
import re
from openerp.tools.translate import _
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_is_zero
import logging
_logger = logging.getLogger(__name__)

VALID_TYPES = [0, 0.005, 0.014, 0.04, 0.052, 0.07, 0.08, 0.10, 0.12, 0.16, 0.18, 0.21]

class L10nEsAeatMod340CalculateRecords(orm.TransientModel):
    _name = "l10n.es.aeat.mod340.calculate_records"
    _description = u"AEAT Model 340 Wizard - Calculate Records"

    def proximo(self, final, numeros):
        def el_menor(numeros):
            menor = numeros[0]
            retorno = 0
            for x in range(len(numeros)):
                if numeros[x] < menor:
                    menor = numeros[x]
                    retorno = x
            return retorno

        diferencia = []
        for x in range(len(numeros)):
            diferencia.append(abs(final - numeros[x]))
        return numeros[el_menor(diferencia)]

    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        report_obj = self.pool['l10n.es.aeat.mod340.report']
        mod340 = report_obj.browse(cr, uid, ids)[0]
        invoices340 = self.pool['l10n.es.aeat.mod340.issued']
        invoices340_rec = self.pool['l10n.es.aeat.mod340.received']
        issued_obj = self.pool['l10n.es.aeat.mod340.tax_line_issued']
        received_obj = self.pool['l10n.es.aeat.mod340.tax_line_received']
        sequence_obj = self.pool['ir.sequence']
        mod340.write({
            'state': 'calculated',
            'calculation_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        })
        if not mod340.company_id.partner_id.vat:
            raise orm.except_orm(mod340.company_id.partner_id.name,
                                 _("This company doesn't have NIF"))
        account_period_ids = [x.id for x in mod340.periods]
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
        tax_code_rec_totals = {}
        tax_code_isu_totals = {}
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
            sign = 1
            if invoice.type in ('out_refund', 'in_refund'):
                sign = -1
            include = False
            if invoice.currency_id.id != invoice.company_id.currency_id.id:
                cur_rate = invoice.cc_amount_untaxed / invoice.amount_untaxed
            else:
                cur_rate = 1
            for tax_line in invoice.tax_line:
                if tax_line.base_code_id and tax_line.base:
                    if tax_line.base_code_id.mod340:
                        include = True
                        break
            partner = invoice.partner_id.commercial_partner_id
            if include:
                exception_text = ""

                # if partner.vat_type in ['1', '2']:
                #     if not partner.vat:
                #         # raise orm.except_orm(
                #         #     _('La siguiente empresa no tiene asignado nif:'),
                #         #     partner.name)
                #         exception_text += _('La siguiente empresa no'
                #                         ' tiene asignado nif: %s')\
                #                           % partner.name
                country_code = False
                nif = False
                if partner.vat:
                    country_code, nif = (
                        re.match(r"([A-Z]{0,2})(.*)",
                                 partner.vat).groups())
                    if country_code and country_code == 'EL':
                        country_code = 'GR'
                else:
                    if partner.country_id:
                        country_code = partner.country_id.code
                    else:
                        exception_text += _('La siguiente empresa no'
                        ' tiene un pais relacionado: %s')\
                        % partner.name

                values = {
                    'mod340_id': mod340.id,
                    'partner_id': partner.id,
                    'partner_vat': partner.vat,
                    'representative_vat': '',
                    'partner_country_code': country_code,
                    'invoice_id': invoice.id,
                    'base_tax': invoice.cc_amount_untaxed * sign,
                    'amount_tax': invoice.cc_amount_tax * sign,
                    'total': invoice.cc_amount_total * sign,
                    'date_invoice': invoice.date_invoice,
                    'record_number': sequence_obj.get(cr, uid, 'mod340'),
                }
                date_payment = False
                payment_amount = 0
                name_payment_method = ''
                if invoice.vat_on_payment:
                    for payment_id in invoice.payment_ids:
                        if not date_payment:
                            date_payment = payment_id.date
                        if not name_payment_method:
                            name_payment_method_id = self.pool['res.partner.bank'].search(
                                cr, uid, [('journal_id', '=', payment_id.journal_id.id)],
                                    context=context)[0]
                            if name_payment_method_id:
                                name_payment_method = self.pool['res.partner.bank'].browse(
                                    cr, uid, name_payment_method_id, context=context).acc_number
                                if name_payment_method:
                                    name_payment_method = name_payment_method.replace(' ', '')
                        payment_amount = payment_amount + payment_id.debit
                    values.update({
                        'date_payment':date_payment,
                        'payment_amount':payment_amount,
                        'name_payment_method':name_payment_method,
                        })

                key_identification = '6'
                if not partner.vat:
                    key_identification = '6'
                else:
                    if country_code:
                        if country_code == 'ES':
                            key_identification = '1'
                        else:
                            group_country_europe = self.pool['res.country.group'].search(cr, uid,
                                [('name','=', 'Europe')], context=context)
                            if group_country_europe:
                                if country_code == 'EL':
                                    country_code = 'GR'
                                country_ids = self.pool['res.country'].search(cr, uid,[
                                    ('code','=', country_code),
                                    ('country_group_ids','=', group_country_europe[0])], context=context)
                                if country_ids and invoice.fiscal_position.intracommunity_operations:
                                    key_identification = '2'

                # Clave de operación
                key_operation = ' '
                if invoice.type in ['out_invoice', 'out_refund']:
                    if invoice.type == 'out_refund':
                        key_operation = 'D'
                    elif invoice.is_ticket_summary == 1:
                        key_operation = 'B'
                    elif invoice.vat_on_payment:
                        key_operation = 'Z'
                    elif invoice.is_leasing_invoice()[0]:
                        key_operation = 'R'
                else:
                    if invoice.is_reverse_charge_invoice()[0]:
                        key_operation = 'I'
                    elif invoice.fiscal_position.intracommunity_operations:
                        key_operation = 'P'
                    elif invoice.vat_on_payment:
                        key_operation = 'Z'
                    elif invoice.type == 'in_refund':
                        key_operation = 'D'
                    elif invoice.is_leasing_invoice()[0]:
                        key_operation = 'R'

                values.update({
                    'vat_type' : key_identification,
                    'key_operation' : key_operation
                })

                if invoice.type in ['out_invoice', 'out_refund']:
                    invoice_created = invoices340.create(cr, uid, values)
                if invoice.type in ['in_invoice', 'in_refund']:
                    values.update({'supplier_invoice_number': invoice.supplier_invoice_number or invoice.reference or ''})
                    invoice_created = invoices340_rec.create(cr, uid, values)
                tot_invoice = invoice.cc_amount_untaxed * sign
                check_base = 0

                invoice_base_tax = 0
                invoice_amount_tax = 0

                # Add the invoices detail to the partner record
                surcharge_taxes_lines = []

                adqu_intra = False
                lines_created = 0

                if invoice.fiscal_position.intracommunity_operations \
                    and invoice.type in ("in_invoice", "in_refund"):
                    adqu_intra = True
                for tax_line in invoice.tax_line:
                    if tax_line.base_code_id and tax_line.base:
                        if tax_line.base_code_id.mod340:
                            # Si es una linea de recargo la gurada para
                            # gestionarla al acabar con las lienas normales"
                            if tax_line.base_code_id.surcharge_tax_id:
                                surcharge_taxes_lines.append(tax_line)
                            else:
                                tax_percentage = self.proximo(round (
                                        abs(tax_line.amount/tax_line.base), 4),\
                                    VALID_TYPES)

                                values = {
                                    'name': tax_line.name,
                                    'tax_percentage': tax_percentage,
                                    'tax_amount': tax_line.amount * sign *
                                                  cur_rate,
                                    'base_amount': tax_line.base_amount,
                                    'invoice_record_id': invoice_created,
                                    'tax_code_id': tax_line.base_code_id.id
                                }

                                invoice_base_tax = invoice_base_tax + values['base_amount']
                                invoice_amount_tax = invoice_amount_tax + values['tax_amount']

                                domain = [
                                    ('invoice_record_id', '=', invoice_created),
                                    ('tax_code_id', '=', tax_line.base_code_id.id),
                                    ('tax_percentage','=', tax_percentage),
                                ]
                                if sign == 1:
                                    domain.append(('tax_amount', '>=', 0))
                                else:
                                    domain.append(('tax_amount', '<=', 0))

                                if invoice.type in ("out_invoice",
                                                    "out_refund"):
                                    line_id = issued_obj.search(cr, uid, domain,
                                                                  context=context)
                                    if line_id:
                                        issue = issued_obj.browse(cr,uid, line_id[0], context = context)
                                        values['name'] = "%s/%s" % (issue.name,values['name'])
                                        values['tax_amount'] = issue.tax_amount + values['tax_amount']
                                        values['base_amount'] = issue.base_amount + values['base_amount']
                                        issued_obj.write(cr, uid, line_id[0], values)
                                    else:
                                        lines_created = lines_created+1
                                        issued_obj.create(cr, uid, values)

                                    if not tax_code_isu_totals.get(
                                            tax_line.base_code_id.id):
                                        tax_code_isu_totals.update({
                                            tax_line.base_code_id.id:[
                                                tax_line.base_amount,
                                                tax_line.amount * sign *
                                                cur_rate, tax_percentage],})
                                    else:
                                        tax_code_isu_totals[
                                            tax_line.base_code_id.id][
                                            0] +=\
                                            tax_line.base_amount
                                        tax_code_isu_totals[
                                            tax_line.base_code_id.id][
                                            1] += tax_line.amount * sign * \
                                                  cur_rate

                                if invoice.type in ("in_invoice",
                                                    "in_refund"):
                                    line_id = received_obj.search(cr, uid, domain,
                                                                  context=context)
                                    if line_id:
                                        recei = received_obj.browse(cr,uid, line_id[0], context = context)
                                        values['name'] = "%s/%s" % (recei.name,values['name'])
                                        values['tax_amount'] = recei.tax_amount + values['tax_amount']
                                        values['base_amount'] = recei.base_amount + values['base_amount']
                                        received_obj.write(cr, uid, line_id[0], values)
                                    else:
                                        lines_created = lines_created+1
                                        received_obj.create(cr, uid, values)

                                    if not tax_code_rec_totals.get(
                                            tax_line.base_code_id.id):
                                        tax_code_rec_totals.update({
                                            tax_line.base_code_id.id: [
                                                tax_line.base_amount,
                                                tax_line.amount * sign *
                                                cur_rate, tax_percentage]})
                                    else:
                                        tax_code_rec_totals[
                                            tax_line.base_code_id.id][
                                            0] += tax_line.base_amount
                                        tax_code_rec_totals[
                                            tax_line.base_code_id.id][
                                            1] += tax_line.amount * sign * cur_rate

                                if tax_line.amount >= 0:
                                    check_base += tax_line.base_amount
                                # Control problem with extracomunitary
                                # purchase  invoices
                                    if not adqu_intra:
                                        tot_invoice += tax_line.amount * sign * \
                                               cur_rate

                values = {'base_tax': invoice_base_tax,
                        'amount_tax': invoice_amount_tax}

                if lines_created > 1 and key_operation == ' ':
                    values.update({'key_operation': 'C' })

                if tot_invoice != invoice.cc_amount_total:
                    values.update({'total': tot_invoice })
                if values:
                    if invoice.type in ['out_invoice', 'out_refund']:
                        invoices340.write(cr, uid, invoice_created, values)
                    if invoice.type in ['in_invoice', 'in_refund']:
                        invoices340_rec.write(cr, uid, invoice_created, values)
                rec_tax_invoice = 0

                for surcharge in surcharge_taxes_lines:
                    rec_tax_percentage = round(surcharge.amount /
                                               surcharge.base, 3)
                    rec_tax_invoice += surcharge.amount * sign * cur_rate
                    invoice_amount_tax += surcharge.amount * sign * cur_rate
                    values = {
                        'rec_tax_percentage': rec_tax_percentage,
                        'rec_tax_amount': surcharge.amount * sign * cur_rate
                    }
                    # GET correct tax_line from created in previous step
                    domain = [
                        ('invoice_record_id', '=', invoice_created),
                        ('tax_code_id', '=',
                        surcharge.base_code_id.surcharge_tax_id.id)
                    ]
                    line_id = issued_obj.search(cr, uid, domain,
                                                  context=context)
                    issued_obj.write(cr, uid, line_id, values)

                if invoice.type in ['out_invoice', 'out_refund']:
                    invoices340.write(cr, uid, invoice_created,
                                      {'amount_tax': invoice_amount_tax,
                                       'rec_amount_tax': rec_tax_invoice})
                if invoice.type in ['in_invoice', 'in_refund']:
                    invoices340_rec.write(cr, uid, invoice_created,
                                          {'amount_tax': invoice_amount_tax})
                sign = 1
                if invoice.type in ('out_refund', 'in_refund'):
                    sign = -1
                if not float_is_zero(invoice.cc_amount_untaxed * sign -
                                 check_base, precision_digits=1):
                #if str(invoice.cc_amount_untaxed * sign) != str(check_base):
                    exception_text += _('Invoice  %s, Amount untaxed Lines '
                                        '%.2f do not  correspond to '
                                        'AmountUntaxed on Invoice %.2f')\
                                      %(invoice.number, check_base,
                                        invoice.cc_amount_untaxed * sign)
                if exception_text:
                    if invoice.type in ['out_invoice', 'out_refund']:
                        invoices340.write(cr, uid, invoice_created,
                                            {'txt_exception': exception_text,
                                             'exception': True})
                    if invoice.type in ['in_invoice', 'in_refund']:
                        invoices340_rec.write(cr, uid, invoice_created,
                                            {'txt_exception': exception_text,
                                             'exception': True})
                    # raise orm.except_orm(
                    #     "REVIEW INVOICE",
                    #     _('Invoice  %s, Amount untaxed Lines %.2f do not '
                    #       'correspond to AmountUntaxed on Invoice %.2f') %
                    #     (invoice.number, check_base,
                    #      invoice.cc_amount_untaxed * sign))
        print tax_code_isu_totals
        summary_obj = self.pool['l10n.es.aeat.mod340.tax_summary']
        sum_ids = summary_obj.search(cr, uid, [('mod340_id', '=', mod340.id)])
        summary_obj.unlink (cr, uid, sum_ids)
        for tax_code_id, values in tax_code_isu_totals.items():
            vals = {
                'tax_code_id': tax_code_id,
                'sum_base_amount': values[0],
                'sum_tax_amount': values[1],
                'tax_percent': values[2],
                'mod340_id':mod340.id,
                'type': 'issued'
            }
            summary_obj.create(cr, uid, vals )
        for tax_code_id, values in tax_code_rec_totals.items():
            vals = {
                'tax_code_id': tax_code_id,
                'sum_base_amount': values[0],
                'sum_tax_amount': values[1],
                'tax_percent': values[2],
                'mod340_id': mod340.id,
                'type': 'received'
            }
            summary_obj.create(cr, uid, vals)
        if recalculate:
            mod340.write({
                'state': 'calculated',
                'calculation_date':
                time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })
        return True
