# -*- coding: utf-8 -*-
# Copyright 2011 Ting
# Copyright 2011-2013 Acysos S.L. - Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import re

from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError
from openerp.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)

VALID_TYPES = [
    0, 0.005, 0.014, 0.04, 0.052, 0.07, 0.08, 0.10, 0.12, 0.16, 0.18, 0.21
]


class L10nEsAeatMod340CalculateRecords(models.TransientModel):
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

    @api.model
    def _calculate_records(self, report_id):
        report = self.env['l10n.es.aeat.mod340.report'].browse(report_id)
        invoices340 = self.env['l10n.es.aeat.mod340.issued']
        invoices340_rec = self.env['l10n.es.aeat.mod340.received']
        issued_obj = self.env['l10n.es.aeat.mod340.tax_line_issued']
        received_obj = self.env['l10n.es.aeat.mod340.tax_line_received']
        sequence_obj = self.env['ir.sequence']
        country_group_europe = self.env.ref('base.europe')
        report.write({
            'state': 'calculated',
            'calculation_date': fields.Datetime.now(),
        })
        if not report.company_id.partner_id.vat:
            raise UserError(_("This company doesn't have NIF"))
        # Limpieza de las facturas calculadas anteriormente
        report.issued.unlink()
        report.received.unlink()
        domain = [
            ('period_id', 'in', report.periods.ids),
            ('state', 'in', ('open', 'paid'))
        ]
        tax_code_rec_totals = {}
        tax_code_isu_totals = {}
        for invoice in report.env['account.invoice'].search(domain):
            sign = 1
            if invoice.type in ('out_refund', 'in_refund'):
                sign = -1
            if not any(
                invoice.tax_line.filtered('base').mapped('base_code_id.mod340')
            ):
                continue
            if invoice.currency_id.id != invoice.company_id.currency_id.id \
                    and invoice.amount_untaxed:
                cur_rate = invoice.cc_amount_untaxed / invoice.amount_untaxed
            else:
                cur_rate = 1
            partner = invoice.partner_id.commercial_partner_id
            exception_text = ""
            country_code = False
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
                    exception_text += _(
                        'La siguiente empresa no tiene un pais relacionado: %s'
                    ) % partner.name
            values = {
                'mod340_id': report.id,
                'partner_id': partner.id,
                'partner_vat': (
                    partner.vat and partner.vat.replace('ES', '')) or '',
                'representative_vat': '',
                'partner_country_code': country_code,
                'invoice_id': invoice.id,
                'base_tax': invoice.cc_amount_untaxed * sign,
                'amount_tax': invoice.cc_amount_tax * sign,
                'total': invoice.cc_amount_total * sign,
                'date_invoice': invoice.date_invoice,
                'record_number': sequence_obj.next_by_code('mod340'),
            }
            key_identification = '6'
            if not partner.vat:
                key_identification = '6'
            else:
                if country_code == 'EL':
                    country_code = 'GR'
                if country_code == 'ES':
                    key_identification = '1'
                elif country_code:
                    eu_country = report.env['res.country'].search([
                        ('code', '=', country_code),
                        ('country_group_ids', 'in', country_group_europe.id)
                    ])
                    if eu_country and invoice.fiscal_position.\
                            intracommunity_operations:
                        key_identification = '2'
            # Clave de operación
            key_operation = ' '
            if invoice.type in ['out_invoice', 'out_refund']:
                if invoice.type == 'out_refund':
                    key_operation = 'D'
                elif invoice.is_ticket_summary == 1:
                    key_operation = 'B'
                elif invoice.is_leasing_invoice()[0]:
                    key_operation = 'R'
            else:
                if invoice.is_reverse_charge_invoice()[0]:
                    key_operation = 'I'
                elif invoice.fiscal_position.intracommunity_operations:
                    key_operation = 'P'
                elif invoice.type == 'in_refund':
                    key_operation = 'D'
                elif invoice.is_leasing_invoice()[0]:
                    key_operation = 'R'
            values.update({
                'vat_type': key_identification,
                'key_operation': key_operation,
            })
            if invoice.type in ['out_invoice', 'out_refund']:
                invoice_created = invoices340.create(values)
            if invoice.type in ['in_invoice', 'in_refund']:
                values.update({
                    'supplier_invoice_number': (
                        invoice.supplier_invoice_number or
                        invoice.reference or ''),
                })
                invoice_created = invoices340_rec.create(values)
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
            tax_lines = invoice.tax_line.filtered(
                lambda x: x.base_code_id.mod340 and x.base
            )
            for tax_line in tax_lines:
                if tax_line.base_code_id.surcharge_tax_id:
                    # Si es una linea de recargo la guarda para
                    # gestionarla al acabar con las líneas normales
                    surcharge_taxes_lines.append(tax_line)
                else:
                    tax_percentage = self.proximo(
                        round(abs(tax_line.amount / tax_line.base), 4),
                        VALID_TYPES,
                    )
                    values = {
                        'name': tax_line.name,
                        'tax_percentage': tax_percentage,
                        'tax_amount':
                            tax_line.amount * sign * cur_rate,
                        'base_amount': tax_line.base_amount,
                        'invoice_record_id': invoice_created.id,
                        'tax_code_id': tax_line.base_code_id.id
                    }
                    invoice_base_tax += values['base_amount']
                    invoice_amount_tax += values['tax_amount']
                    domain = [
                        ('invoice_record_id', '=', invoice_created.id),
                        ('tax_code_id', '=', tax_line.base_code_id.id),
                        ('tax_percentage', '=', tax_percentage),
                    ]
                    if sign == 1:
                        domain.append(('tax_amount', '>=', 0))
                    else:
                        domain.append(('tax_amount', '<=', 0))
                    if invoice.type in ("out_invoice", "out_refund"):
                        obj = issued_obj
                        dic = tax_code_isu_totals
                        key = 'issued'
                    else:
                        obj = received_obj
                        dic = tax_code_rec_totals
                        key = 'received'
                    record = obj.search(domain)
                    if record:
                        values['name'] += '/' + record.name
                        values['tax_amount'] += record.tax_amount
                        values['base_amount'] += record.base_amount
                        record.write(values)
                    else:
                        lines_created += 1
                        obj.create(values)
                    base_code = tax_line.base_code_id
                    if not dic.get(base_code):
                        dic[base_code] = {
                            'base': tax_line.base_amount,
                            'tax': tax_line.amount * sign * cur_rate,
                            'perc': tax_percentage,
                            key: invoice_created,
                        }
                    else:
                        dic[base_code]['base'] += tax_line.base_amount
                        dic[base_code]['tax'] += (
                            tax_line.amount * sign * cur_rate
                        )
                        dic[base_code][key] += invoice_created
                    if tax_line.amount >= 0:
                        check_base += tax_line.base_amount
                    # Control problem with extracommunitary purchase invoices
                    if not adqu_intra:
                        tot_invoice += tax_line.amount * sign * cur_rate
            values = {
                'base_tax': invoice_base_tax,
                'amount_tax': invoice_amount_tax,
            }
            if lines_created > 1 and key_operation == ' ':
                values['key_operation'] = 'C'
            if tot_invoice != invoice.cc_amount_total:
                values['total'] = tot_invoice
            if invoice.type in ['out_invoice', 'out_refund']:
                invoices340.write(invoice_created)
            if invoice.type in ['in_invoice', 'in_refund']:
                invoices340_rec.write(invoice_created)
            rec_tax_invoice = 0
            for surcharge in surcharge_taxes_lines:
                rec_tax_percentage = round(surcharge.amount /
                                           surcharge.base, 3)
                rec_tax_invoice += surcharge.amount * sign * cur_rate
                tot_invoice += surcharge.amount * sign * cur_rate
                values = {
                    'rec_tax_percentage': rec_tax_percentage,
                    'rec_tax_amount': surcharge.amount * sign * cur_rate
                }
                # GET correct tax_line from created in previous step
                domain = [
                    ('invoice_record_id', '=', invoice_created.id),
                    ('tax_code_id', '=',
                        surcharge.base_code_id.surcharge_tax_id.id)
                ]
                issued_obj.search(domain).write(values)
            if invoice.type in ['out_invoice', 'out_refund']:
                vals2 = {
                    'rec_amount_tax': rec_tax_invoice}
                if rec_tax_invoice:
                    vals2.update({'total': tot_invoice})
                invoice_created.write(vals2)
            if invoice.type in ['in_invoice', 'in_refund']:
                invoice_created.write({'amount_tax': invoice_amount_tax})
            sign = 1
            if invoice.type in ('out_refund', 'in_refund'):
                sign = -1
            if not float_is_zero(
                    invoice.cc_amount_untaxed * sign - check_base,
                    precision_digits=1):
                exception_text += _(
                    'Invoice %s, Amount untaxed Lines %.2f do not correspond '
                    'to AmountUntaxed on Invoice %.2f'
                ) % (
                    invoice.number, check_base,
                    invoice.cc_amount_untaxed * sign,
                )
            if exception_text:
                invoice_created.write({
                    'txt_exception': exception_text,
                    'exception': True,
                })
        summary_obj = report.env['l10n.es.aeat.mod340.tax_summary']
        report.summary_issued.unlink()
        report.summary_received.unlink()
        summary_types = {
            'issued': tax_code_isu_totals,
            'received': tax_code_rec_totals,
        }
        for summary_type, summary in summary_types.iteritems():
            for tax_code, values in summary.iteritems():
                summary_obj.create({
                    'tax_code_id': tax_code.id,
                    'sum_base_amount': values['base'],
                    'sum_tax_amount': values['tax'],
                    'tax_percent': values['perc'],
                    'mod340_id': report.id,
                    'issue_ids': [
                        (6, 0, values.get('issued', invoices340).ids)
                    ],
                    'received_ids': [
                        (6, 0, values.get('received', invoices340_rec).ids)
                    ],
                    'summary_type': summary_type,
                })
        return True
