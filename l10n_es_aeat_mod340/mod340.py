# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es) All Rights Reserved.
#    Copyright (c) 2011-2013 Acysos S.L.(http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                       http://www.NaN-tic.com
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
from openerp.tools.translate import _
import re

class l10n_es_aeat_mod340(orm.Model):

    def calculate(self, cr, uid, ids, context=None):
        for mod340 in self.browse(cr, uid, ids, context=context):
            invoices340 = self.pool['l10n.es.aeat.mod340.issued']
            invoices340_rec = self.pool['l10n.es.aeat.mod340.received']
            period_obj = self.pool['account.period']
            code = '340' + mod340.fiscalyear_id.code + ''
            code += mod340.period_to.date_stop[5:7] + '0001'
            account_period_ids = period_obj.build_ctx_periods(cr, uid,
                                  mod340.period_from.id, mod340.period_to.id)
            if not account_period_ids:
                raise orm.except_orm(_('Error'),
                   _("The periods selected don't belong to the fiscal year %s") 
                   % (mod340.fiscalyear_id.name))
            tot_base = 0
            tot_amount = 0
            tot_tot = 0
            tot_rec = 0
            #Limpieza de las facturas calculadas anteriormente
            del_ids = invoices340.search(cr, uid,
                                         [('mod340_id', '=', mod340.id)])
            if del_ids:
                invoices340.unlink(cr, uid, del_ids, context=context)
            del_ids = invoices340_rec.search(cr, uid,
                                             [('mod340_id', '=', mod340.id)])
            if del_ids:
                invoices340_rec.unlink(cr, uid, del_ids, context=context)
            domain = [('period_id', 'in', account_period_ids),
                      ('state', 'in', ('open', 'paid'))]
            invoice_obj = self.pool['account.invoice']
            invoice_ids = invoice_obj.search(cr, uid, domain, context=context)
            for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
                include = False
                for tax_line in invoice.tax_line:
                    if tax_line.base_code_id:
                        if tax_line.base_code_id.mod340:
                            include = True
                if include:
                    if invoice.partner_id.vat_type == 1:
                        if not invoice.partner_id.vat:
                            raise orm.except_orm(
                                _('La siguiente empresa no tiene asignado nif:'),
                                invoice.partner_id.name)
                    nif = invoice.partner_id.vat and re.match(r"([A-Z]{0,2})(.*)",
                                          invoice.partner_id.vat).groups()[1]
                    country_code = invoice.partner_id.country_id.code
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
                    if invoice.type in ('out_refund','in_refund'):
                        values['base_tax'] *=- 1
                        values['amount_tax'] *= -1
                        values['total'] *= -1
                    if invoice.type == "out_invoice" or invoice.type == "out_refund":
                        invoice_created = invoices340.create(cr, uid, values)
                    if invoice.type == "in_invoice" or invoice.type == "in_refund":
                        invoice_created = invoices340_rec.create(cr,uid,values)
                    tot_tax_invoice = 0
                    check_tax=0
                    check_base=0
                    # Add the invoices detail to the partner record
                    for tax_line in invoice.tax_line:
                        if tax_line.base_code_id:
                            if tax_line.base_code_id.mod340:
                                tax_percentage = tax_line.amount/tax_line.base
                                values = {
                                    'name': tax_line.name,
                                    'tax_percentage': tax_percentage,
                                    'tax_amount': tax_line.tax_amount,
                                    'base_amount': tax_line.base_amount,
                                    'invoice_record_id': invoice_created,
                                }
                                if invoice.type == "out_invoice" or invoice.type == "out_refund":
                                    issued_obj = self.pool.get('l10n.es.aeat.mod340.tax_line_issued')
                                    issued_obj.create(cr, uid, values)
                                if invoice.type == "in_invoice" or invoice.type == "in_refund":
                                    received_obj=self.pool.get('l10n.es.aeat.mod340.tax_line_received')
                                    received_obj.create(cr, uid, values)
                                tot_tax_invoice += tax_line.tax_amount
                                tot_rec += 1
                                check_tax += tax_line.tax_amount
                                if tax_percentage >= 0:
                                    check_base += tax_line.base_amount
                    tot_base += invoice.amount_untaxed
                    tot_amount += tot_tax_invoice
                    tot_tot += invoice.amount_untaxed + tot_tax_invoice
                    if invoice.type=="out_invoice" or invoice.type=="out_refund":
                        invoices340.write(cr, uid, invoice_created,
                                          {'amount_tax': tot_tax_invoice})
                    if invoice.type == "in_invoice" or invoice.type == "in_refund":
                        invoices340_rec.write(cr, uid, invoice_created,
                                              {'amount_tax': tot_tax_invoice})
                    sign = 1
                    if  invoice.type in ('out_refund', 'in_refund'):
                        sign = -1
                    if str(invoice.amount_untaxed * sign) != str(check_base):
                        raise orm.except_orm( "REVIEW INVOICE",
                          _('Invoice  %s, Amount untaxed Lines %.2f do not correspond to AmountUntaxed on Invoice %.2f' )
                          %(invoice.number, check_base,  invoice.amount_untaxed * sign))
            mod340.write({'total_taxable': tot_base,
                          'total_sharetax': tot_amount,
                          'number_records': tot_rec,
                          'total': tot_tot,
                          'number': code}, context=context)
        return True

    def _get_number_records(self, cr, uid,ids, field_name, args,
                            context=None):
        result = {}
        for id in ids:
            result[id] = {}.fromkeys(
               ['number_records', 'total_taxable', 'total_sharetax', 'total'],
               0.0)
        for model in self.browse(cr, uid, ids,context):
            for issue in model.issued:
                result[model.id]['number_records'] += len(issue.tax_line_ids)
                result[model.id]['total_taxable'] += issue.base_tax
                result[model.id]['total_sharetax'] += issue.amount_tax
                result[model.id]['total'] +=issue.base_tax + issue.amount_tax
            for issue in model.received:
                result[model.id]['number_records'] += len(issue.tax_line_ids)
                result[model.id]['total_taxable'] += issue.base_tax
                result[model.id]['total_sharetax'] += issue.amount_tax
                result[model.id]['total'] += issue.base_tax + issue.amount_tax
        return result

    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.aeat.mod340'
    _description = 'Model 340'
    _rec_name = "number"

    _columns = {
        'phone_contact' : fields.char('Phone Contact',size=9),
        'name_contact' : fields.char('Name And Surname Contact',size=40),
        'period_from': fields.many2one('account.period', 'Start period',
                states={'done': [('readonly', True)]}, required=True),
        'period_to': fields.many2one('account.period', 'End period',
                states={'done': [('readonly', True)]}, required=True),
        'issued': fields.one2many('l10n.es.aeat.mod340.issued', 'mod340_id',
                                  'Invoices Issued',
                                  states={'done': [('readonly', True)]}),
        'received': fields.one2many('l10n.es.aeat.mod340.received',
                                    'mod340_id','Invoices Received',
                                    states={'done': [('readonly', True)]}),
        'investment': fields.one2many('l10n.es.aeat.mod340.investment',
                                      'mod340_id','Property Investment'),
        'intracomunitarias': fields.one2many(
                             'l10n.es.aeat.mod340.intracomunitarias',
                             'mod340_id', 'Operations Intracomunitarias'),
        'ean13': fields.char('Electronic Code VAT reverse charge', size=16),
        'total_taxable':  fields.function(_get_number_records, method=True,
            type='float', string='Total Taxable', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'total_sharetax': fields.function(_get_number_records, method=True,
            type='float', string='Total Share Tax', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'number_records': fields.function(_get_number_records, method=True,
            type='integer', string='Records', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'total': fields.function(_get_number_records, method=True,
            type='float', string="Total", multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'calculation_date': fields.date('Calculation date', readonly=True),
        'attach_id':fields.many2one('ir.attachment', 
                                    'BOE file', readonly=True),
    }
    _defaults = {
        'number' : '340',
    }


class l10n_es_aeat_mod340_issued(orm.Model):
    _name = 'l10n.es.aeat.mod340.issued'
    _description = 'Invoices invoice'
    _columns = {
        'mod340_id': fields.many2one('l10n.es.aeat.mod340', 'Model 340',
                                     ondelete="cascade"),
        'partner_id':fields.many2one('res.partner','Partner',
                                     ondelete="cascade"),
        'partner_vat':fields.char('Company CIF/NIF',size=12),
        'representative_vat': fields.char('L.R. VAT number', size=9,
                                      help="Legal Representative VAT number"),
        'partner_country_code': fields.char('Country Code', size=2),
        'invoice_id':fields.many2one('account.invoice','Invoice',
                                     ondelete="cascade"),
        'base_tax':fields.float('Base tax bill',digits=(13,2)),
        'amount_tax':fields.float('Total tax',digits=(13,2)),
        'total':fields.float('Total',digits=(13,2)),
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_issued',
                                        'invoice_record_id', 'Tax lines'),
        'date_invoice': fields.date('Date Invoice', readonly=True),
    }

    _order = 'date_invoice asc, invoice_id asc'


class l10n_es_aeat_mod340_received(orm.Model):
    _name = 'l10n.es.aeat.mod340.received'
    _description = 'Invoices Received'
    _inherit = 'l10n.es.aeat.mod340.issued'
    _columns = {
        'tax_line_ids':fields.one2many('l10n.es.aeat.mod340.tax_line_received',
                                       'invoice_record_id', 'Tax lines'),
    }


class l10n_es_aeat_mod340_investment(orm.Model):
    _name = 'l10n.es.aeat.mod340.investment'
    _description = 'Property Investment'
    _inherit = 'l10n.es.aeat.mod340.issued'


class l10n_es_aeat_mod340_intracomunitarias(orm.Model):
    _name = 'l10n.es.aeat.mod340.intracomunitarias'
    _description = 'Operations Intracomunitarias'
    _inherit = 'l10n.es.aeat.mod340.issued'


class l10n_es_aeat_mod340_tax_line_issued(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_issued'
    _description = 'Mod340 vat lines issued'
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True),
        'tax_percentage': fields.float('Tax percentage',digits=(0,2)),
        'tax_amount': fields.float('Tax amount',digits=(13,2)),
        'base_amount': fields.float('Base tax bill',digits=(13,2)),
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.issued',
             'Invoice issued', required=True, ondelete="cascade", select=1),
    }


class l10n_es_aeat_mod340_tax_line_received(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_received'
    _description = 'Mod340 vat lines received'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'
    _columns = {
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.received',
             'Invoice received', required=True, ondelete="cascade", select=1),
    }
