# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models, api, exceptions, _

import re
from datetime import datetime
from calendar import monthrange
from openerp.addons.decimal_precision import decimal_precision as dp


class L10nEsAeatMod347Report(models.Model):
    _inherit = "l10n.es.aeat.report"
    _name = "l10n.es.aeat.mod347.report"
    _description = "AEAT 347 Report"

    def _get_export_conf(self):
        try:
            return self.env.ref(
                'l10n_es_aeat_mod347.aeat_mod347_main_export_config').id
        except ValueError:
            return self.env['aeat.model.export.config']

    @api.multi
    def btn_list_records(self):
        return {
            'domain': "[('report_id','in'," + str(self.ids) + ")]",
            'name': _("Partner records"),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'l10n.es.aeat.mod347.partner_record',
            'type': 'ir.actions.act_window',
        }

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

    @api.multi
    def _calculate_partner_records(self, partners, date_start, date_end):
        """Search for invoices for the given partners, and check if exceeds
        the limit. If so, it creates the partner record."""
        self.ensure_one()
        invoice_obj = self.env['account.invoice']
        partner_record_obj = self.env['l10n.es.aeat.mod347.partner_record']
        receivable_partner_record_id = False
        # We will repeat the process for sales and purchases:
        for invoice_type, refund_type in zip(('out_invoice', 'in_invoice'),
                                             ('out_refund', 'in_refund')):
            # CHECK THE SALE/PURCHASES INVOICE LIMIT
            # (A and B operation keys)
            # Search for invoices to this partner (with account moves).
            invoices = invoice_obj.search(
                [('partner_id', 'child_of', partners.ids),
                 ('type', '=', invoice_type),
                 ('date', '>=', date_start),
                 ('date', '<=', date_end),
                 ('state', 'not in', ['draft', 'cancel']),
                 ('not_in_mod347', '=', False)])
            refunds = invoice_obj.search(
                [('partner_id', 'child_of', partners.ids),
                 ('type', '=', refund_type),
                 ('date', '>=', date_start),
                 ('date', '<=', date_end),
                 ('state', 'not in', ['draft', 'cancel']),
                 ('not_in_mod347', '=', False)])
            # Calculate the invoiced amount
            # Remove IRPF tax for invoice amount
            invoice_amount = sum(x.amount_total_wo_irpf for x in invoices)
            refund_amount = sum(x.amount_total_wo_irpf for x in refunds)
            total_amount = invoice_amount - refund_amount
            # If the invoiced amount is greater than the limit
            # we will add a partner record to the report.
            if abs(total_amount) > self.operations_limit:
                if invoice_type == 'out_invoice':
                    operation_key = 'B'  # Note: B = Sale operations
                else:
                    assert invoice_type == 'in_invoice'
                    operation_key = 'A'  # Note: A = Purchase operations
                address = self._get_default_address(partners[0])
                # Get the partner data
                if partners.vat:
                    partner_country_code, partner_vat = (
                        re.match(r"([A-Z]{0,2})(.*)", partners.vat).groups())
                else:
                    partner_vat = ''
                    partner_country_code = address.country_id.code
                # Create the partner record
                partner_record_id = partner_record_obj.create(
                    {'report_id': self.id,
                     'operation_key': operation_key,
                     'partner_id': partners[0].id,
                     'partner_vat': partner_vat,
                     'representative_vat': '',
                     'partner_state_code': address.state_id.code,
                     'partner_country_code': partner_country_code,
                     'invoice_record_ids': [(0, 0, {'invoice_id': x})
                                            for x in (invoices.ids +
                                                      refunds.ids)],
                     'amount': total_amount})
                if invoice_type == 'out_invoice':
                    receivable_partner_record_id = partner_record_id
        return receivable_partner_record_id

    @api.multi
    def _calculate_cash_records(
            self, partners, partner_record_id, date_start, date_end):
        """Search for payments received in cash from the given partners.
        @param partner: Partner for generating cash records.
        @param partner_ids: List of ids that corresponds to the same partner.
        @param partner_record_id: Possible previously created 347 record for
            the same partner.
        """
        self.ensure_one()
        partner_record_obj = self.env['l10n.es.aeat.mod347.partner_record']
        cash_record_obj = self.env['l10n.es.aeat.mod347.cash_record']
        move_line_obj = self.env['account.move.line']
        # Get the cash journals (moves on these journals are considered cash)
        cash_journals = self.env['account.journal'].search(
            [('type', '=', 'cash')])
        if not cash_journals:
            return
        receivable_ids = [
            x.property_account_receivable_id.id for x in partners]
        cash_account_move_lines = move_line_obj.search(
            [('partner_id', 'child_of', partners.ids),
             ('account_id', 'in', receivable_ids),
             ('journal_id', 'in', cash_journals.ids),
             ('date', '>=', date_start),
             ('date', '<=', date_end),
             ])
        # Calculate the cash amount in report fiscalyear
        received_cash_amount = sum([line.credit for line in
                                    cash_account_move_lines])
        # Add the cash detail to the partner cash_move_year if over limit
        if received_cash_amount > self.received_cash_limit:
            address = self._get_default_address(partners[0])
            # Get the partner data
            if partners.vat:
                partner_country_code, partner_vat = (
                    re.match(r"([A-Z]{0,2})(.*)", partners.vat).groups())
            else:
                partner_vat = ''
                partner_country_code = address.country_id.code
            cash_moves = {}
            # Group cash move lines by origin operation fiscalyear
            for move_line in cash_account_move_lines:
                # FIXME: ugly group by reconciliation invoices, because there
                # isn't any direct relationship between payments and invoice
                invoices = []
                if move_line.reconcile_id:
                    for line in move_line.reconcile_id.line_id:
                        if line.invoice:
                            invoices.append(line.invoice)
                elif move_line.reconcile_partial_id:
                    line_ids = move_line.reconcile_partial_id.line_partial_ids
                    for line in line_ids:
                        if line.invoice:
                            invoices.append(line.invoice)
                invoices = list(set(invoices))
                if invoices:
                    invoice = invoices[0]

                    cash_move_year = fields.Date.from_string(
                        invoice.date).strftime("%Y")

                    if cash_move_year not in cash_moves:
                        cash_moves[cash_move_year] = [move_line]
                    else:
                        cash_moves[cash_move_year].append(move_line)
            for cash_move_year in cash_moves.keys():
                receivable_amount = sum([line.credit for line in
                                         cash_moves[cash_move_year]])
                if receivable_amount > self.received_cash_limit:
                    if (cash_move_year != self.year or
                            not partner_record_id):
                        # create partner cash_move_year for cash operation in
                        # different year to currently
                        cash_partner_record_id = partner_record_obj.create(
                            {'report_id': self.id,
                             'operation_key': 'B',
                             'partner_id': partners[0].id,
                             'partner_vat': partner_vat,
                             'representative_vat': '',
                             'partner_state_code': address.state_id.code,
                             'partner_country_code': partner_country_code,
                             'amount': 0.0,
                             'cash_amount': sum([line.credit for line in
                                                 cash_moves[cash_move_year]]),
                             'origin_year': int(cash_move_year)}
                        )
                    else:
                        partner_record_obj.write(
                            partner_record_id,
                            {'cash_amount': sum([line.credit for line in
                                                 cash_account_move_lines]),
                             'origin_year': int(cash_move_year)
                             })
                    cash_partner_record_id = partner_record_id
                    for line in cash_account_move_lines:
                        cash_record_obj.create(
                            {'partner_record_id': cash_partner_record_id,
                             'move_line_id': line.id,
                             'date': line.date,
                             'amount': line.credit})

    @api.multi
    def calculate(self):
        partner_obj = self.env['res.partner']
        for report in self:
            # Delete previous partner records
            report.partner_record_ids.unlink()
            # Get the fiscal year period ids of the non-special periods
            # (to ignore closing/opening entries)

            # We will check every partner with not_in_mod347 flag unchecked
            visited_partners = self.env['res.partner']
            domain = [('not_in_mod347', '=', False),
                      ('parent_id', '=', False)]
            if report.only_supplier:
                domain.append(('supplier', '=', True))
            else:
                domain.extend(['|',
                               ('customer', '=', True),
                               ('supplier', '=', True)])
            for partner in partner_obj.search(domain):
                if partner not in visited_partners:
                    if partner.vat and report.group_by_vat:
                        domain_group = list(domain)
                        domain_group.append(('vat', '=', partner.vat))
                        partners_grouped = partner_obj.search(
                            domain_group)
                    else:
                        partners_grouped = partner
                    visited_partners |= partners_grouped
                    partner_record_id = report._calculate_partner_records(
                        partners_grouped, report.date_start, report.date_end)
                    if partner.customer:
                        report._calculate_cash_records(
                            partners_grouped, partner_record_id,
                            report.date_start, report.date_end)
        return True

    @api.one
    @api.depends('partner_record_ids', 'real_estate_record_ids')
    def _get_totals(self):
        """Calculates the total_* fields from the line values."""
        self.total_partner_records = len(self.partner_record_ids)
        self.total_amount = sum([x.amount for x in
                                 self.partner_record_ids])
        self.total_cash_amount = sum([x.cash_amount for x in
                                      self.partner_record_ids])
        self.total_real_estate_transmissions_amount = (
            sum([x.real_estate_transmissions_amount for x in
                 self.partner_record_ids]))
        self.total_real_estate_amount = sum([x.amount for x in
                                             self.real_estate_record_ids])
        self.total_real_estate_records = len(self.real_estate_record_ids)

    export_config_id = fields.Many2one(
        comodel_name='aeat.model.export.config', oldname='export_config',
        string="Export configuration", default=_get_export_conf)
    number = fields.Char(default='347')
    group_by_vat = fields.Boolean(
        string='Group by VAT number', oldname='group_by_cif')
    only_supplier = fields.Boolean(string='Only Suppliers')
    operations_limit = fields.Float(
        string='Invoiced Limit (1)', digits=(13, 2), default=3005.06,
        help="The declaration will include partners with the total of "
             "operations over this limit")
    received_cash_limit = fields.Float(
        string='Received cash Limit (2)', digits=(13, 2), default=6000.00,
        help="The declaration will show the total of cash operations over "
             "this limit")
    charges_obtp_limit = fields.Float(
        string='Charges on behalf of third parties Limit (3)', digits=(13, 2),
        help="The declaration will include partners from which we received "
             "payments, on behalf of third parties, over this limit",
        default=300.51)
    total_partner_records = fields.Integer(
        compute="_get_totals", string="Partners records")
    total_amount = fields.Float(
        compute="_get_totals", string="Amount")
    total_cash_amount = fields.Float(
        compute="_get_totals", string="Cash Amount")
    total_real_estate_transmissions_amount = fields.Float(
        compute="_get_totals", string="Real Estate Transmissions Amount",
        oldname='total_real_state_transmissions_amount')
    total_real_estate_records = fields.Integer(
        compute="_get_totals", string="Real estate records",
        oldname='total_real_state_records')
    total_real_estate_amount = fields.Float(
        compute="_get_totals", string="Real Estate Amount",
        oldname='total_real_state_amount')
    partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        inverse_name='report_id', string='Partner Records')
    real_estate_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.real_estate_record',
        inverse_name='report_id', string='Real Estate Records',
        oldname='real_state_record_ids')

    @api.multi
    def button_confirm(self):
        """Different check out in report"""
        for item in self:
            # Browse partner record lines to check if all are correct (all
            # fields filled)
            for partner_record in item.partner_record_ids:
                if not partner_record.partner_state_code:
                    raise exceptions.ValidationError(
                        _("All partner state code field must be filled.\n"
                          "Partner: %s (%s)") %
                        (partner_record.partner_id.name,
                         partner_record.partner_id.id))
                if (not partner_record.partner_vat and
                        not partner_record.community_vat):
                    raise exceptions.ValidationError(
                        _("All partner vat number field must be filled.\n"
                          "Partner: %s (%s)") %
                        (partner_record.partner_id.name,
                         partner_record.partner_id.id))
                if (partner_record.partner_state_code and
                        not partner_record.partner_state_code.isdigit()):
                    raise exceptions.ValidationError(
                        _("All partner state code field must be numeric.\n"
                          "Partner: %s (%s)") %
                        (partner_record.partner_id.name,
                         partner_record.partner_id.id))
            for real_estate_record in item.real_estate_record_ids:
                if not real_estate_record.state_code:
                    raise exceptions.ValidationError(
                        _("All real estate records state code field must be "
                          "filled."))
        return super(L10nEsAeatMod347Report, self).button_confirm()

    def __init__(self, pool, cr):
        self._aeat_number = '347'
        super(L10nEsAeatMod347Report, self).__init__(pool, cr)


class L10nEsAeatMod347PartnerRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.partner_record'
    _description = 'Partner Record'
    _rec_name = "partner_vat"

    @api.one
    @api.depends('invoice_record_ids.invoice_id.date', 'report_id.year')
    def _get_quarter_totals(self):
        year = int(self.report_id.year)

        def calc_amount_by_quarter(invoices, refunds, year, quarter):
            if quarter == 'first':
                month_start = 1
            elif quarter == 'second':
                month_start = 4
            elif quarter == 'third':
                month_start = 7
            elif quarter == 'fourth':
                month_start = 10

            day_start = 1
            month_end = month_start + 2
            day_end = monthrange(year, month_end)[1]

            date_start = fields.Date.to_string(
                datetime(year, month_start, day_start))
            date_end = fields.Date.to_string(
                datetime(year, month_end, day_end))
            amount = (
                sum(x.amount for x in invoices
                    if (x.invoice_id.date >= date_start and
                        x.invoice_id.date <= date_end)) -
                sum(x.amount for x in refunds
                    if (x.invoice_id.date >= date_start and
                        x.invoice_id.date <= date_end)))
            return amount

        invoices = self.invoice_record_ids.filtered(
            lambda rec: rec.invoice_id.type in ('out_invoice', 'in_invoice'))
        refunds = self.invoice_record_ids.filtered(
            lambda rec: rec.invoice_id.type in ('out_refund', 'in_refund'))
        self.first_quarter = calc_amount_by_quarter(
            invoices, refunds, year, 'first')
        self.second_quarter = calc_amount_by_quarter(
            invoices, refunds, year, 'second')
        self.third_quarter = calc_amount_by_quarter(
            invoices, refunds, year, 'third')
        self.fourth_quarter = calc_amount_by_quarter(
            invoices, refunds, year, 'fourth')

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

    @api.one
    def _set_real_estate_record_ids(self, vals):
        """Set the real estate records from this record parent report for this
        partner.
        """
        if vals:
            real_estate_record_obj = self.env[
                'l10n.es.aeat.mod347.real_estate_record']
            for value in vals:
                o_action, o_id, o_vals = value
                rec = real_estate_record_obj.browse(o_id)
                if o_action == 1:
                    rec.write(o_vals)
                elif o_action == 2:
                    rec.unlink()
                elif o_action == 0:
                    rec.create(o_vals)
        return True

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
        string='Operations amount', digits=(13, 2))
    cash_amount = fields.Float(
        string='Received cash amount', digits=(13, 2))
    real_estate_transmissions_amount = fields.Float(
        string='Real Estate Transmisions amount', digits=(13, 2),
        oldname='real_state_transmissions_amount')
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
    origin_year = fields.Integer(
        string='Origin year',
        help="Origin cash operation year")
    invoice_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.invoice_record',
        inverse_name='partner_record_id', string='Invoice records')
    real_estate_record_ids = fields.One2many(
        compute="_get_real_estate_record_ids",
        # inverse="_set_real_estate_record_ids",
        comodel_name="l10n.es.aeat.mod347.real_estate_record",
        string='Real Estate Records', store=False,
        oldname='real_state_record_ids')
    cash_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.cash_record',
        inverse_name='partner_record_id', string='Payment records')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Loads some partner data (country, state and vat) when the selected
        partner changes.
        """
        if self.partner_id:
            addr = self.partner_id.address_get(['delivery', 'invoice'])
            # Get the invoice or the default address of the partner
            addr = self.partner_id.address_get(['invoice', 'default'])
            address = self.env['res.partner'].browse(addr['invoice'])
            self.partner_vat = self.partner_id.vat and \
                re.match("(ES){0,1}(.*)",
                         self.partner_id.vat).groups()[1]
            self.partner_state_code = address.state_id.code
            self.partner_country_code = address.country_id.code
        else:
            self.partner_vat = ''
            self.partner_country_code = ''
            self.partner_state_code = ''


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
    amount = fields.Float(string='Amount', digits=(13, 2))
    situation = fields.Selection(
        selection=[('1', '1 - Spain but Basque Country and Navarra'),
                   ('2', '2 - Basque Country and Navarra'),
                   ('3', '3 - Spain, without catastral reference'),
                   ('4', '4 - Foreign')],
        string='Real estate Situation')
    reference = fields.Char(
        string='Catastral Reference', size=25)
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

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        """Loads some partner data (vat) when the selected partner changes."""
        if self.partner_id:
            self.partner_vat = re.match("(ES){0,1}(.*)",
                                        self.partner_id.vat).groups()[1]
        else:
            self.partner_vat = ''


class L10nEsAeatMod347InvoiceRecord(models.Model):
    _name = 'l10n.es.aeat.mod347.invoice_record'
    _description = 'Invoice Record'

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
    date = fields.Date(
        string='Date', related='invoice_id.date_invoice', store=True)
    amount = fields.Float(
        string='Amount', related="invoice_id.amount_total_wo_irpf", store=True)


class L10nEsAeatMod347CashRecord(models.Model):
    """Represents a payment record."""
    _name = 'l10n.es.aeat.mod347.cash_record'
    _description = 'Cash Record'

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
    amount = fields.Float(string='Amount')
