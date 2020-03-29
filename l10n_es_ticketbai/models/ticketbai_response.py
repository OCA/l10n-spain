# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from enum import Enum
from ..ticketbai.xml_schema import XMLSchema, TicketBaiInvoiceTypeEnum
from odoo import models, fields, api, _


class TicketBaiResponseState(Enum):
    REQUEST_ERROR = -1
    RECEIVED = '00'
    REJECTED = '01'


class TicketBaiResponse(models.Model):
    _name = 'tbai.response'
    _order = 'id desc'

    xml = fields.Binary(string='XML Response')
    xml_fname = fields.Char('File Name', compute='_compute_xml_fname')
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', required=True, ondelete='cascade')
    state = fields.Selection(selection=[
        (TicketBaiResponseState.RECEIVED.value, 'Received'),
        (TicketBaiResponseState.REJECTED.value, 'Rejected'),
        (TicketBaiResponseState.REQUEST_ERROR.value, 'Request error')
    ], required=True)
    tbai_response_message_ids = fields.One2many(
        comodel_name='tbai.response.message', inverse_name='tbai_response_id')

    def __init__(self, pool, cr):
        super(TicketBaiResponse, self).__init__(pool, cr)
        type(self).TicketBAIXMLSchema = XMLSchema(TicketBaiInvoiceTypeEnum.response)

    @api.multi
    @api.depends('invoice_id', 'state')
    def _compute_xml_fname(self):
        for record in self:
            state = dict(record._fields['state']._description_selection(
                record.env)).get(record.state)
            record.xml_fname = "%s_%s_%s.xml" % (
                _("Invoice"), record.invoice_id.number.replace('/', '_'), state)

    @api.model
    def prepare_tbai_response_values(self, response, **kwargs):
        values = kwargs
        if response.error:
            errno = response.errno
            strerror = response.strerror
            values.update({
                'state': TicketBaiResponseState.REQUEST_ERROR.value,
                'tbai_response_message_ids': [
                    (0, 0, {
                        'code': errno,
                        'description': strerror
                    })
                ]
            })
        else:
            xml_dict = self.TicketBAIXMLSchema.parse_xml(
                response.data)['TicketBaiResponse'] or {}
            state = xml_dict['Salida']['Estado']
            values.update({
                'xml': base64.encodebytes(response.data.encode('utf-8')),
                'state': state
            })
            if state == TicketBaiResponseState.RECEIVED.value:
                tbai_response_message_ids = [(0, 0, {
                    'code': xml_dict['Salida']['CSV'],
                    'description': {
                        'es_ES': xml_dict['Salida']['Descripcion'],
                        'eu_ES': xml_dict['Salida']['Azalpena']
                    }
                })]
            elif state == TicketBaiResponseState.REJECTED.value:
                messages = xml_dict['Salida']['ResultadosValidacion']
                tbai_response_message_ids = []
                if isinstance(messages, dict):
                    messages = [messages]
                for msg in messages:
                    tbai_response_message_ids.append((0, 0, {
                        'code': msg['Codigo'],
                        'description': {
                            'es_ES': msg['Descripcion'],
                            'eu_ES': msg['Azalpena']
                        }
                    }))
            else:
                tbai_response_message_ids = [(0, 0, {
                    'code': state,
                    'description': _('Unknown TicketBAI response code.')
                })]
            values.update(tbai_response_message_ids=tbai_response_message_ids)
        return values


class TicketBaiResponseMessage(models.Model):
    _name = 'tbai.response.message'

    tbai_response_id = fields.Many2one(
        comodel_name='tbai.response', required=True, ondelete='cascade')
    code = fields.Char(required=True)
    description = fields.Char(required=True, translate=True)

    @api.multi
    @api.depends('code', 'description')
    def name_get(self):
        result = []
        for msg in self:
            name = "%s - %s" % (msg.code, msg.description)
            result.append((msg.id, name))
        return result

    @api.model
    def create(self, vals):
        if 'description' in vals and isinstance(vals['description'], dict):
            description = vals['description']['es_ES']
            description_basque_translation = vals['description']['eu_ES']
            vals['description'] = description
        else:
            description_basque_translation = ''
        record = super().create(vals)
        lang = self.env['res.lang'].search([('code', '=', 'eu_ES')], limit=1)
        if lang and description_basque_translation:
            record.with_context(lang='eu_ES').description = \
                description_basque_translation
        return record
