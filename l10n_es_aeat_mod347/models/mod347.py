# -*- coding: utf-8 -*-
# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2012 NaN·Tic  (http://www.nan-tic.com)
# © 2013 Acysos (http://www.acysos.com)
# © 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#             (http://www.serviciosbaeza.com)
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from openerp import fields, models, api, exceptions, _
from openerp.addons import decimal_precision as dp


class L10nEsAeatMod347Report(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod347.report"
    _description = "AEAT 347 Report"
    _period_yearly = True
    _period_quarterly = False
    _period_monthly = False

    def _get_default_address(self, partner):
        """Get the default invoice address of the partner"""
        partner_obj = self.env['res.partner']
        address_ids = partner.address_get(['invoice', 'default'])
        if address_ids.get('invoice'):
            return partner_obj.browse(address_ids['invoice'])
        elif address_ids.get('default'):
            return partner_obj.browse(address_ids['default'])
        else:
            return None

    def _invoice_amount_get(self, invoices, refunds):
        invoice_amount = sum(x.amount_total_wo_irpf for x in invoices)
        refund_amount = sum(x.amount_total_wo_irpf for x in refunds)
        amount = invoice_amount - refund_amount
        if abs(amount) > self.operations_limit:
            return amount
        return 0

    def _cash_amount_get(self, moves):
        amount = sum([line.credit for line in moves])
        if abs(amount) > self.received_cash_limit:
            return amount
        return 0

    def _cash_moves_group(self, moves):
        cash_moves = {}
        # Group cash move lines by origin operation fiscalyear
        for move_line in moves:
            # FIXME: ugly group by reconciliation invoices, because there
            # isn't any direct relationship between payments and invoice
            invoices = []
            if move_line.reconcile_id:
                for line in move_line.reconcile_id.line_id:
                    if line.invoice:
                        invoices.append(line.invoice)
            elif move_line.reconcile_partial_id:
                for line in move_line.reconcile_partial_id.line_partial_ids:
                    if line.invoice:
                        invoices.append(line.invoice)
            # Remove duplicates
            invoices = list(set(invoices))
            if invoices:
                invoice = invoices[0]
                fy_id = invoice.period_id.fiscalyear_id.id
                if fy_id not in cash_moves:
                    cash_moves[fy_id] = [move_line]
                else:
                    cash_moves[fy_id].append(move_line)
        return cash_moves

    def _partner_record_a_create(self, data, vals):
        """ Partner record type A: Adquisiciones de bienes y servicios
            Create from income (from supplier) invoices
        """
        partner_record_obj = self.env['l10n.es.aeat.mod347.partner_record']
        record = False
        vals['operation_key'] = 'A'
        invoices = data.get('in_invoices', self.env['account.invoice'])
        refunds = data.get('in_refunds', self.env['account.invoice'])
        amount = self._invoice_amount_get(invoices, refunds)
        if amount:
            vals['amount'] = amount
            vals['invoice_record_ids'] = [
                (0, 0, {'invoice_id': x})
                for x in (invoices.ids + refunds.ids)]
            record = partner_record_obj.create(vals)
        return record

    def _partner_record_b_create(self, data, vals):
        """ Partner record type B: Entregas de bienes y servicios
            Create from outcome (from customer) invoices and cash movements
        """
        partner_record_obj = self.env['l10n.es.aeat.mod347.partner_record']
        cash_record_obj = self.env['l10n.es.aeat.mod347.cash_record']
        records = []
        invoice_record = False
        vals['operation_key'] = 'B'
        invoices = data.get('out_invoices', self.env['account.invoice'])
        refunds = data.get('out_refunds', self.env['account.invoice'])
        moves = data.get('cash_moves', self.env['account.move.line'])
        amount = self._invoice_amount_get(invoices, refunds)
        if amount:
            vals['amount'] = amount
            vals['invoice_record_ids'] = [
                (0, 0, {'invoice_id': x})
                for x in (invoices.ids + refunds.ids)]
            invoice_record = partner_record_obj.create(vals)
            if invoice_record:
                records.append(invoice_record)
        if self._cash_amount_get(moves):
            cash_moves = self._cash_moves_group(moves)
            for fy_id in cash_moves.keys():
                amount = self._cash_amount_get(cash_moves[fy_id])
                if amount:
                    if (fy_id != self.fiscalyear_id.id or not invoice_record):
                        vals['amount'] = 0.0
                        vals['cash_amount'] = amount
                        vals['origin_fiscalyear_id'] = fy_id
                        partner_record = partner_record_obj.create(vals)
                        if partner_record:
                            records.append(partner_record)
                    else:
                        invoice_record.write({
                            'cash_amount': amount,
                            'origin_fiscalyear_id': fy_id,
                        })
                        partner_record = invoice_record
                    for line in cash_moves[fy_id]:
                        cash_record_obj.create({
                            'partner_record_id': partner_record.id,
                            'move_line_id': line.id,
                            'date': line.date,
                            'amount': line.credit,
                        })
        return records

    def _partner_records_create(self, data):
        partner = data.get('partner')
        address = self._get_default_address(partner)
        partner_country_code, partner_vat = (
            re.match(r"([A-Z]{0,2})(.*)", partner.vat or '').groups())
        community_vat = ''
        if not partner_country_code:
            partner_country_code = address.country_id.code
        partner_state_code = address.state_id.code
        if partner_country_code != 'ES':
            partner_vat = ''
            community_vat = partner.vat
            partner_state_code = 99
        vals = {
            'report_id': self.id,
            'partner_id': partner.id,
            'partner_vat': partner_vat,
            'representative_vat': '',
            'community_vat': community_vat,
            'partner_state_code': partner_state_code,
            'partner_country_code': partner_country_code,
        }
        # Create A record
        self._partner_record_a_create(data, vals)
        # Create B records
        self._partner_record_b_create(data, vals)
        return True

    def _invoices_search(self, partners):
        invoice_obj = self.env['account.invoice']
        partner_obj = self.env['res.partner']
        domain = [
            ('state', 'in', ['open', 'paid']),
            ('period_id', 'in', self.periods.ids),
            ('not_in_mod347', '=', False),
            ('commercial_partner_id.not_in_mod347', '=', False),
        ]
        if self.only_supplier:
            domain.append(('type', 'in', ('in_invoice', 'in_refund')))
        key_field = 'id'
        if self.group_by_vat:
            key_field = 'vat'
        groups = invoice_obj.read_group(
            domain, ['commercial_partner_id'], ['commercial_partner_id'])
        for group in groups:
            partner = partner_obj.browse(group['commercial_partner_id'][0])
            key_value = partner[key_field]
            invoices = invoice_obj.search(group['__domain'])
            in_invoices = invoices.filtered(
                lambda x: x.type in 'in_invoice')
            in_refunds = invoices.filtered(
                lambda x: x.type in 'in_refund')
            out_invoices = invoices.filtered(
                lambda x: x.type in 'out_invoice')
            out_refunds = invoices.filtered(
                lambda x: x.type in 'out_refund')
            if key_value not in partners:
                partners[key_value] = {
                    # Get first partner found when grouping by vat
                    'partner': partner,
                    'in_invoices': in_invoices,
                    'in_refunds': in_refunds,
                    'out_invoices': out_invoices,
                    'out_refunds': out_refunds,
                }
            else:
                # No need to check here if *_invoices exists,
                # because this entry has been created in this method
                partners[key_value]['in_invoices'] += in_invoices
                partners[key_value]['in_refunds'] += in_refunds
                partners[key_value]['out_invoices'] += out_invoices
                partners[key_value]['out_refunds'] += out_refunds
        return partners

    def _cash_moves_search(self, partners):
        partner_obj = self.env['res.partner']
        move_line_obj = self.env['account.move.line']
        cash_journals = self.env['account.journal'].search(
            [('type', '=', 'cash')])
        if not cash_journals or self.only_supplier:
            return partners
        domain = [
            ('account_id.type', '=', 'receivable'),
            ('journal_id', 'in', cash_journals.ids),
            ('period_id', 'in', self.periods.ids),
            ('partner_id.not_in_mod347', '=', False),
        ]
        groups = move_line_obj.read_group(
            domain, ['partner_id'], ['partner_id'])
        key_field = 'id'
        if self.group_by_vat:
            key_field = 'vat'
        for group in groups:
            partner = partner_obj.browse(group['partner_id'][0])
            key_value = partner[key_field]
            moves = move_line_obj.search(group['__domain'])
            if key_value not in partners:
                partners[key_value] = {
                    # Get first partner found when grouping by vat
                    'partner': partner,
                    'cash_moves': moves,
                }
            else:
                # Check here if cash_moves exists, maybe this entry
                # has been created by _invoices_search
                if partners[key_value].get('cash_moves'):
                    partners[key_value]['cash_moves'] += moves
                else:
                    partners[key_value]['cash_moves'] = moves
        return partners

    @api.depends('partner_record_ids',
                 'partner_record_ids.amount',
                 'partner_record_ids.cash_amount',
                 'partner_record_ids.real_estate_transmissions_amount')
    def _get_partner_totals(self):
        """Calculates the total_* fields from the line values."""
        for record in self:
            record.total_partner_records = len(record.partner_record_ids)
            record.total_amount = (
                sum([x.amount for x in record.partner_record_ids]))
            record.total_cash_amount = (
                sum([x.cash_amount for x in record.partner_record_ids]))
            record.total_real_estate_transmissions_amount = (
                sum([x.real_estate_transmissions_amount for x in
                     record.partner_record_ids]))

    @api.depends('real_estate_record_ids',
                 'real_estate_record_ids.amount')
    def _get_real_state_totals(self):
        """Calculates the total_* fields from the line values."""
        for record in self:
            record.total_real_estate_amount = (
                sum([x.amount for x in record.real_estate_record_ids]))
            record.total_real_estate_records = (
                len(record.real_estate_record_ids))

    number = fields.Char(default='347')
    group_by_vat = fields.Boolean(
        string='Group by VAT number', oldname='group_by_cif')
    only_supplier = fields.Boolean(string='Only Suppliers')
    operations_limit = fields.Float(
        string='Invoiced Limit (1)', digits=dp.get_precision('Account'),
        default=3005.06,
        help="The declaration will include partners with the total of "
             "operations over this limit")
    received_cash_limit = fields.Float(
        string='Received cash Limit (2)', digits=dp.get_precision('Account'),
        default=6000.00,
        help="The declaration will show the total of cash operations over "
             "this limit")
    charges_obtp_limit = fields.Float(
        string='Charges on behalf of third parties Limit (3)',
        digits=dp.get_precision('Account'), default=300.51,
        help="The declaration will include partners from which we received "
             "payments, on behalf of third parties, over this limit")
    total_partner_records = fields.Integer(
        compute="_get_partner_totals", store=True, readonly=True,
        string="Partners records")
    total_amount = fields.Float(
        compute="_get_partner_totals", store=True, readonly=True,
        digits=dp.get_precision('Account'), string="Operations amount")
    total_cash_amount = fields.Float(
        compute="_get_partner_totals", store=True, readonly=True,
        digits=dp.get_precision('Account'), string="Cash movements amount")
    total_real_estate_transmissions_amount = fields.Float(
        compute="_get_partner_totals", store=True, readonly=True,
        digits=dp.get_precision('Account'),
        string="Real estate transmissions amount",
        oldname='total_real_state_transmissions_amount')
    total_real_estate_records = fields.Integer(
        compute="_get_real_state_totals", store=True, readonly=True,
        string="Real estate records",
        oldname='total_real_state_records')
    total_real_estate_amount = fields.Float(
        compute="_get_real_state_totals", store=True, readonly=True,
        digits=dp.get_precision('Account'), string="Real estate amount",
        oldname='total_real_state_amount')
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        inverse_name='report_id', string='Partner Records')
    real_estate_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.real_estate_record',
        inverse_name='report_id', string='Real Estate Records',
        oldname='real_state_record_ids')

    @api.multi
    def button_list_partner_records(self):
        return {
            'domain': "[('report_id','in'," + str(self.ids) + ")]",
            'name': _("Partner records"),
            'context': "{'default_report_id': %s}" % self.ids[0],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'l10n.es.aeat.mod347.partner_record',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def button_list_real_estate_records(self):
        return {
            'domain': "[('report_id','in'," + str(self.ids) + ")]",
            'name': _("Real estate records"),
            'context': "{'default_report_id': %s}" % self.ids[0],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'l10n.es.aeat.mod347.real_estate_record',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def button_confirm(self):
        """Different check out in report"""
        for item in self:
            # Browse partner record lines to check if all are correct (all
            # fields filled)
            partner_errors = []
            for partner_record in item.partner_record_ids:
                if not partner_record.check_ok:
                    partner_errors.append(
                        _("- %s (%s)") %
                        (partner_record.partner_id.name,
                         partner_record.partner_id.id))
            real_state_errors = []
            for real_estate_record in item.real_estate_record_ids:
                if not real_estate_record.check_ok:
                    real_state_errors.append(
                        _("- %s (%s)") %
                        (real_estate_record.partner_id.name,
                         real_estate_record.partner_id.id))
            error = _("Please review partner and real estate records, "
                      "some of them are in red color:\n\n")
            if partner_errors:
                error += _("Partner record errors:\n")
                error += '\n'.join(partner_errors)
                error += '\n\n'
            if real_state_errors:
                error += _("Real estate record errors:\n")
                error += '\n'.join(real_state_errors)
            if error:
                raise exceptions.ValidationError(error)
        return super(L10nEsAeatMod347Report, self).button_confirm()

    @api.multi
    def calculate(self):
        def _automatic_filter(self):
            return bool(self.invoice_record_ids or self.cash_record_ids)

        for report in self:
            # Delete previous partner records
            report.partner_record_ids.filtered(_automatic_filter).unlink()
            partners = {}
            # Read invoices: normal and refunds
            # We have to call _invoices_search always first
            partners = report._invoices_search(partners)
            # Read cash movements
            partners = report._cash_moves_search(partners)
            for k, v in partners.iteritems():
                report._partner_records_create(v)
        return True

    def __init__(self, pool, cr):
        self._aeat_number = '347'
        super(L10nEsAeatMod347Report, self).__init__(pool, cr)


class L10nEsAeatMod347PartnerRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.partner_record'
    _description = 'Partner Record'
    _rec_name = "partner_vat"

    @api.depends('invoice_record_ids',
                 'invoice_record_ids.invoice_id.type',
                 'invoice_record_ids.invoice_id.period_id.quarter',
                 'manual_first_quarter', 'manual_second_quarter',
                 'manual_third_quarter', 'manual_fourth_quarter')
    def _get_quarter_invoice_totals(self):
        def _invoices_normal(rec):
            return rec.invoice_id.type in ('out_invoice', 'in_invoice')

        def _invoices_refund(rec):
            return rec.invoice_id.type in ('out_refund', 'in_refund')

        def _invoices_sum(invoices, refunds, quarter):
            return (
                sum(x.amount for x in invoices
                    if x.invoice_id.period_id.quarter == quarter) -
                sum(x.amount for x in refunds
                    if x.invoice_id.period_id.quarter == quarter))

        for record in self:
            # Invoices
            if record.invoice_record_ids:
                invoices = record.invoice_record_ids.filtered(_invoices_normal)
                refunds = record.invoice_record_ids.filtered(_invoices_refund)
                # Go to normal mode for getting invoice data
                last_mode = self.env.all.mode
                self.env.all.mode = False
                first_quarter = _invoices_sum(invoices, refunds, 'first')
                second_quarter = _invoices_sum(invoices, refunds, 'second')
                third_quarter = _invoices_sum(invoices, refunds, 'third')
                fourth_quarter = _invoices_sum(invoices, refunds, 'fourth')
                # Return to current mode to save results
                self.env.all.mode = last_mode
                record.first_quarter = first_quarter
                record.second_quarter = second_quarter
                record.third_quarter = third_quarter
                record.fourth_quarter = fourth_quarter
            else:
                record.first_quarter = record.manual_first_quarter
                record.second_quarter = record.manual_second_quarter
                record.third_quarter = record.manual_third_quarter
                record.fourth_quarter = record.manual_fourth_quarter
            # Totals
            record.amount = sum([
                record.first_quarter, record.second_quarter,
                record.third_quarter, record.fourth_quarter])

    @api.depends('cash_record_ids',
                 'cash_record_ids.move_line_id.period_id.quarter')
    def _get_quarter_cash_totals(self):
        def _cash_moves_sum(records, quarter):
            return (sum(x.amount for x in records
                        if x.move_line_id.period_id.quarter == quarter))

        for record in self:
            # Cash
            if record.cash_record_ids:
                record.first_quarter_cash_amount = \
                    _cash_moves_sum(record.cash_record_ids, 'first')
                record.second_quarter_cash_amount = \
                    _cash_moves_sum(record.cash_record_ids, 'second')
                record.third_quarter_cash_amount = \
                    _cash_moves_sum(record.cash_record_ids, 'third')
                record.fourth_quarter_cash_amount = \
                    _cash_moves_sum(record.cash_record_ids, 'fourth')
            # Totals
            record.cash_amount = sum([
                record.first_quarter_cash_amount,
                record.second_quarter_cash_amount,
                record.third_quarter_cash_amount,
                record.fourth_quarter_cash_amount])

    @api.depends('first_quarter_real_estate_transmission_amount',
                 'second_quarter_real_estate_transmission_amount',
                 'third_quarter_real_estate_transmission_amount',
                 'fourth_quarter_real_estate_transmission_amount')
    def _get_quarter_real_state_totals(self):
        for record in self:
            # Totals
            record.real_estate_transmissions_amount = sum([
                record.first_quarter_real_estate_transmission_amount,
                record.second_quarter_real_estate_transmission_amount,
                record.third_quarter_real_estate_transmission_amount,
                record.fourth_quarter_real_estate_transmission_amount])

    @api.depends('invoice_record_ids', 'cash_record_ids')
    def _compute_automatic(self):
        for record in self:
            record.automatic = bool(
                record.invoice_record_ids or record.cash_record_ids)

    # TODO: By now user must fill real estate transmission amounts manually
    @api.one
    def _get_real_estate_record_ids(self):
        """Get the real estate records from this record parent report for this
        partner.
        """
        self.real_estate_record_ids = self.env[
            'l10n.es.aeat.mod347.real_estate_record']
        if self.partner_id:
            self.real_estate_record_ids = self.real_estate_record_ids.search(
                [('report_id', '=', self.report_id.id),
                 ('partner_id', '=', self.partner_id.id)])

    # @api.one
    # def _set_real_estate_record_ids(self, vals):
    #     """Set the real estate records from this record parent report for
    #     this partner.
    #     """
    #     if vals:
    #         real_estate_record_obj = self.env[
    #             'l10n.es.aeat.mod347.real_estate_record']
    #         for value in vals:
    #             o_action, o_id, o_vals = value
    #             rec = real_estate_record_obj.browse(o_id)
    #             if o_action == 1:
    #                 rec.write(o_vals)
    #             elif o_action == 2:
    #                 rec.unlink()
    #             elif o_action == 0:
    #                 rec.create(o_vals)
    #     return True

    @api.multi
    @api.depends('partner_country_code', 'partner_state_code', 'partner_vat',
                 'community_vat')
    def _compute_check_ok(self):
        for record in self:
            record.check_ok = (
                record.partner_country_code and
                record.partner_state_code and
                record.partner_state_code.isdigit() and
                (record.partner_vat or record.community_vat)
            )

    @api.model
    def _default_record_id(self):
        return self.env.context.get('report_id', False)

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.report', string='AEAT 347 Report',
        ondelete="cascade", select=1, default=_default_record_id)
    operation_key = fields.Selection(
        selection=[('A', 'A - Adquisiciones de bienes y servicios superiores '
                         'al límite (1)'),
                   ('B', 'B - Entregas de bienes y servicios superiores al '
                         'límite (1)'),
                   ('C', 'C - Cobros por cuenta de terceros superiores al '
                         'límite (3)'),
                   ('D', 'D - Adquisiciones efectuadas por Entidades Públicas '
                         '(...) superiores al límite (1)'),
                   ('E', 'E - Subvenciones, auxilios y ayudas satisfechas por '
                         'Ad. Públicas superiores al límite (1)'),
                   ('F', 'F - Ventas agencia viaje'),
                   ('G', 'G - Compras agencia viaje')],
        string='Operation Key')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True)
    partner_vat = fields.Char(string='VAT number', size=9)
    representative_vat = fields.Char(
        string='L.R. VAT number', size=9,
        help="Legal Representative VAT number")
    community_vat = fields.Char(
        string='Community vat number', size=17,
        help="VAT number for professionals established in other state "
             "member without national VAT")
    partner_country_code = fields.Char(string='Country Code', size=2)
    partner_state_code = fields.Char(string='State Code', size=2)
    first_quarter = fields.Float(
        compute="_get_quarter_invoice_totals", store=True, readonly=True,
        string="First quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of first quarter in, out and refund invoices "
             "for this partner")
    manual_first_quarter = fields.Float(
        string="First quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of first quarter in, out and refund invoices "
             "for this partner")
    first_quarter_real_estate_transmission_amount = fields.Float(
        string="First quarter real estate", digits=dp.get_precision('Account'),
        oldname="first_quarter_real_state_transmission_amount",
        help="Total amount of first quarter real estate transmissions "
             "for this partner")
    first_quarter_cash_amount = fields.Float(
        compute="_get_quarter_cash_totals", store=True, readonly=True,
        string="First quarter cash movements",
        digits=dp.get_precision('Account'),
        help="Total amount of first quarter cash movements "
             "for this partner")
    second_quarter = fields.Float(
        compute="_get_quarter_invoice_totals", store=True, readonly=True,
        string="Second quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of second quarter in, out and refund invoices "
             "for this partner")
    manual_second_quarter = fields.Float(
        string="Second quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of second quarter in, out and refund invoices "
             "for this partner")
    second_quarter_real_estate_transmission_amount = fields.Float(
        string="Second quarter real estate",
        digits=dp.get_precision('Account'),
        oldname="second_quarter_real_state_transmission_amount",
        help="Total amount of second quarter real estate transmissions "
             "for this partner")
    second_quarter_cash_amount = fields.Float(
        compute="_get_quarter_cash_totals", store=True, readonly=True,
        string="Second quarter cash movements",
        digits=dp.get_precision('Account'),
        help="Total amount of second quarter cash movements "
             "for this partner")
    third_quarter = fields.Float(
        compute="_get_quarter_invoice_totals", store=True, readonly=True,
        string="Third quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of third quarter in, out and refund invoices "
             "for this partner")
    manual_third_quarter = fields.Float(
        string="Third quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of third quarter in, out and refund invoices "
             "for this partner")
    third_quarter_real_estate_transmission_amount = fields.Float(
        string="Third quarter real estate", digits=dp.get_precision('Account'),
        oldname="third_quarter_real_state_transmission_amount",
        help="Total amount of third quarter real estate transmissions "
             "for this partner")
    third_quarter_cash_amount = fields.Float(
        compute="_get_quarter_cash_totals", store=True, readonly=True,
        string="Third quarter cash movements",
        digits=dp.get_precision('Account'),
        help="Total amount of third quarter cash movements "
             "for this partner")
    fourth_quarter = fields.Float(
        compute="_get_quarter_invoice_totals", store=True, readonly=True,
        string="Fourth quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of fourth quarter in, out and refund invoices "
             "for this partner")
    manual_fourth_quarter = fields.Float(
        string="Fourth quarter operations", digits=dp.get_precision('Account'),
        help="Total amount of fourth quarter in, out and refund invoices "
             "for this partner")
    fourth_quarter_real_estate_transmission_amount = fields.Float(
        string="Fourth quarter real estate",
        digits=dp.get_precision('Account'),
        oldname="fourth_quarter_real_state_transmission_amount",
        help="Total amount of fourth quarter real estate transmissions "
             "for this partner")
    fourth_quarter_cash_amount = fields.Float(
        compute="_get_quarter_cash_totals", store=True, readonly=True,
        string="Fourth quarter cash movements",
        digits=dp.get_precision('Account'),
        help="Total amount of fourth quarter cash movements "
             "for this partner")
    amount = fields.Float(
        compute="_get_quarter_invoice_totals", store=True, readonly=True,
        string='Anual operations amount', digits=dp.get_precision('Account'),
        help="Total amount of fiscal year in, out and refund invoices "
             "for this partner")
    cash_amount = fields.Float(
        compute="_get_quarter_cash_totals", store=True, readonly=True,
        string='Anual cash movements amount',
        digits=dp.get_precision('Account'),
        help="Total amount of fiscal year cash movements "
             "for this partner")
    real_estate_transmissions_amount = fields.Float(
        compute="_get_quarter_real_state_totals", store=True, readonly=True,
        string='Real estate transmisions amount',
        digits=dp.get_precision('Account'),
        oldname='real_state_transmissions_amount',
        help="Total amount of fiscal year real estate transmissions "
             "for this partner")
    insurance_operation = fields.Boolean(
        string='Insurance Operation',
        help="Only for insurance companies. Set to identify insurance "
             "operations aside from the rest.")
    cash_basis_operation = fields.Boolean(
        string='Cash Basis Operation',
        help="Only for cash basis operations. Set to identify cash basis "
             "operations aside from the rest.")
    tax_person_operation = fields.Boolean(
        string='Taxable Person Operation',
        help="Only for taxable person operations. Set to identify taxable "
             "person operations aside from the rest.")
    related_goods_operation = fields.Boolean(
        string='Related Goods Operation',
        help="Only for related goods operations. Set to identify related "
             "goods operations aside from the rest.")
    bussiness_real_estate_rent = fields.Boolean(
        string='Bussiness Real Estate Rent',
        help="Set to identify real estate rent operations aside from the rest."
             " You'll need to fill in the real estate info only when you are "
             "the one that receives the money.",
        oldname='bussiness_real_state_rent')
    origin_fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear', string='Origin fiscal year',
        help="Origin cash operation fiscal year")
    invoice_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.invoice_record',
        inverse_name='partner_record_id', string='Invoice records')
    # TODO: By now user must fill real estate transmission amounts manually
    real_estate_record_ids = fields.One2many(
        compute="_get_real_estate_record_ids",
        # inverse="_set_real_estate_record_ids",
        comodel_name="l10n.es.aeat.mod347.real_estate_record",
        string='Real Estate Records', store=False,
        oldname='real_state_record_ids')
    cash_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.cash_record',
        inverse_name='partner_record_id', string='Payment records')
    automatic = fields.Boolean(
        compute="_compute_automatic", store=True, readonly=True)
    check_ok = fields.Boolean(
        compute="_compute_check_ok", string='Record is OK',
        store=True, readonly=True,
        help='Checked if this record is OK')

    @api.multi
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """Loads some partner data (country, state and vat) when the selected
        partner changes.
        """
        for record in self:
            if record.partner_id:
                record.partner_vat = re.match(
                    r'(ES)?(.*)', record.partner_id.vat or '').groups()[1]
                record.partner_state_code = record.partner_id.state_id.code
                record.partner_country_code = record.partner_id.country_id.code


class L10nEsAeatMod347RealStateRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.real_estate_record'
    _description = 'Real Estate Record'
    _rec_name = "reference"

    @api.model
    def _default_record_id(self):
        return self.env.context.get('report_id', False)

    @api.model
    def _default_partner_id(self):
        return self.env.context.get('partner_id', False)

    @api.model
    def _default_partner_vat(self):
        return self.env.context.get('partner_vat', False)

    @api.model
    def _default_representative_vat(self):
        return self.env.context.get('representative_vat', False)

    @api.multi
    @api.depends('state_code')
    def _compute_check_ok(self):
        for record in self:
            record.check_ok = bool(record.partner_state_code)

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.report', string='AEAT 347 Report',
        ondelete="cascade", select=1, default=_default_record_id)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', required=True,
        default=_default_partner_id)
    partner_vat = fields.Char(
        string='VAT number', size=32, default=_default_partner_vat)
    representative_vat = fields.Char(
        string='L.R. VAT number', size=32, default=_default_representative_vat,
        help="Legal Representative VAT number")
    amount = fields.Float(
        string='Amount', digits=dp.get_precision('Account'), required=True)
    situation = fields.Selection(
        selection=[('1', '1 - Spain but Basque Country and Navarra'),
                   ('2', '2 - Basque Country and Navarra'),
                   ('3', '3 - Spain, without catastral reference'),
                   ('4', '4 - Foreign')],
        string='Real estate Situation', required=True)
    reference = fields.Char(
        string='Catastral Reference', size=25, required=True)
    address_type = fields.Char(
        string='Address type', size=5)
    address = fields.Char(string='Address', size=50)
    number_type = fields.Selection(
        selection=[('NUM', 'Number'),
                   ('KM.', 'Kilometer'),
                   ('S/N', 'Without number')],
        string='Number type')
    number = fields.Integer(string='Number', size=5)
    number_calification = fields.Selection(
        selection=[('BIS', 'Bis'),
                   ('MOD', 'Mod'),
                   ('DUP', 'Dup'),
                   ('ANT', 'Ant')],
        string='Number calification')
    block = fields.Char(string='Block', size=3)
    portal = fields.Char(string='Portal', size=3)
    stairway = fields.Char(string='Stairway', size=3)
    floor = fields.Char(string='Floor', size=3)
    door = fields.Char(string='Door', size=3)
    complement = fields.Char(
        string='Complement', size=40,
        help="Complement (urbanization, industrial park...)")
    city = fields.Char(string='City', size=30)
    township = fields.Char(string='Township', size=30)
    township_code = fields.Char(string='Township Code', size=5)
    state_code = fields.Char(string='State Code', size=2)
    postal_code = fields.Char(string='Postal code', size=5)
    check_ok = fields.Boolean(
        compute="_compute_check_ok", string='Record is OK',
        store=True, readonly=True,
        help='Checked if this record is OK')

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """Loads some partner data (vat) when the selected partner changes."""
        for record in self:
            record.partner_vat = re.match(
                r'(ES)?(.*)', record.partner_id.vat or '').groups()[1]


class L10nEsAeatMod347InvoiceRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.invoice_record'
    _description = 'Invoice Record'
    _order = 'date ASC, invoice_id ASC'

    @api.model
    def _default_partner_record(self):
        return self.env.context.get('partner_record_id', False)

    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        string='Partner record', required=True, ondelete="cascade", select=1,
        default=_default_partner_record)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice', required=True,
        ondelete="cascade")
    invoice_type = fields.Selection(related="invoice_id.type", readonly=True)
    date = fields.Date(
        related='invoice_id.date_invoice', store=True, readonly=True,
        string='Date')
    amount = fields.Float(
        related="invoice_id.amount_total_wo_irpf", store=True, readonly=True,
        digits=dp.get_precision('Account'), string='Amount')


class L10nEsAeatMod347CashRecord(models.Model):
    """Represents a payment record."""
    _name = 'l10n.es.aeat.mod347.cash_record'
    _description = 'Cash Record'
    _order = 'date ASC, move_line_id ASC'

    @api.model
    def _default_partner_record(self):
        return self.env.context.get('partner_record_id', False)

    partner_record_id = fields.Many2one(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        string='Partner record', required=True, ondelete="cascade", select=1,
        default=_default_partner_record)
    move_line_id = fields.Many2one(
        comodel_name='account.move.line', string='Account move line',
        required=True, ondelete="cascade")
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'))
