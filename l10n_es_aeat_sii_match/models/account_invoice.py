# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import json

from odoo import _, api, fields, exceptions, models
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)
try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory

try:
    from deepdiff import DeepDiff
except ImportError:
    DeepDiff = object

try:
    from zeep.helpers import serialize_object
except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sii_match_sent = fields.Text(
        string="SII match sent", copy=False, readonly=True,
    )
    sii_match_return = fields.Text(
        string="SII match return", copy=False, readonly=True,
    )
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
        help='- No testable: The counterpart is not suscribed to SII '
             'the record will not be contrasted.\n'
             '- In process of contrast: AEAT is processing the data '
             'soon will be a result.\n'
             '- Not contrasted: The counterpart '
             'has not sent the invoice to SII, '
             'AEAT gives up to 4 months in order '
             'to contrast the information.\n'
             '- Partially contrasted: A invoice has been found '
             'but some data is different.\n'
             '- Contrasted: The counterpart has send '
             'the invoice to SII, all is OK.'
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
    sii_match_difference_ids = fields.One2many(
        string="SII match differences",
        readonly=True, copy=False,
        comodel_name='l10n.es.aeat.sii.match.difference',
        inverse_name='invoice_id',
    )

    @api.multi
    def _get_diffs(self, odoo_values, sii_values):
        sii_values = json.loads(json.dumps((serialize_object(sii_values))))
        dp = self.env['decimal.precision'].precision_get('Account')
        res = []
        if not DeepDiff:
            raise exceptions.Warning(_(
                "You have not installed deepdiff library, "
                "please install it in order to use this feature"
            ))
        diff = DeepDiff(odoo_values, sii_values)
        differences = diff.get('type_changes', {})
        differences.update(diff.get('values_changed', {}))
        for label, value in list(differences.items()):
            sii_value = value['new_value']
            odoo_value = value['old_value']
            label = label.split("['")[-1].replace("']", "")
            if sii_value is not None:
                # We made an explicit case for TipoImpositivo because we get
                # always 2 numbers as strings, one with decimal point separator
                # and another without
                if label == 'TipoImpositivo' or isinstance(odoo_value, float):
                    sii_value = round(float(sii_value), dp)
                    odoo_value = round(float(odoo_value), dp)
                elif isinstance(odoo_value, str):
                    sii_value = sii_value.strip()
                    odoo_value = odoo_value.strip()
                if sii_value != odoo_value:
                    res.append({
                        'sii_field': label,
                        'sii_return_field_value': sii_value,
                        'sii_sent_field_value': odoo_value,
                    })
        return res

    @api.multi
    def _get_diffs_values(self, sii_values):
        self.ensure_one()
        res = []
        if self.sii_content_sent:
            odoo_values = json.loads(self.sii_content_sent)
            if self.type in ['out_invoice', 'out_refund']:
                res += self._get_diffs(odoo_values['FacturaExpedida'],
                                       sii_values['DatosFacturaEmitida'])
            elif self.type in ['in_invoice', 'in_refund']:
                res += self._get_diffs(odoo_values['FacturaRecibida'],
                                       sii_values['DatosFacturaRecibida'])
        return list((0, 0, r) for r in res)

    @api.multi
    def _invoice_started_jobs(self):
        for queue in self.mapped('invoice_jobs_ids'):
            if queue.state == 'started':
                return False
        return True

    @api.multi
    def _process_invoice_for_contrast_aeat(self):
        """Process invoices for contrast to the AEAT. Adds general checks from
        configuration parameters and invoice availability for SII"""
        queue_obj = self.env['queue.job'].sudo()
        for invoice in self:
            company = invoice.company_id
            new_delay = invoice.sudo().with_context(
                company_id=company.id
            ).with_delay(
                eta=False,
            ).contrast_one_invoice()
            jb = queue_obj.search([
                ('uuid', '=', new_delay.uuid)
            ], limit=1)
            invoice.sudo().invoice_jobs_ids |= jb

    @api.multi
    def contrast_aeat(self):
        invoices = self.filtered(
            lambda i: (
                i.sii_state == 'sent' and
                i.state in ['open', 'paid'] and
                i.sii_csv and
                i.sii_enabled
            )
        )
        if not invoices._invoice_started_jobs():
            raise exceptions.Warning(_(
                'You can not contrast this invoice at this moment '
                'because there is a job running'))
        invoices._process_invoice_for_contrast_aeat()

    @api.multi
    def direct_contrast_aeat(self):
        self.ensure_one()
        if not self._invoice_started_jobs():
            raise exceptions.Warning(_(
                'You can not contrast this invoice at this moment '
                'because there is a job running'))
        if (self.sii_csv and self.sii_enabled and self.sii_state == 'sent' and
                self.state in ['open', 'paid']):
            self._contrast_invoice_to_aeat()
        else:
            raise Warning(_(
                'Las facturas tienen que estar enviadas y con CSV para poder '
                'ser contrastadas.'
            ))

    @api.multi
    def _get_contrast_invoice_dict_out(self):
        """Build dict with data to send to AEAT WS for invoice types:
        out_invoice and out_refund.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.date_invoice)
        partner = self.partner_id.commercial_partner_id
        company = self.company_id
        ejercicio = fields.Date.from_string(self.date).year
        periodo = '%02d' % fields.Date.from_string(self.date).month
        inv_dict = {
            "FiltroConsulta": {},
            "PeriodoLiquidacion": {
                "Ejercicio": ejercicio,
                "Periodo": periodo,
            },
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.vat[2:],
                },
                "NumSerieFacturaEmisor":
                    (self.number or self.internal_number or '')[0:60],
                "FechaExpedicionFacturaEmisor": invoice_date,
            },
        }
        if not partner.sii_simplified_invoice:
            # Simplified invoices don't have counterpart
            inv_dict["Contraparte"] = {"NombreRazon": partner.name[0:120]}
            # Uso condicional de IDOtro/NIF
            inv_dict['Contraparte'].update(self._get_sii_identifier())
        return inv_dict

    @api.multi
    def _get_contrast_invoice_dict_in(self):
        """Build dict with data to send to AEAT WS for invoice types:
        in_invoice and in_refund.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.date_invoice)
        ejercicio = fields.Date.from_string(self.date).year
        periodo = '%02d' % fields.Date.from_string(self.date).month
        inv_dict = {
            "FiltroConsulta": {},
            "IDFactura": {
                "IDEmisorFactura": {
                    "NombreRazon":
                        self.partner_id.commercial_partner_id.name[0:120],
                },
                "NumSerieFacturaEmisor": (
                    (self.reference or '')[:60]
                ),
                "FechaExpedicionFacturaEmisor": invoice_date},
            "PeriodoLiquidacion": {
                "Ejercicio": ejercicio,
                "Periodo": periodo
            },
        }
        # Uso condicional de IDOtro/NIF
        ident = self._get_sii_identifier()
        inv_dict['IDFactura']['IDEmisorFactura'].update(ident)
        return inv_dict

    @api.multi
    def _get_contrast_invoice_dict(self):
        self.ensure_one()
        self._sii_check_exceptions()
        if self.type in ['out_invoice', 'out_refund']:
            return self._get_contrast_invoice_dict_out()
        elif self.type in ['in_invoice', 'in_refund']:
            return self._get_contrast_invoice_dict_in()
        return {}

    @api.multi
    def _contrast_invoice_to_aeat(self):
        for invoice in self.filtered(lambda i: i.state in ['open', 'paid']):
            serv = invoice._connect_sii(invoice.type)
            header = invoice._get_sii_header(False, True)
            inv_vals = {}
            try:
                inv_dict = invoice._get_contrast_invoice_dict()
                inv_vals['sii_match_sent'] = json.dumps(inv_dict, indent=4)
                res_line = False
                if invoice.type in ['out_invoice', 'out_refund']:
                    res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                    res_line = \
                        res['RegistroRespuestaConsultaLRFacturasEmitidas'][0]
                elif invoice.type in ['in_invoice', 'in_refund']:
                    res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                    res_line = \
                        res['RegistroRespuestaConsultaLRFacturasRecibidas'][0]
                inv_vals.update({
                    'sii_contrast_state': 'no_exist',
                    'sii_match_state': False,
                })
                if res_line:
                    if res_line['DatosPresentacion']['CSV'] == self.sii_csv:
                        cuadre_state = (
                            res_line['EstadoFactura']['EstadoCuadre']
                            if res_line['EstadoFactura'] else False)
                        if cuadre_state:
                            inv_vals.update({
                                'sii_match_state':
                                    res_line['EstadoFactura']['EstadoCuadre'],
                                'sii_contrast_state': 'correct',
                            })
                            diffs = invoice._get_diffs_values(res_line)
                            if diffs:
                                inv_vals['sii_match_difference_ids'] = diffs
                                inv_vals.update(
                                    {'sii_contrast_state': 'partially', })
                invoice.sii_match_difference_ids.unlink()
                inv_vals['sii_match_return'] = json.dumps(
                    serialize_object(res), indent=4)
                invoice.write(inv_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env['account.invoice'].browse(self.id)
                inv_vals.update({
                    'sii_match_return': repr(fault),
                    'sii_contrast_state': False,
                    'sii_match_state': False,
                })
                invoice.write(inv_vals)
                new_cr.commit()
                new_cr.close()
                raise

    @job(default_channel='root.invoice_validate_sii')
    @api.multi
    def contrast_one_invoice(self):
        self._contrast_invoice_to_aeat()
