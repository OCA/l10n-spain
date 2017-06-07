# -*- coding: utf-8 -*-
# Copyright 2011 Ting
# Copyright 2011 2011 NaN Projectes de Programari Lliure, S.L.
# Copyright 2011-2013 Acysos S.L. - Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Tecnativa - Pedro M. Baeza

from openerp import _, api, models
from openerp import fields as new_fields
from openerp.osv import fields, orm


class L10nEsAeatMod340Report(orm.Model):
    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.aeat.mod340.report'
    _period_quarterly = False
    _period_monthly = True
    _period_yearly = True
    _description = 'Model 340'

    def button_calculate(self, cr, uid, ids, args, context=None):
        self.pool['l10n.es.aeat.mod340.calculate_records']._calculate_records(
            cr, uid, ids[0], context,
        )
        return True

    def button_recalculate(self, cr, uid, ids, context=None):
        self.pool['l10n.es.aeat.mod340.calculate_records']._calculate_records(
            cr, uid, ids[0], context,
        )
        return True

    # def _name_get(self, cr, uid, ids, field_name, arg, context=None):
    #     """Returns the report name"""
    #     result = {}
    #     for report in self.browse(cr, uid, ids, context=context):
    #         result[report.id] = report.number
    #     return result

    def _get_number_records(self, cr, uid, ids, field_name, args, context):
        result = {}
        for id in ids:
            result[id] = {}.fromkeys(['number_records', 'total_taxable',
                                      'total_sharetax', 'total',
                                      'total_taxable_rec',
                                      'total_sharetax_rec', 'total_rec'],
                                     0.0)
        for model in self.browse(cr, uid, ids, context):
            for issue in model.issued:
                result[model.id]['number_records'] += len(issue.tax_line_ids)
                result[model.id]['total_taxable'] += issue.base_tax
                result[model.id]['total_sharetax'] += issue.amount_tax + \
                    issue.rec_amount_tax
                result[model.id]['total'] += issue.base_tax + \
                    issue.amount_tax + issue.rec_amount_tax
            for issue in model.received:
                result[model.id]['number_records'] += len(issue.tax_line_ids)
                result[model.id]['total_taxable_rec'] += issue.base_tax
                result[model.id]['total_sharetax_rec'] += issue.amount_tax
                result[model.id]['total_rec'] += issue.base_tax
                result[model.id]['total_rec'] += issue.amount_tax
        return result

    _columns = {
        # 'name': fields.function(_name_get, method=True, type="char",
        #                         size=64, string="Name"),

        'issued': fields.one2many('l10n.es.aeat.mod340.issued', 'mod340_id',
                                  'Invoices Issued',
                                  states={'done': [('readonly', True)]}),
        'summary_issued': fields.one2many(
            'l10n.es.aeat.mod340.tax_summary',
            'mod340_id', 'Summary Invoices Issued',
            domain=[('summary_type', '=', 'issued')],
            states={'done': [('readonly', True)]}),
        'received': fields.one2many('l10n.es.aeat.mod340.received',
                                    'mod340_id', 'Invoices Received',
                                    states={'done': [('readonly', True)]}),
        'summary_received': fields.one2many(
            'l10n.es.aeat.mod340.tax_summary',
            'mod340_id',
            'Summary Invoices Received',
            domain=[('summary_type', '=', 'received')],
            states={'done': [('readonly', True)]}),
        'investment': fields.one2many('l10n.es.aeat.mod340.investment',
                                      'mod340_id', 'Property Investment'),
        'intracomunitarias': fields.one2many(
            'l10n.es.aeat.mod340.intracomunitarias',
            'mod340_id', 'Operations Intracomunitarias'),
        'ean13': fields.char('Electronic Code VAT reverse charge', size=16),
        'total_taxable': fields.function(
            _get_number_records, method=True,
            type='float', string='Total Taxable', multi='recalc'),
        'total_sharetax': fields.function(
            _get_number_records, method=True,
            type='float', string='Total Share Tax', multi='recalc'),
        'number_records': fields.function(
            _get_number_records, method=True,
            type='integer', string='Records', multi='recalc'),
        'total': fields.function(
            _get_number_records, method=True,
            type='float', string="Total", multi='recalc'),
        'total_taxable_rec': fields.function(
            _get_number_records, method=True,
            type='float', string='Total Taxable', multi='recalc'),
        'total_sharetax_rec': fields.function(
            _get_number_records, method=True,
            type='float', string='Total Share Tax', multi='recalc'),
        'total_rec': fields.function(
            _get_number_records, method=True,
            type='float', string="Total", multi='recalc'),
        'calculation_date': fields.date('Calculation date', readonly=True),
    }

    _defaults = {
        'number': '340',
    }

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            fy = self.env['account.fiscalyear'].browse(
                vals['fiscalyear_id'])[0]
            period = vals['period_type']
            if vals['period_type'] == '0A':
                period = '00'

            vals['name'] = '340' + fy.name + period + self.\
                _report_identifier_get(vals)
        return super(L10nEsAeatMod340Report, self).create(vals)

    def __init__(self, pool, cr):
        self._aeat_number = '340'
        super(L10nEsAeatMod340Report, self).__init__(pool, cr)


class L10nEsAeatMod340Issued(orm.Model):
    _name = 'l10n.es.aeat.mod340.issued'
    _description = 'Invoices invoice'
    _columns = {
        'mod340_id': fields.many2one('l10n.es.aeat.mod340.report', 'Model 340',
                                     ondelete="cascade"),
        'partner_id': fields.many2one('res.partner', 'Partner',
                                      ondelete="cascade"),
        'partner_vat': fields.char('Company CIF/NIF', size=17),
        'representative_vat': fields.char(
            'L.R. VAT number', size=9, help="Legal Representative VAT number"),
        'partner_country_code': fields.char('Country Code', size=2),
        'invoice_id': fields.many2one('account.invoice', 'Invoice',
                                      ondelete="cascade"),
        'base_tax': fields.float('Base tax bill', digits=(13, 2)),
        'amount_tax': fields.float('Total tax', digits=(13, 2)),
        'rec_amount_tax': fields.float('Tax surcharge amount', digits=(13, 2)),
        'total': fields.float('Total', digits=(13, 2)),
        'key_operation': fields.char('Key operation', size=12),
        'vat_type': fields.char('Vat type', size=12),
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_issued',
                                        'invoice_record_id', 'Tax lines'),
        'date_invoice': fields.date('Date Invoice', readonly=True),
        'txt_exception': fields.char('Exception', size=256),
        'exception': fields.boolean('Exception'),
        'date_payment': fields.date('Date Payment', readonly=True),
        'payment_amount': fields.float('Payment amount', digits=(13, 2)),
        'name_payment_method': fields.char('Method Payment', size=34),
        'record_number': fields.char(string='Record number', readonly=True)
    }

    _order = 'date_invoice asc, invoice_id asc'


class L10nEsAeatMod340Received(orm.Model):
    _name = 'l10n.es.aeat.mod340.received'
    _description = 'Invoices Received'
    _inherit = 'l10n.es.aeat.mod340.issued'
    _columns = {
        'supplier_invoice_number': fields.char(
            'Supplier invoice number', size=128),
        'tax_line_ids': fields.one2many(
            'l10n.es.aeat.mod340.tax_line_received', 'invoice_record_id',
            'Tax lines'),
    }


class L10nEsAeatMod340Investment(orm.Model):
    _name = 'l10n.es.aeat.mod340.investment'
    _description = 'Property Investment'
    _inherit = 'l10n.es.aeat.mod340.issued'


class L10nEsAeatMod340Intracomunitarias(orm.Model):
    _name = 'l10n.es.aeat.mod340.intracomunitarias'
    _description = 'Operations Intracomunitarias'
    _inherit = 'l10n.es.aeat.mod340.issued'


class L10nEsAeatMod340TaxLineIssued(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_issued'
    _description = 'Mod340 vat lines issued'
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True),
        'tax_percentage': fields.float('Tax percentage', digits=(0, 4)),
        'tax_amount': fields.float('Tax amount', digits=(13, 2)),
        'base_amount': fields.float('Base tax bill', digits=(13, 2)),
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.issued',
                                             'Invoice issued', required=True,
                                             ondelete="cascade", select=1),
        'tax_code_id': fields.many2one(
            'account.tax.code',
            'Account Tax Code', required=True,
            ondelete="cascade", select=1),
        'rec_tax_percentage': fields.float('Tax surcharge percentage',
                                           digits=(0, 4)),
        'rec_tax_amount': fields.float('Tax surcharge amount', digits=(13, 2)),
    }


class L10nEsAeatMod340TaxLineReceived(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_received'
    _description = 'Mod340 vat lines received'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'
    _columns = {
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.received',
                                             'Invoice received', required=True,
                                             ondelete="cascade", select=1),
    }


class L10nEsAeatMod340TaxSummary(models.Model):
    _name = 'l10n.es.aeat.mod340.tax_summary'
    _description = 'Mod340 vat tax summary'

    tax_code_id = new_fields.Many2one(
        comodel_name='account.tax.code', string='Account Tax Code',
        required=True, ondelete="cascade", index=1,
    )
    sum_tax_amount = new_fields.Float(
        string='Summary tax amount', digits=(13, 2),
    )
    sum_base_amount = new_fields.Float(
        string='Summary base amount', digits=(13, 2),
    )
    tax_percent = new_fields.Float('Tax percent', digits=(13, 4))
    mod340_id = new_fields.Many2one(
        comodel_name='l10n.es.aeat.mod340.report', string='Model 340',
        ondelete="cascade",
    )
    issue_ids = new_fields.Many2many(
        comodel_name='l10n.es.aeat.mod340.issued', id1='mod340_id',
        id2='issue_id', rel='l10n_es_aeat_mod340_summary_issue_rel',
    )
    received_ids = new_fields.Many2many(
        comodel_name='l10n.es.aeat.mod340.received', id1='mod340_id',
        id2='received_id', rel='l10n_es_aeat_mod340_summary_received_rel',
    )
    summary_type = new_fields.Selection(
        selection=[
            ('issued', 'Issued'),
            ('received', 'Received')
        ], oldname='type',
    )

    @api.multi
    def show_records(self):
        self.ensure_one()
        res = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
        }
        if self.summary_type == 'issued':
            res['name'] = _('Issued invoices')
            res['res_model'] = 'l10n.es.aeat.mod340.issued'
            res['domain'] = [('id', 'in', self.issue_ids.ids)]
        elif self.summary_type == 'received':
            res['name'] = _('Received invoices')
            res['res_model'] = 'l10n.es.aeat.mod340.received'
            res['domain'] = [('id', 'in', self.received_ids.ids)]
        return res
