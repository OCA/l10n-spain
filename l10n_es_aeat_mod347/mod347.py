# -*- coding: utf-8 -*-
##############################################################################
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
from openerp.osv import fields, orm
from openerp.tools.translate import _
import re


class l10n_es_aeat_mod347_report(orm.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod347.report"
    _description = "AEAT 347 Report"

    def _calc_total_invoice(self, cr, uid, invoice, context=None):
        amount = invoice.cc_amount_untaxed
        for tax_line in invoice.tax_line:
            if tax_line.name.find('IRPF') == -1:
                amount += tax_line.tax_amount
        return amount

    def _get_default_address(self, cr, uid, partner, context=None):
        """Get the default invoice address of the partner"""
        partner_obj = self.pool['res.partner']
        address_ids = partner_obj.address_get(cr, uid, [partner.id],
                                              ['invoice', 'default'])
        if address_ids.get('invoice'):
            return partner_obj.browse(cr, uid, address_ids['invoice'],
                                      context=context)
        elif address_ids.get('default'):
            return partner_obj.browse(cr, uid, address_ids['default'],
                                      context=context)
        else:
            return None

    def _calculate_partner_records(self, cr, uid, partner, partner_ids,
                                  period_ids, report, context=None):
        """Search for invoices for the given partners, and check if exceeds
        the limit. If so, it creates the partner record."""
        invoice_obj = self.pool['account.invoice']
        partner_record_obj = self.pool['l10n.es.aeat.mod347.partner_record']
        invoice_record_obj = self.pool['l10n.es.aeat.mod347.invoice_record']
        receivable_partner_record_id = False
        # We will repeat the process for sales and purchases:
        for invoice_type, refund_type in zip(('out_invoice', 'in_invoice'),
                                             ('out_refund', 'in_refund')):
            # CHECK THE SALE/PURCHASES INVOICE LIMIT
            # (A and B operation keys)
            # Search for invoices to this partner (with account moves).
            invoice_ids = invoice_obj.search(cr, uid, [
                        ('partner_id', 'in', partner_ids),
                        ('type', '=', invoice_type),
                        ('period_id', 'in', period_ids),
                        ('state', '!=', 'draft')])
            refund_ids = invoice_obj.search(cr, uid, [
                        ('partner_id', 'in', partner_ids),
                        ('type', '=', refund_type),
                        ('period_id', 'in', period_ids),
                        ('state', '!=', 'draft')])
            invoices = invoice_obj.browse(cr, uid, invoice_ids,
                                          context=context)
            refunds = invoice_obj.browse(cr, uid, refund_ids, context=context)
            ## Calculate the invoiced amount
            ## Remove IRPF tax for invoice amount
            invoice_amount = 0
            for invoice in invoices:
                invoice_amount += self._calc_total_invoice(cr, uid,
                                        invoice, context=context)
            refund_amount = 0
            for refund in refunds:
                refund_amount += self._calc_total_invoice(cr, uid,
                                        refund, context=context)
            total_amount = invoice_amount - refund_amount
            ## If the invoiced amount is greater than the limit
            ## we will add an partner record to the report.
            if total_amount > report.operations_limit:
                if invoice_type == 'out_invoice':
                    operation_key = 'B'  # Note: B = Sale operations
                else:
                    assert invoice_type == 'in_invoice'
                    operation_key = 'A'  # Note: A = Purchase operations
                address = self._get_default_address(cr, uid, partner,
                                               context=context)
                # Get the partner data
                partner_vat = partner.vat and re.match(r"([A-Z]{0,2})(.*)",
                                                       partner.vat).groups()[1]
                partner_country_code = address.country_id and address.country_id.code or ''
                if partner.vat:
                    partner_country_code, partner_vat = re.match("(ES){0,1}(.*)", partner.vat).groups()
                # Create the partner record
                partner_record_id = partner_record_obj.create(cr, uid, {
                        'report_id': report.id,
                        'operation_key': operation_key,
                        'partner_id': partner.id,
                        'partner_vat': partner_vat,
                        'representative_vat': '',
                        'partner_state_code': (address.state_id and
                                               address.state_id.code or ''),
                        'partner_country_code': partner_country_code,
                        'amount': total_amount,
                    })
                if invoice_type == 'out_invoice':
                    receivable_partner_record_id = partner_record_id
                # Add invoices detail to the partner record
                for invoice in invoices:
                    amount = self._calc_total_invoice(cr, uid,
                                        invoice, context=context)
                    invoice_record_obj.create(cr, uid, {
                        'partner_record_id': partner_record_id,
                        'invoice_id': invoice.id,
                        'date': invoice.date_invoice,
                        'amount': amount,
                    })
                for refund in refunds:
                    amount = self._calc_total_invoice(cr, uid,
                                    refund, context=context)
                    invoice_record_obj.create(cr, uid, {
                        'partner_record_id': partner_record_id,
                        'invoice_id': refund.id,
                        'date': refund.date_invoice,
                        'amount': -amount,
                    })
        return receivable_partner_record_id

    def _calculate_cash_records(self, cr, uid, partner, partner_ids,
                        partner_record_id, period_ids, report, context=None):
        """Search for payments received in cash from the given partners.
        @param partner: Partner for generating cash records.
        @param partner_ids: List of ids that corresponds to the same partner.
        @param partner_record_id: Possible previously created 347 record for
            the same partner.
        """
        partner_record_obj = self.pool['l10n.es.aeat.mod347.partner_record']
        cash_record_obj = self.pool['l10n.es.aeat.mod347.cash_record']
        move_line_obj = self.pool['account.move.line']
        # Get the cash journals (moves on this journals are considered cash)
        cash_journal_ids = self.pool['account.journal'].search(cr, uid,
                            [('type', '=', 'cash')])
        if not cash_journal_ids:
            return
        cash_account_move_line_ids = move_line_obj.search(cr, uid,
            [('partner_id', 'in', partner_ids),
             ('account_id', '=', partner.property_account_receivable.id),
             ('journal_id', 'in', cash_journal_ids),
             ('period_id', 'in', period_ids)],
            context=context)
        cash_account_move_lines = move_line_obj.browse(cr, uid,
                    cash_account_move_line_ids, context=context)
        # Calculate the cash amount in report fiscalyear
        received_cash_amount = sum([line.credit for line in cash_account_move_lines])
        # Add the cash detail to the partner cash_move_fy_id if over limit
        if received_cash_amount > report.received_cash_limit:
            address = self._get_default_address(cr, uid, partner,
                                                context=context)
            # Get the partner data
            partner_vat = partner.vat and re.match(r"([A-Z]{0,2})(.*)",
                                                   partner.vat).groups()[1]
            partner_country_code = address.country_id and address.country_id.code or ''
            if partner.vat:
                partner_country_code, partner_vat = re.match("(ES){0,1}(.*)", partner.vat).groups()
            cash_moves = {}
            # Group cash move lines by origin operation fiscalyear
            for move_line in cash_account_move_lines:
                #FIXME: ugly group by reconciliation invoices, because there isn't any direct relationship between payments and invoice
                invoices = []
                if move_line.reconcile_id:
                    for line in move_line.reconcile_id.line_id:
                        if line.invoice:
                            invoices.append(line.invoice)
                elif move_line.reconcile_partial_id:
                    for line in move_line.reconcile_partial_id.line_partial_ids:
                        if line.invoice:
                            invoices.append(line.invoice)
                invoices = list(set(invoices))
                if invoices:
                    invoice = invoices[0]
                    cash_move_fy_id = invoice.period_id.fiscalyear_id.id
                    if cash_move_fy_id not in cash_moves:
                        cash_moves[cash_move_fy_id] = [move_line]
                    else:
                        cash_moves[cash_move_fy_id].append(move_line)
            for cash_move_fy_id in cash_moves.keys():
                receivable_amount = sum([line.credit for line in cash_moves[cash_move_fy_id]])
                if receivable_amount > report.received_cash_limit:
                    if cash_move_fy_id != report.fiscalyear_id.id or not partner_record_id:
                        #create partner cash_move_fy_id for cash operation in different year to currently
                        cash_partner_record_id = partner_record_obj.create(cr, uid, {
                            'report_id': report.id,
                            'operation_key' : 'B',
                            'partner_id': partner.id,
                            'partner_vat': partner_vat,
                            'representative_vat': '',
                            'partner_state_code': (address.state_id and
                                                   address.state_id.code or ''),
                            'partner_country_code': partner_country_code,
                            'amount': 0.0,
                            'cash_amount': sum([line.credit for line in cash_moves[cash_move_fy_id]]),
                            'origin_fiscalyear_id': cash_move_fy_id,
                        })
                    else:
                        partner_record_obj.write(cr, uid,
                            partner_record_id,
                            {'cash_amount': sum([line.credit for line in cash_moves[cash_move_fy_id]]),
                             'origin_fiscalyear_id': cash_move_fy_id},
                            context=context)
                        cash_partner_record_id = partner_record_id
                    for line in cash_moves[cash_move_fy_id]:
                        cash_record_obj.create(cr, uid, {
                            'partner_record_id': cash_partner_record_id,
                            'move_line_id': line.id,
                            'date': line.date,
                            'amount': line.credit,
                        })

    def calculate(self, cr, uid, ids, context=None):
        partner_obj = self.pool['res.partner']
        partner_record_obj = self.pool['l10n.es.aeat.mod347.partner_record']
        for report in self.browse(cr, uid, ids, context):
            # Delete previous partner records
            partner_record_obj.unlink(cr, uid, [r.id for
                                                r in
                                                report.partner_record_ids])
            # Get the fiscal year period ids of the non-special periods
            # (to ignore closing/opening entries)
            period_ids = [period.id for period in
                          report.fiscalyear_id.period_ids if not
                          period.special]
            # We will check every partner with not_in_mod347 flag unchecked
            visited_partners = []
            if report.only_supplier:
                partner_ids = partner_obj.search(cr, uid,
                                            [('not_in_mod347', '=', False),
                                            ('supplier', '=', True)])
            else:
                partner_ids = partner_obj.search(cr, uid,
                                            [('not_in_mod347', '=', False),
                                             '|',
                                             ('customer', '=', True),
                                             ('supplier', '=', True)])
            for partner in partner_obj.browse(cr, uid, partner_ids,
                                              context=context):
                if partner.id not in visited_partners:
                    receivable_partner_record = False
                    if partner.vat and report.group_by_cif:
                        if report.only_supplier:
                            partners_grouped = partner_obj.search(cr, uid,
                                            [('vat', '=', partner.vat),
                                            ('not_in_mod347', '=', False),
                                            ('supplier', '=', True)
                                            ])
                        else:
                            partners_grouped = partner_obj.search(cr, uid,
                                            [('vat', '=', partner.vat),
                                            ('not_in_mod347', '=', False)])
                    else:
                        partners_grouped = [partner.id]
                    visited_partners.extend(partners_grouped)
                    partner_record_id = self._calculate_partner_records(cr,
                            uid, partner, partners_grouped, period_ids, report,
                            context=context)
                    if partner.customer:
                        self._calculate_cash_records(cr, uid, partner,
                            partners_grouped, partner_record_id, period_ids,
                            report, context=context)
        return True

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        """
        Calculates the total_* fields from the line values.
        """
        res = {}
        for report in self.browse(cr, uid, ids, context=context):
            res[report.id] = {
                'total_partner_records': len(report.partner_record_ids),
                'total_amount': sum([
                                     record.amount for
                                     record in
                                     report.partner_record_ids]) or 0.0,
                'total_cash_amount': sum([
                                     record.cash_amount for
                                     record in
                                     report.partner_record_ids]) or 0.0,
                'total_real_state_transmissions_amount': sum([
                                     record.real_state_transmissions_amount for
                                     record in
                                     report.partner_record_ids]) or 0.,
                'total_real_state_amount': sum([
                                     record.amount for
                                     record in
                                     report.real_state_record_ids]) or 0,
                'total_real_state_records': len(report.real_state_record_ids),
            }
        return res

    _columns = {
        'contact_name': fields.char("Full Name", size=40),
        'contact_phone': fields.char("Phone", size=9),
        'group_by_cif': fields.boolean('Group by VAT'),
        'only_supplier': fields.boolean('Only Suppliers'),
        'operations_limit': fields.float('Invoiced Limit (1)',
                                         digits=(13, 2),
                                         help="The declaration will include "\
                                         "partners with the total of "\
                                         "operations over this limit"),
        'received_cash_limit': fields.float('Received cash Limit (2)',
                                            digits=(13, 2),
                                            help="The declaration will show" \
                                            "the total of cash operations"\
                                            " over this limit"),
        'charges_obtp_limit': fields.float('Charges on behalf of third parties Limit (3)',
                                           digits=(13, 2),
                                           help="The declaration will include"\
                                           " partners from which we received"\
                                           " payments, on behalf of third "\
                                           "parties, over this limit"),
        'total_partner_records': fields.function(_get_totals,
                                                 string="Partners records",
                                                 method=True,
                                                 type='integer',
                                                 multi="totals_multi"),
        'total_amount': fields.function(_get_totals,
                        string="Amount", method=True, type='float',
                        multi="totals_multi"),
        'total_cash_amount': fields.function(_get_totals,
                        string="Cash Amount", method=True, type='float',
                        multi="totals_multi"),
        'total_real_state_transmissions_amount': fields.function(_get_totals,
                        string="Real State Transmissions Amount",
                        method=True, type='float', multi="totals_multi"),
        'total_real_state_records': fields.function(_get_totals,
                        string="Real state records", method=True,
                        type='integer', multi="totals_multi"),
        'total_real_state_amount': fields.function(_get_totals,
                        string="Real State Amount", method=True, type='float',
                        multi="totals_multi"),
        'partner_record_ids': fields.one2many('l10n.es.aeat.mod347.partner_record',
                                              'report_id', 'Partner Records'),
        'real_state_record_ids': fields.one2many('l10n.es.aeat.mod347.real_state_record',
                                                 'report_id', 'Real State Records'),
        }

    _defaults = {
         'operations_limit': 3005.06,
         'charges_obtp_limit': 300.51,
         'received_cash_limit': 6000.00,
         'number': '347',
    }

    def button_confirm(self, cr, uid, ids, context=None):
        """Different check out in report"""
        for item in self.browse(cr, uid, ids, context):
            ## Browse partner record lines to check if all are correct (all fields filled)
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_state_code:
                    raise orm.except_orm(
                         _('Error!'), 
                         _("All partner state code field must be filled.\nPartner: %s (%s)") %
                         (partner_record.partner_id.name,
                           partner_record.partner_id.id))
                if not partner_record.partner_vat:
                    raise orm.except_orm(
                         _('Error!'), 
                         _("All partner vat number field must be filled.\nPartner: %s (%s)") %
                         (partner_record.partner_id.name,
                          partner_record.partner_id.id))
            for real_state_record in item.real_state_record_ids:
                if not real_state_record.state_code:
                    raise orm.except_orm(_('Error!'),
                        _("All real state records state code field must be filled."))
        return super(l10n_es_aeat_mod347_report, self).button_confirm(cr, uid,
                                                        ids, context=context)


class l10n_es_aeat_mod347_partner_record(orm.Model):
    """
    Represents a partner record for the 347 model.
    """
    _name = 'l10n.es.aeat.mod347.partner_record'
    _description = 'Partner Record'
    _rec_name = "partner_vat"

    def _get_quarter_totals(self, cr, uid, ids, field_name, arg,
                            context=None):
        result = {}
        for record  in self.browse(cr, uid, ids, context=context):
            result[record.id] = {
                'first_quarter': 0,
                'first_quarter_real_state_transmission_amount': 0,
                'second_quarter': 0,
                'second_quarter_real_state_transmission_amount': 0,
                'third_quarter': 0,
                'third_quarter_real_state_transmission_amount': 0,
                'fourth_quarter': 0,
                'fourth_quarter_real_state_transmission_amount': 0,
            }
            for invoice in record.invoice_record_ids:
                if invoice.invoice_id.period_id.quarter == 'first':
                    result[record.id]['first_quarter'] += invoice.amount
                elif invoice.invoice_id.period_id.quarter == 'second':
                    result[record.id]['second_quarter'] += invoice.amount
                elif invoice.invoice_id.period_id.quarter == 'third':
                    result[record.id]['third_quarter'] += invoice.amount
                elif invoice.invoice_id.period_id.quarter == 'fourth':
                    result[record.id]['fourth_quarter'] += invoice.amount
        return result

    def _get_lines(self, cr, uid, ids, context):
        invoice_record_obj = self.pool['l10n.es.aeat.mod347.invoice_record']
        res = []
        for invoice_record in invoice_record_obj.browse(cr, uid, ids, context):
            res.append(invoice_record.partner_record_id.id)
        return list(set(res))

    def _get_real_state_record_ids(self, cr, uid, ids, field_name, args,
                                   context=None):
        """
        Get the real state records from this record
        parent report for this partner.
        """
        res = {}
        real_state_record_obj = self.pool['l10n.es.aeat.mod347.real_state_record']
        for partner_record in self.browse(cr, uid, ids):
            res[partner_record.id] = []
            if partner_record.partner_id:
                res[partner_record.id] = real_state_record_obj.search(cr, uid, [
                            ('report_id', '=', partner_record.report_id.id),
                            ('partner_id', '=', partner_record.partner_id.id),
                            ])
        return res

    def _set_real_state_record_ids(self, cr, uid, field_name, values,
                                   args=None, context=None):
        """
        Set the real state records from this record 
        parent report for this partner.
        """
        if context is None:
            context = {}
        if values:
            real_state_record_obj = self.pool.get('l10n.es.aeat.mod347.real_state_record')
            for value in values:
                o_action, o_id, o_vals = value
                if o_action == 1:
                    real_state_record_obj.write(cr, uid, [o_id], o_vals)
                elif o_action == 2:
                    real_state_record_obj.unlink(cr, uid, [o_id])
                elif o_action == 0:
                    real_state_record_obj.create(cr, uid, o_vals)
        return True

    _columns = {
        'report_id': fields.many2one('l10n.es.aeat.mod347.report',
                                     'AEAT 347 Report',
                                     ondelete="cascade",
                                     select=1),
        'operation_key': fields.selection([
                    ('A', u'A - Adquisiciones de bienes y servicios superiores al límite (1)'),
                    ('B', u'B - Entregas de bienes y servicios superiores al límite (1)'),
                    ('C', u'C - Cobros por cuenta de terceros superiores al límite (3)'),
                    ('D', u'D - Adquisiciones efectuadas por Entidades Públicas (...) superiores al límite (1)'),
                    ('E', u'E - Subvenciones, auxilios y ayudas satisfechas por Ad. Públicas superiores al límite (1)'),
                    ('F', u'F - Ventas agencia viaje'),
                    ('G', u'G - Compras agencia viaje'),
                ], 'Operation Key'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'partner_vat': fields.char('VAT number', size=9),
        'representative_vat': fields.char('L.R. VAT number', size=9,
                                          help="Legal Representative VAT number"),
        'partner_country_code': fields.char('Country Code', size=2),
        'partner_state_code': fields.char('State Code', size=2),
        'first_quarter': fields.function(_get_quarter_totals,
                string="First Quarter",
                method=True, type='float', 
                multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'first_quarter_real_state_transmission_amount': fields.function(_get_quarter_totals,
                string="First Quarter Real State Transmission Amount",
                method=True, type='float',
                multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'second_quarter': fields.function(_get_quarter_totals,
                string="Second Quarter",
                method=True, type='float',
                multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'second_quarter_real_state_transmission_amount': fields.function(_get_quarter_totals,
                string="Second Quarter Real State Transmission Amount",
                method=True, type='float', multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'third_quarter': fields.function(_get_quarter_totals,
                string="Third Quarter",
                method=True, type='float',
                multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'third_quarter_real_state_transmission_amount': fields.function(_get_quarter_totals,
                string="Third Quarter Real State Transmission Amount",
                method=True, type='float',
                multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'fourth_quarter': fields.function(_get_quarter_totals,
                string="Fourth Quarter",
                method=True, type='float',
                multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'fourth_quarter_real_state_transmission_amount': fields.function(_get_quarter_totals,
                string="Fourth Quarter Real State Transmossion Amount",
                method=True, type='float',
                multi="quarter_multi", digits=(13, 2),
                store={
                    'l10n.es.aeat.mod347.invoice_record': (_get_lines, ['amount'], 10)
                    }),
        'amount': fields.float('Operations amount', digits=(13,2)),
        'cash_amount': fields.float('Received cash amount', digits=(13,2)),
        'real_state_transmissions_amount': fields.float('Real State Transmisions amount',
                                                        digits=(13, 2)),
        'insurance_operation': fields.boolean('Insurance Operation',
                        help="Only for insurance companies. Set to identify"\
                             " insurance operations aside from the rest."),
        'bussiness_real_state_rent': fields.boolean('Bussiness Real State Rent',
                        help="Set to identify real state rent operations"\
                                " aside from the rest. You'll need to fill"\
                                " in the real state info only when you are"\
                                " the one that receives the money."),
        'origin_fiscalyear_id': fields.many2one('account.fiscalyear',
                                                'Origin fiscal year',
                                help="Origin cash operation fiscal year"),
        'invoice_record_ids': fields.one2many('l10n.es.aeat.mod347.invoice_record',
                                              'partner_record_id',
                                              'Invoice records'),
        'real_state_record_ids': fields.function(_get_real_state_record_ids,
                    fnct_inv=_set_real_state_record_ids, method=True,
                    obj="l10n.es.aeat.mod347.real_state_record",
                    type="one2many", string='Real State Records', store=False),
        'cash_record_ids': fields.one2many('l10n.es.aeat.mod347.cash_record',
                                           'partner_record_id',
                                           'Payment records'),
    }

    _defaults = {
        'report_id': lambda self, cr, uid, context=None: (context and
                                            context.get('report_id', None)),
    }

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        """
        Loads some partner data (country and vat)
        when the selected partner changes.
        """
        partner_vat = ''
        partner_country_code = ''
        partner_state_code = ''
        if partner_id:
            partner = self.pool['res.partner'].browse(cr, uid, partner_id,
                                                      context=context)
            # Get the default invoice address of the partner
            address = None
            address_ids = self.pool.get('res.partner').address_get(cr,
                                    uid, [partner.id], ['invoice', 'default'])
            if address_ids.get('invoice'):
                address = self.pool.get('res.partner.address').browse(cr,
                                            uid, address_ids.get('invoice'))
            elif address_ids.get('default'):
                address = self.pool.get('res.partner.address').browse(
                                        cr, uid, address_ids.get('default'))
            partner_vat = partner.vat and re.match("(ES){0,1}(.*)",
                                                   partner.vat).groups()[1]
            partner_state_code = address.state_id and address.state_id.code or ''
            partner_country_code = address.country_id and address.country_id.code or ''
        return {'value': {
                    'partner_vat': partner_vat,
                    'partner_country_code': partner_country_code,
                    'partner_state_code': partner_state_code
                }}


class l10n_es_aeat_mod347_real_state_record(orm.Model):
    """
    Represents a real state record for the 347 model.
    """
    _name = 'l10n.es.aeat.mod347.real_state_record'
    _description = 'Real State Record'
    _rec_name = "reference"

    _columns = {
        'report_id': fields.many2one('l10n.es.aeat.mod347.report',
                                     'AEAT 347 Report', ondelete="cascade",
                                     select=1),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'partner_vat': fields.char('VAT number', size=32),
        'representative_vat': fields.char('L.R. VAT number', size=32,
                                    help="Legal Representative VAT number"),
        'amount': fields.float('Amount', digits=(13, 2)),
        'situation': fields.selection([
                    ('1', '1 - Spain but Basque Country and Navarra'),
                    ('2', '2 - Basque Country and Navarra'),
                    ('3', '3 - Spain, without catastral reference'),
                    ('4', '4 - Foreign'),
                ], 'Real state Situation'),
        'reference': fields.char('Catastral Reference', size=25),
        # 'address_id': fields.many2one('res.partner.address', 'Address'),
        'address_type': fields.char('Address type', size=5),
        'address': fields.char('Address', size=50),
        'number_type': fields.selection([
                    ('NUM', 'Number'),
                    ('KM.', 'Kilometer'),
                    ('S/N', 'Without number'),
                ], 'Number type'),
        'number': fields.integer('Number', size=5),
        'number_calification': fields.selection([
                    ('BIS', 'Bis'),
                    ('MOD', 'Mod'),
                    ('DUP', 'Dup'),
                    ('ANT', 'Ant'),
                ], 'Number calification'),
        'block': fields.char('Block', size=3),
        'portal': fields.char('Portal', size=3),
        'stairway': fields.char('Stairway', size=3),
        'floor': fields.char('Floor', size=3),
        'door': fields.char('Door', size=3),
        'complement': fields.char('Complement', size=40,
                        help="Complement (urbanization, industrial park...)"),
        'city': fields.char('City', size=30),
        'township': fields.char('Township', size=30),
        'township_code': fields.char('Township Code', size=5),
        'state_code': fields.char('State Code', size=2),
        'postal_code': fields.char('Postal code', size=5),
    }

    _defaults = {
        'report_id': lambda self, cr, uid, context=None: (context and
                                            context.get('report_id', None)),
        'partner_id': lambda self, cr, uid, context=None: (context and
                                            context.get('partner_id', None)),
        'partner_vat': lambda self, cr, uid, context=None: (context and
                                            context.get('partner_vat', None)),
        'representative_vat': lambda self, cr, uid, context=None: (context and
                                    context.get('representative_vat', None)),
    }

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        """
        Loads some partner data (country and vat)
        when the selected partner changes.
        """
        partner_vat = ''
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            partner_vat = partner.vat and re.match("(ES){0,1}(.*)",
                                                   partner.vat).groups()[1]
        return  { 'value': {'partner_vat': partner_vat} }


class l10n_es_aeat_mod347_invoice_record(orm.Model):
    """
    Represents an invoice record.
    """
    _name = 'l10n.es.aeat.mod347.invoice_record'
    _description = 'Invoice Record'

    _columns = {
        'partner_record_id': fields.many2one('l10n.es.aeat.mod347.partner_record',
                                             'Partner record',
                                             required=True, ondelete="cascade",
                                             select=1),
        'invoice_id': fields.many2one('account.invoice',
                                      'Invoice',
                                      required=True, ondelete="cascade"),
        'date': fields.date('Date'),
        'amount': fields.float('Amount'),
    }

    _defaults = {
        'partner_record_id': lambda self, cr, uid, context: context.get('partner_record_id',
                                                                        None),
    }


class l10n_es_aeat_mod347_cash_record(orm.Model):
    """
    Represents a payment record.
    """
    _name = 'l10n.es.aeat.mod347.cash_record'
    _description = 'Cash Record'

    _columns = {
        'partner_record_id': fields.many2one('l10n.es.aeat.mod347.partner_record',
                                             'Partner record',
                                             required=True,
                                             ondelete="cascade", select=1),
        'move_line_id': fields.many2one('account.move.line',
                                        'Account move line',
                                        required=True, ondelete="cascade"),
        'date': fields.date('Date'),
        'amount': fields.float('Amount'),
    }

    _defaults = {
        'partner_record_id': lambda self, cr, uid, context: context.get('partner_record_id',
                                                                        None),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
