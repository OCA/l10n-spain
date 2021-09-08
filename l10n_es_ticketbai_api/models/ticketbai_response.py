# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from ..utils import utils as tbai_utils
from ..ticketbai.xml_schema import XMLSchema, TicketBaiSchema
from odoo import models, fields, api, _


class TicketBaiCancellationResponseCode(tbai_utils.EnumValues):
    INCORRECT_SENDER_CERTIFICATE = '001'
    XSD_SCHEMA_NOT_COMPLY = '002'
    INVALID_SENDER_CERTIFICATE = '003'
    WRONG_SIGNATURE = '004'
    INVALID_SIGNER_CERTIFICATE = '005'
    REQUIRED_FIELD_MISSING = '006'
    INVALID_TBAI_LICENSE = '007'
    DEVICE_NOT_REGISTERED = '008'
    ADDRESSEE_NOT_REGISTERED = '009'
    INVOICE_NOT_REGISTERED = '010'
    INVOICE_ALREADY_CANCELLED = '011'
    SERVICE_NOT_AVAILABLE = '012'


class TicketBaiInvoiceResponseCode(tbai_utils.EnumValues):
    INCORRECT_SENDER_CERTIFICATE = '001'
    XSD_SCHEMA_NOT_COMPLY = '002'
    INVOICE_WITHOUT_LINES = '003'
    TBAI_IDENTIFIER_FIELD_MISSING = '004'
    INVOICE_ALREADY_REGISTERED = '005'
    SERVICE_NOT_AVAILABLE = '006'
    INVALID_SENDER_CERTIFICATE = '007'
    WRONG_SIGNATURE = '008'
    INVALID_SIGNER_CERTIFICATE = '009'
    INCORRECT_INVOICE_CHAINING = '010'
    REQUIRED_FIELD_MISSING = '011'
    INVALID_TBAI_LICENSE = '012'
    DEVICE_NOT_REGISTERED = '013'
    ADDRESSEE_NOT_REGISTERED = '014'


class TicketBaiResponseState(tbai_utils.EnumValues):
    BUILD_ERROR = '-2'
    REQUEST_ERROR = '-1'
    RECEIVED = '00'
    REJECTED = '01'


class TicketBaiResponse(models.Model):
    _name = 'tbai.response'
    _order = 'id desc'
    _description = 'TicketBAI Tax Agency Invoice response'

    tbai_invoice_id = fields.Many2one(
        comodel_name='tbai.invoice', required=True, ondelete='cascade')
    xml = fields.Binary(string='XML Response', attachment=True)
    xml_fname = fields.Char('File Name')
    state = fields.Selection(string='Status', selection=[
        (TicketBaiResponseState.RECEIVED.value, 'Received'),
        (TicketBaiResponseState.REJECTED.value, 'Rejected'),
        (TicketBaiResponseState.REQUEST_ERROR.value, 'Request error'),
        (TicketBaiResponseState.BUILD_ERROR.value, 'Build error')
    ], required=True)
    tbai_response_message_ids = fields.One2many(
        comodel_name='tbai.response.message', inverse_name='tbai_response_id')

    @api.model
    def prepare_tbai_api_error_values(self, msg, **kwargs):
        values = kwargs
        values.update({
            'state': TicketBaiResponseState.BUILD_ERROR.value,
            'tbai_response_message_ids': [
                (0, 0, {
                    'code': _("TicketBAI API required fields missing."),
                    'description': msg
                })
            ]
        })
        return values

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
            xml_dict = XMLSchema(
                TicketBaiSchema.TicketBaiResponse.value).parse_xml(
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
    _description = 'TicketBAI Tax Agency Invoice response messages'

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
