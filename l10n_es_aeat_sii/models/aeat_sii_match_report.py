# -*- coding: utf-8 -*-
# Copyright 2018 Abraham Anes <abraham@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import json
import copy

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, exceptions, models
from requests import Session

from odoo.modules.registry import RegistryManager

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
    from zeep.helpers import serialize_object
except (ImportError, IOError) as err:
    _logger.debug(err)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory

SII_VERSION = '1.0'


class SiiMatchReport(models.Model):
    _name = "l10n.es.aeat.sii.match.report"
    _description = "AEAT SII match Report"

    def _default_company_id(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get(
            'l10n.es.aeat.sii.match.report')

    name = fields.Char(string='Report identifier', required=True,)
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('calculated', 'Calculated'),
                   ('done', 'Done'),
                   ('error', 'Error'),
                   ('cancelled', 'Cancelled')],
        string='State', default='draft',
    )
    period_type = fields.Selection(
        selection=[('01', '01 - January'),
                   ('02', '02 - February'),
                   ('03', '03 - March'),
                   ('04', '04 - April'),
                   ('05', '05 - May'),
                   ('06', '06 - June'),
                   ('07', '07 - July'),
                   ('08', '08 - August'),
                   ('09', '09 - September'),
                   ('10', '10 - October'),
                   ('11', '11 - November'),
                   ('12', '12 - December')],
        string="Period type", required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    fiscalyear = fields.Integer(
        string='Fiscal year', lenght=4, required=True,
        default=fields.Date.from_string(fields.Date.today()).year,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    company_id = fields.Many2one(
        comodel_name='res.company', default=_default_company_id,
        string='Company', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    calculate_date = fields.Datetime(
        string='Calculate date',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    sii_match_result = fields.One2many(
        comodel_name='l10n.es.aeat.sii.match.result',
        inverse_name='report_id',
        string='SII Match Result',
        readonly=True,
    )
    invoice_type = fields.Selection(
        selection=[('out', 'Out invoice/refund'),
                   ('in', 'In invoice/refund')],
        string='Invoice type', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    number_records = fields.Integer(string='Records', readonly=True, )
    number_records_both = fields.Integer(
        string='Records in Odoo and SII', readonly=True,
    )
    number_records_odoo = fields.Integer(
        string='Records only in Odoo', readonly=True,
    )
    number_records_sii = fields.Integer(
        string='Records only in SII', readonly=True,
    )
    number_records_correct = fields.Integer(
        string='Records corretly contrasted', readonly=True,
    )
    number_records_no_exist = fields.Integer(
        string='Records without contrast', readonly=True,
    )
    number_records_partially = fields.Integer(
        string='Records partially contrasted', readonly=True,
    )
    number_records_no_test = fields.Integer(
        string='Records no testables', readonly=True,
    )
    number_records_in_process = fields.Integer(
        string='Records in process of contrast', readonly=True,
    )
    number_records_not_contrasted = fields.Integer(
        string='Records not contasted', readonly=True,
    )
    number_records_partially_contrasted = fields.Integer(
        string='Records partially contrasted', readonly=True,
    )
    number_records_contrasted = fields.Integer(
        string='Records contrasted', readonly=True,
    )
    sii_match_jobs_ids = fields.Many2many(
        comodel_name='queue.job', column1='sii_match_id', column2='job_id',
        string="Connector Jobs", copy=False,
    )

    @api.multi
    def _process_invoices_from_sii(self):
        queue_obj = self.env['queue.job'].sudo()
        for match_report in self:
            company = match_report.company_id
            new_delay = match_report.sudo().with_context(
                company_id=company.id
            ).with_delay(
                eta=False,
            ).get_invoice_aeat()
            job = queue_obj.search([
                ('uuid', '=', new_delay.uuid)
            ], limit=1)
            match_report.sudo().sii_match_jobs_ids |= job

    @api.multi
    def _get_invoice_dict(self):
        self.ensure_one()
        inv_dict = {
            "FiltroConsulta": {},
            "PeriodoImpositivo": {
                "Ejercicio": str(self.fiscalyear),
                "Periodo": self.period_type,
            },
        }
        return inv_dict

    @api.multi
    def _get_aeat_odoo_invoices_by_csv(self, sii_response):
        matched_invoices = {}
        left_invoices = []
        for invoice in sii_response:
            invoice = json.loads(json.dumps(serialize_object(invoice)))
            csv = invoice['DatosPresentacion']['CSV']
            invoice_state = invoice['EstadoFactura']['EstadoRegistro']
            odoo_invoice = self.env['account.invoice'].search(
                [('sii_csv', '=', csv)])
            if odoo_invoice:
                matched_invoices[odoo_invoice.id] = invoice
            elif invoice_state != 'Anulada':
                left_invoices.append(invoice)
        return matched_invoices, left_invoices

    @api.multi
    def _get_aeat_odoo_invoices_by_num(self, left_invoices, matched_invoices):
        left_results = []
        for invoice in left_invoices:
            name = invoice['IDFactura']['NumSerieFacturaEmisor']
            if self.invoice_type == 'out':
                odoo_invoice = self.env['account.invoice'].search([
                    ('number', '=', name),
                    ('type', 'in', ['out_invoice', 'out_refund'])
                ], limit=1)
            else:
                odoo_invoice = self.env['account.invoice'].search([
                    ('reference', '=', name),
                    ('type', 'in', ['in_invoice', 'in_refund'])
                ], limit=1)
            if odoo_invoice and odoo_invoice.id not in matched_invoices.keys():
                matched_invoices[odoo_invoice.id] = invoice
            else:
                left_results.append(invoice)
        return matched_invoices, left_results

    @api.multi
    def _get_aeat_odoo_invoices(self, sii_response):
        matched_invoices, left_invoices = self._get_aeat_odoo_invoices_by_csv(
            sii_response)
        matched_invoices, left_invoices = self._get_aeat_odoo_invoices_by_num(
            left_invoices, matched_invoices)
        res = []
        invoices_list = {}
        for odoo_inv_id, invoice in matched_invoices.items():
            name = invoice['IDFactura']['NumSerieFacturaEmisor']
            csv = invoice['DatosPresentacion']['CSV']
            match_state = invoice['EstadoFactura']['EstadoCuadre']
            odoo_invoice = self.env['account.invoice'].browse([odoo_inv_id])
            inv_location = 'both'
            contrast_state = 'correct'
            diffs = odoo_invoice._get_diffs_values(invoice)
            if diffs:
                contrast_state = 'partially'
            invoices_list[odoo_invoice.id] = {
                'sii_match_return': json.dumps(str(invoice), indent=4),
                'sii_match_state': match_state,
                'sii_contrast_state': contrast_state,
                'sii_match_differences': copy.deepcopy(diffs),
            }
            res.append({
                'invoice': name,
                'invoice_id': odoo_invoice.id,
                'csv': csv,
                'invoice_location': inv_location,
                'sii_match_differences': diffs,
                'sii_match_state': match_state,
                'sii_contrast_state': contrast_state,
            })
        for invoice in left_invoices:
            name = invoice['IDFactura']['NumSerieFacturaEmisor']
            csv = invoice['DatosPresentacion']['CSV']
            match_state = invoice['EstadoFactura']['EstadoCuadre']
            contrast_state = 'no_exist'
            inv_location = 'sii'
            diffs = []
            res.append({
                'invoice': name,
                'invoice_id': False,
                'csv': csv,
                'invoice_location': inv_location,
                'sii_match_differences': diffs,
                'sii_match_state': match_state,
                'sii_contrast_state': contrast_state,
            })
        return res, invoices_list

    @api.multi
    def _get_not_in_sii_invoices(self, invoices):
        self.ensure_one()
        start_date = fields.Date.from_string(
            '%s-%s-01' % (str(self.fiscalyear), self.period_type))
        date_from = fields.Date.to_string(start_date)
        date_to = fields.Date.to_string(
            start_date + relativedelta(months=1)
        )
        res = []
        inv_type = [
            'out_invoice', 'out_refund'] if self.invoice_type == 'out' else [
            'in_invoice', 'in_refund']
        invoice_ids = self.env['account.invoice'].search([
            ('date', '>=', date_from),
            ('date', '<', date_to),
            ('company_id', '=', self.company_id.id),
            ('id', 'not in', invoices.keys()),
            ('type', 'in', inv_type),
        ])
        for invoice in invoice_ids:
            if invoice.sii_enabled:
                if 'out_invoice' in inv_type:
                    number = invoice.number or _('Draft')
                else:
                    number = invoice.reference
                res.append({
                    'invoice': number,
                    'invoice_id': invoice.id,
                    'sii_contrast_state': 'no_exist',
                    'invoice_location': 'odoo',
                })
        return res

    @api.multi
    def _update_odoo_invoices(self, invoices):
        self.ensure_one()
        for invoice_id, values in invoices.items():
            invoice = self.env['account.invoice'].browse([invoice_id])
            invoice.sii_match_differences.unlink()
            invoice.write(values)
        return []

    @api.multi
    def _get_match_result_values(self, sii_response):
        self.ensure_one()
        vals = []
        invoices, matched_invoices = self._get_aeat_odoo_invoices(sii_response)
        invoices += self._get_not_in_sii_invoices(matched_invoices)
        self._update_odoo_invoices(matched_invoices)
        summary = {
            'total': len(invoices),
            'both': len(
                filter(lambda i: i['invoice_location'] == 'both', invoices)
            ),
            'sii': len(
                filter(lambda i: i['invoice_location'] == 'sii', invoices)
            ),
            'odoo': len(
                filter(lambda i: i['invoice_location'] == 'odoo', invoices)
            ),
            'correct': len(
                filter(
                    lambda i: i['sii_contrast_state'] == 'correct',
                    invoices
                )
            ),
            'no_exist': len(
                filter(
                    lambda i: i['sii_contrast_state'] == 'no_exist',
                    invoices
                )
            ),
            'partially': len(
                filter(
                    lambda i: i['sii_contrast_state'] == 'partially',
                    invoices
                )
            ),
            'no_test': len(
                filter(
                    lambda i: (i.get('sii_match_state', False) and
                               i['sii_match_state'] == '1'),
                    invoices
                )
            ),
            'in_process': len(
                filter(
                    lambda i: (i.get('sii_match_state', False) and
                               i['sii_match_state'] == '2'),
                    invoices
                )
            ),
            'not_contrasted': len(
                filter(
                    lambda i: (i.get('sii_match_state', False) and
                               i['sii_match_state'] == '3'),
                    invoices
                )
            ),
            'partially_contrasted': len(
                filter(
                    lambda i: (i.get('sii_match_state', False) and
                               i['sii_match_state'] == '4'),
                    invoices
                )
            ),
            'contrasted': len(
                filter(
                    lambda i: (i.get('sii_match_state', False)
                               and i['sii_match_state'] == '5'),
                    invoices
                )
            ),
        }
        for l in filter(
            lambda i: (i['sii_contrast_state'] != 'correct'
                       or i['sii_match_state'] == '4'),
            invoices
        ):
            vals.append((0, 0, l))
        return vals, summary

    @api.multi
    def _get_invoices_from_sii(self):
        for sii_match_report in self.filtered(
                lambda r: r.state in ['draft', 'error', 'calculated']):
            company = sii_match_report.company_id
            port_name = ''
            wsdl = ''
            if sii_match_report.invoice_type == 'out':
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_out', False)
                port_name = 'SuministroFactEmitidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            elif sii_match_report.invoice_type == 'in':
                wsdl = self.env['ir.config_parameter'].get_param(
                    'l10n_es_aeat_sii.wsdl_in', False)
                port_name = 'SuministroFactRecibidas'
                if company.sii_test:
                    port_name += 'Pruebas'
            client = self._connect_sii(wsdl)
            serv = client.bind('siiService', port_name)
            header = sii_match_report._get_sii_header()
            match_vals = {}
            summary = {}
            try:
                inv_dict = sii_match_report._get_invoice_dict()
                if sii_match_report.invoice_type == 'out':
                    res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                    res_line = \
                        res['RegistroRespuestaConsultaLRFacturasEmitidas']
                elif sii_match_report.invoice_type == 'in':
                    res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                    res_line = \
                        res['RegistroRespuestaConsultaLRFacturasRecibidas']
                if res_line:
                    match_vals['sii_match_result'], summary = \
                        sii_match_report._get_match_result_values(res_line)
                match_vals['number_records'] = \
                    summary and summary['total'] or 0
                match_vals['number_records_both'] = \
                    summary and summary['both'] or 0
                match_vals['number_records_odoo'] = \
                    summary and summary['odoo'] or 0
                match_vals['number_records_sii'] = \
                    summary and summary['sii'] or 0
                match_vals['number_records_correct'] = \
                    summary and summary['correct'] or 0
                match_vals['number_records_no_exist'] = \
                    summary and summary['no_exist'] or 0
                match_vals['number_records_partially'] = \
                    summary and summary['partially'] or 0
                match_vals['number_records_no_test'] = \
                    summary and summary['no_test'] or 0
                match_vals['number_records_in_process'] = \
                    summary and summary['in_process'] or 0
                match_vals['number_records_not_contrasted'] = \
                    summary and summary['not_contrasted'] or 0
                match_vals['number_records_partially_contrasted'] = \
                    summary and summary['partially_contrasted'] or 0
                match_vals['number_records_contrasted'] = \
                    summary and summary['contrasted']
                sii_match_report.sii_match_result.mapped(
                    'sii_match_differences').unlink()
                sii_match_report.sii_match_result.unlink()
                match_vals['state'] = 'calculated'
                match_vals['calculate_date'] = fields.Datetime.now()
                sii_match_report.write(match_vals)
            except Exception:
                new_cr = RegistryManager.get(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                sii_match_report = env['l10n.es.aeat.sii.match.report'].browse(
                    self.id)
                match_vals.update({
                    'state': 'error',
                })
                sii_match_report.write(match_vals)
                new_cr.commit()
                new_cr.close()
                raise

    @api.multi
    def _get_sii_header(self):
        """Builds SII send header

        :return Dict with header data depending on cancellation
        """
        self.ensure_one()
        company = self.company_id
        if not company.vat:
            raise exceptions.Warning(_(
                "No VAT configured for the company '{}'").format(company.name))
        header = {
            "IDVersionSii": SII_VERSION,
            "Titular": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.vat[2:]}
        }
        return header

    @api.multi
    def _connect_sii(self, wsdl):
        today = fields.Date.today()
        sii_config = self.env['l10n.es.aeat.sii'].search([
            ('company_id', '=', self.company_id.id),
            ('public_key', '!=', False),
            ('private_key', '!=', False),
            '|',
            ('date_start', '=', False),
            ('date_start', '<=', today),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', today),
            ('state', '=', 'active'),
        ], limit=1)
        if sii_config:
            public_crt = sii_config.public_key
            private_key = sii_config.private_key
        else:
            public_crt = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.publicCrt', False)
            private_key = self.env['ir.config_parameter'].get_param(
                'l10n_es_aeat_sii.privateKey', False)
        session = Session()
        session.cert = (public_crt, private_key)
        transport = Transport(session=session)
        history = HistoryPlugin()
        client = Client(wsdl=wsdl, transport=transport, plugins=[history])
        return client

    @api.multi
    def button_calculate(self):
        for match in self:
            for queue in match.mapped('sii_match_jobs_ids'):
                if queue.state in ('pending', 'enqueued', 'failed'):
                    queue.sudo().unlink()
                elif queue.state == 'started':
                    raise exceptions.Warning(_(
                        'You can not calculate at this moment '
                        'because there is a job running!'))
        self._process_invoices_from_sii()
        return []

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancelled'})
        return []

    @api.multi
    def button_recover(self):
        self.write({'state': 'draft'})
        return []

    @api.multi
    def button_confirm(self):
        self.write({'state': 'done'})
        return []

    @api.multi
    def open_result(self):
        self.ensure_one()
        tree_view = self.env.ref(
            'l10n_es_aeat_sii.view_l10n_es_aeat_sii_match_result_tree')
        return {
            'name': _('Results'),
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'l10n.es.aeat.sii.match.result',
            'views': [(tree_view and tree_view.id or False, "tree"),
                      (False, "form")],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.sii_match_result.ids)],
            'context': {},
        }

    @job(default_channel='root.invoice_validate_sii')
    @api.multi
    def get_invoice_aeat(self):
        self._get_invoices_from_sii()


class SiiMatchResult(models.Model):
    _name = 'l10n.es.aeat.sii.match.result'
    _description = 'AEAT SII Match - Result'
    _order = 'invoice asc'

    report_id = fields.Many2one(
        comodel_name='l10n.es.aeat.sii.match.report',
        string='AEAT SII Match Report ID',
        ondelete="cascade"
    )
    invoice = fields.Char(string='Invoice')
    invoice_id = fields.Many2one(
        string='Odoo invoice',
        comodel_name='account.invoice'
    )
    csv = fields.Char(string='CSV')
    sii_match_state = fields.Selection(
        string="Match state",
        readonly=True, copy=False,
        selection=[
            ('1', 'No testable'),
            ('2', 'In process of contrast'),
            ('3', 'Not contrasted'),
            ('4', 'Partially contrasted'),
            ('5', 'Contrasted'),
        ],
    )
    sii_contrast_state = fields.Selection(
        string="AEAT contrast state",
        readonly=True, copy=False,
        selection=[
            ('correct', 'Correct'),
            ('no_exist', 'Doesn\'t exist'),
            ('partially', 'Partially correct'),
        ],
    )
    invoice_location = fields.Selection(
        string="Invoice location",
        readonly=True, copy=False,
        selection=[
            ('both', 'Invoice in Odoo and SII'),
            ('odoo', 'Invoice in Odoo'),
            ('sii', 'Invoice in SII'),
        ],
    )
    sii_match_differences = fields.One2many(
        string="SII match differences",
        readonly=True, copy=False,
        comodel_name='l10n.es.aeat.sii.match.differences',
        inverse_name='report_id',
    )
