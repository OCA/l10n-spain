# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Ting. All Rights Reserved
#    Copyright (c) 2011-2013 Acysos S.L.(http://acysos.com) All Rights Reserved
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

import threading
from openerp import netsvc
import time
import re
from openerp.tools.translate import _
from openerp.osv import orm
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_round


class l10n_es_aeat_mod340_calculate_records(orm.TransientModel):
    _name = "l10n.es.aeat.mod340.calculate_records"
    _description = u"AEAT Model 340 Wizard - Calculate Records"

    def _wkf_calculate_records(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        self._calculate_records(cr, uid, ids, context, recalculate=False)
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340.report',
                                ids and ids[0], 'calculate', cr)

    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        fiscal_position_tax_obj = self.pool.get('account.fiscal.position.tax')

        def _get_source_tax(tax_line, pct, inv):
            ''' Recupera cuál es el impuesto que originó la línea de impuesto a partir
                de su tipo y su código base '''
            for line in inv.invoice_line:
                for tax in line.invoice_line_tax_id:
                    if tax.base_code_id.id == tax_line.base_code_id.id and pct == tax.amount:
                        return tax
                    for child_tax in tax.child_ids:
                        if child_tax.base_code_id.id == tax_line.base_code_id.id and pct == child_tax.amount:
                            return child_tax
            raise orm.except_orm(_('Error'),
                                 _("Invoice %s: Unable to determine the tax line %s source tax. The base code of the source tax may have been changed, please recompute the invoice taxes") % (inv.number,tax_line.name)) 

        def _get_surcharged_tax(position_id, surcharge_id):
            mapping_ids = fiscal_position_tax_obj.search(cr, uid, [('position_id','=',position_id),
                                                                   ('tax_dest_id','=',surcharge_id)], context=context)
            if not mapping_ids:
                return False
            mapping = fiscal_position_tax_obj.browse(cr, uid, mapping_ids[0], context)
            mapping_ids = fiscal_position_tax_obj.search(cr, uid, [('position_id','=',position_id),
                                                                   ('tax_src_id','=',mapping.tax_src_id.id),
                                                                   ('tax_dest_id','!=',surcharge_id)], context=context)
            if not mapping_ids:
                return False
            mapping = fiscal_position_tax_obj.browse(cr, uid, mapping_ids[0], context)
            return mapping.tax_dest_id.id

        def _rounded_pct(allowed_pcts, pct, key, invoice, threshold=0.01):
            pcts = allowed_pcts[key]
            sign = 1
            if pct < 0:
                sign = -1
                pct = pct * -1
            candidates = [(x, abs(x-pct)) for x in pcts]
            candidates.sort(key=lambda x: x[1])
            if candidates[0][1] <= threshold:
                return candidates[0][0] * sign
            raise orm.except_orm(_('Error'),
                                 _("Invoice %s: No match found for tax percentage %s") % (invoice.number, pct))

        if context is None:
            context = {}

        try:
            report_obj = self.pool.get('l10n.es.aeat.mod340.report')
            mod340 = report_obj.browse(cr, uid, ids)[0]

            invoices340 = self.pool.get('l10n.es.aeat.mod340.issued')
            invoices340_rec = self.pool.get('l10n.es.aeat.mod340.received')
            invoices340_inv = self.pool.get('l10n.es.aeat.mod340.investment')
            invoices340_intra = self.pool.get('l10n.es.aeat.mod340.intracomunitarias')
            period_obj = self.pool.get('account.period')
            precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
            tax_obj = self.pool.get('account.tax')

            allowed_tax_pct = tax_obj._allowed_pct_by_ledger(cr, uid, context)
            ledger2obj = {
                'I': invoices340_inv,
                'J': invoices340_inv,
                'U': invoices340_intra,
                'E': invoices340,
                'F': invoices340,
                'R': invoices340_rec,
                'S': invoices340_rec
            }

            if not mod340.company_id.partner_id.vat:
                raise orm.except_orm(mod340.company_id.partner_id.name,
                                     _('This company dont have NIF'))

            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n.es.aeat.mod347.report',
                                    ids and ids[0], 'calculate', cr)

            account_period_ids = period_obj.build_ctx_periods(cr, uid,
                                  mod340.period_from.id, mod340.period_to.id)

            if len(account_period_ids) == 0:
                raise orm.except_orm(_('Error'),
                   _("The periods selected don't belong to the fiscal year %s")
                   % (mod340.fiscalyear_id.name))

            # Limpieza de las facturas calculadas anteriormente

            del_ids = invoices340.search(cr, uid, [('mod340_id', '=', mod340.id)])

            if del_ids:
                invoices340.unlink(cr, uid, del_ids, context=context)

            del_ids = invoices340_rec.search(cr, uid, [('mod340_id', '=', mod340.id)])

            if del_ids:
                invoices340_rec.unlink(cr, uid, del_ids, context=context)

            del_ids = invoices340_inv.search(cr, uid, [('mod340_id', '=', mod340.id)])

            if del_ids:
                invoices340_inv.unlink(cr, uid, del_ids, context=context)

            del_ids = invoices340_intra.search(cr, uid, [('mod340_id', '=', mod340.id)])

            if del_ids:
                invoices340_intra.unlink(cr, uid, del_ids, context=context)

            domain = [('period_id', 'in', account_period_ids),
                      ('state', 'in', ('open', 'paid'))]

            invoice_obj = self.pool.get('account.invoice')
            invoice_ids = invoice_obj.search(cr, uid, domain, context=context)
            for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
                include = False
                for tax_line in invoice.tax_line:
                    if tax_line.base_code_id and tax_line.base:
                        if tax_line.base_code_id.mod340:
                            include = True
                            break
                if include:
                    if invoice.partner_id.vat_type == 1:
                        if not invoice.partner_id.vat:
                            raise orm.except_orm(
                                _('La siguiente empresa no tiene asignado nif:'),
                                invoice.partner_id.name)

                    nif = invoice.partner_id.vat and \
                        re.match(r"([A-Z]{0,2})(.*)",
                                 invoice.partner_id.vat).groups()[1]
                    country_code = invoice.partner_id.country_id.code
                    ledger_key, operation_key = invoice_obj.get_340_classification(cr, uid, invoice.id, context)
                    amounts = invoice_obj.get_cc_amounts(cr, uid, invoice.id, context)
                    values = {
                        'mod340_id': mod340.id,
                        'partner_id': invoice.partner_id.id,
                        'partner_vat': nif,
                        'representative_vat': '',
                        'partner_country_code': country_code,
                        'invoice_id': invoice.id,
                        'base_tax': amounts['cc_amount_untaxed'],
                        'total': amounts['cc_amount_total'],
                        'date_invoice': invoice.date_invoice,
                        'ledger_key': ledger_key,
                        'operation_key': operation_key
                    }
                    if ledger_key in ('I', 'J'):
                        values['use_date'] = invoice.date_invoice
                    if invoice.type in ('out_refund', 'in_refund'):
                        values['base_tax'] *= -1
                        values['total'] *= -1

                    invoice_created = ledger2obj[ledger_key].create(cr, uid, values)

                    tot_tax_invoice = 0
                    check_base = 0
                    added_tax_lines = []
                    values_taxes = {}
                    values_surcharges = {}
                    # Add the invoices detail to the partner record
                    for tax_line in invoice.tax_line:
                        if tax_line.base_code_id and tax_line.base:
                            if tax_line.base_code_id.mod340:
                                tax = tax_line.tax_id
                                tax_percentage = tax.amount

                                # El IVA agrario aunque tenga tipo 12% debe declararse con 0%
                                if tax.operation_key and tax.operation_key == 'X':
                                    tax_percentage = 0

                                # No se debe contar la base de los recargos
                                # de equivalencia o el check fallará al sumar
                                # el doble que el subtotal de la factura
                                if tax_percentage >= 0 and \
                                        tax.operation_key != '-':
                                    check_base += tax_line.base

                                # Los impuestos que se desdoblan en 2 hijos 
                                # como los de compras intra solo deben generar
                                # un registro
                                if (tax_line.base_amount, tax_percentage) \
                                        in added_tax_lines:
                                    continue

                                tot_tax_invoice += tax_line.tax_amount
                                added_tax_lines.append((tax_line.base_amount,
                                                        tax_percentage * -1))
                                values = {
                                    'name': tax_line.name,
                                    'tax_percentage': tax_percentage,
                                    'tax_amount': tax_line.tax_amount,
                                    'base_amount': tax_line.base_amount,
                                    'invoice_record_id': invoice_created,
                                }
                                if tax.ledger_key in ('I', 'J'):
                                    values['goods_identification'] = invoice_obj.get_inv_good_names(cr, uid, invoice.id, tax_percentage, context)

                                # Separamos recargos de los impuestos corrientes y agrupamos por impuesto
                                # Esta agrupación se hace porque un mismo impuesto OpenERP lo desdobla en 2 líneas de impuestos
                                # si hay líneas con importe positivo (línea impuesto con base con un signo) 
                                # y negativo (línea impuesto con base de signo opuesto)
                                if tax.operation_key and tax.operation_key == '-':
                                    if tax.id in values_surcharges:
                                        for key in ['tax_amount', 'base_amount']:
                                            values_surcharges[tax.id][key] += values[key]
                                    else:
                                        values_surcharges[tax.id] = values
                                else:
                                    if tax.id in values_taxes:
                                        for key in ['tax_amount', 'base_amount']:
                                            values_taxes[tax.id][key] += values[key]
                                    else:
                                        values_taxes[tax.id] = values

                    # Juntamos los recargos con los registros de impuestos a los que afectan
                    position_id = invoice.fiscal_position.id
                    for surcharge_id, values in values_surcharges.items():
                        surcharged_tax_id = _get_surcharged_tax(position_id, surcharge_id)
                        if not surcharged_tax_id:
                            raise orm.except_orm(_('Error'),
                                                 _("Invoice %s: Unable to determine the surcharged tax because it is not mapped in the partner's fiscal position %s") 
                                                 % (invoice.number, invoice.fiscal_position.name))
                        values_taxes[surcharged_tax_id]['surcharge_percentage'] = values['tax_percentage']
                        values_taxes[surcharged_tax_id]['surcharge_amount'] = values['tax_amount']

                    ledger2obj[ledger_key].write(cr, uid, invoice_created,
                                                 {'tax_line_ids': [(0,0, values) for values in values_taxes.values()],
                                                  'amount_tax':tot_tax_invoice}, context)

                    if abs(float_round(invoice.amount_untaxed, precision)-float_round(check_base, precision)) > 0.01:
                        raise orm.except_orm( "REVIEW INVOICE",
                          _('Invoice  %s, Amount untaxed on Lines %.2f do not correspond to AmountUntaxed on Invoice %.2f' )
                          %(invoice.number, check_base,
                            invoice.amount_untaxed))

            code = '340' + mod340.fiscalyear_id.code
            code += mod340.period_to.date_stop[5:7] + '0001'
            mod340.write({
                'declaration_number': code,
                'state': 'calculated',
                'calculation_date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })

        except Exception, ex:
            raise

        return True

    def calculation_threading(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        threaded_calculation = threading.Thread(target=self._calculate_records,
                                                args=(cr, uid, ids, context))
        threaded_calculation.start()

        return {}
