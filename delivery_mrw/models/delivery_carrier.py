# Copyright 2021 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import _, fields, models
from .mrw_request import MrwRequest
from .mrw_request import (
        MRW_SERVICES, MRW_IN_FRANCHISE, MRW_BOOLEAN, MRW_RETURN, MRW_REFUND,
        MRW_DELIVERY_STATES_STATIC
    )


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('mrw', 'MRW')])
    mrw_api_franchise = fields.Char(string='Franchise')
    mrw_api_subscriber = fields.Char(string='Subscriber')
    mrw_api_user = fields.Char(string='UID')
    mrw_api_password = fields.Char(string='Password')
    mrw_api_dept_code = fields.Char(string='Department Code')
    mrw_api_language = fields.Char(
        string='Language Code', default='3082',
        help='3082 for Spanish; 2070 for Portuguese')
    mrw_api_filter_type = fields.Integer(
        string='Filter Type', default=0,
        help='0 for tracking number; 1 for reference; 2 package reference')
    mrw_api_information_type = fields.Integer(
        string='Information Type', default=0,
        help='0 for Basic Information; 1 for Detailed')

    mrw_service = fields.Selection(
        selection=MRW_SERVICES,
        string='Service',
        help='Set the contracted MRW Service',
    )
    mrw_in_franchise = fields.Selection(
        selection=MRW_IN_FRANCHISE,
        string='In Franchise', default='N'
    )
    mrw_delivery_on_saturday = fields.Selection(
        selection=MRW_BOOLEAN,
        string='Delivery on Saturday', default='N')
    mrw_return = fields.Selection(
        selection=MRW_RETURN, string='Return',
        help='(Optional) delivery with return', default='N')
    mrw_refund = fields.Selection(
        selection=MRW_REFUND, string='Refund')
    mrw_label_type = fields.Integer(string='Label Type', default=0)
    mrw_margin_top = fields.Integer(string='Margin Top', default=1100)
    mrw_margin_left = fields.Integer(string='Margin Left', default=650)

    def _get_mrw_wsdl_file(self):
        wsdl_file = 'mrw-api-test.wsdl'
        if self.prod_environment:
            wsdl_file = 'mrw-api-prod.wsdl'
        return wsdl_file

    def _get_mrw_wsdl_tracking_file(self):
        wsdl_file = 'mrw-api-tracking-prod.wsdl'
        return wsdl_file

    def _prepare_mrw_shipping(self, picking):
        """Convert picking values for mrw api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        partner = picking.partner_id
        street = partner.street or ''
        if partner.street2 or '':
            if street:
                street += ' '
            street += partner.street2
        return {
            'entrega_codigo_direccion': '',  # [optional]
            'entrega_tipo_via': '',  # [optional]] MRW_TIPO_VIA
            'entrega_via': street or '',
            'entrega_numero': '',
            'entrega_resto': '',
            'entrega_codigo_postal': partner.zip or '',
            'entrega_poblacion': partner.city or '',
            'entrega_estado': partner.state_id.name or '',
            'entrega_codigo_pais': partner.country_id.code or '',

            'entrega_nif': partner.vat or '',
            'entrega_nombre': partner.name or '',
            'entrega_telefono': partner.phone or partner.mobile or '',
            'entrega_contacto': '',
            'entrega_atencion': '',
            'entrega_horario_rango_desde': '08:00',
            'entrega_horario_rango_hasta': '18:00',
            'entrega_observaciones': '',
            'fecha': fields.Date.today().strftime('%d/%m/%Y'),
            'referencia_albaran': picking.name,
            'en_franquicia': self.mrw_in_franchise,
            'codigo_servicio': self.mrw_service,
            'descripcion_servicio': '',
            'numero_bultos': picking.number_of_packages or '1',
            'peso': str(picking.weight).replace('.', ','),
            'entrega_sabado': self.mrw_delivery_on_saturday or '',
            'retorno': self.mrw_return or '',
            'reembolso': self.mrw_refund or '',
            'importe_reembolso': '',
        }

    def mrw_send_shipping(self, pickings):
        """Send the package to MRW
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        wsdl_file = self._get_mrw_wsdl_file()
        mrw_request = MrwRequest(
            wsdl_file, self.mrw_api_franchise, self.mrw_api_subscriber,
            self.mrw_api_user, self.mrw_api_password, self.mrw_api_dept_code)
        result = []
        for picking in pickings:
            vals = self._prepare_mrw_shipping(picking)
            vals.update({'tracking_number': False, 'exact_price': 0})
            response = mrw_request._send_shipping(vals)
            self.mrw_request = response['mrw_sent_xml']
            self.mrw_response = response['response'] or ''
            if not response['tracking_number']:
                result.append(vals)
                continue
            vals['tracking_number'] = response['tracking_number']
            picking.carrier_tracking_ref = response['tracking_number']
            # request for label:
            label_response = self.mrw_request_label(
                response['tracking_number'])
            body = (_(
                'MRW Shipping extra info:\n'
                'barcode: %s') % response.get('tracking_number'))
            attachment = []
            if label_response.get('label_file'):
                file_name = 'mrw_label_{}.pdf'.format(
                    response.get('tracking_number'))
                file_content = label_response.get('label_file')
                attachment = [(file_name, file_content)]
            picking.message_post(body=body, attachments=attachment)

            result.append(vals)
        return result

    def _prepare_mrw_request_label(self, tracking_number):
        """Convert picking values for mrw api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        today = datetime.today()
        today_str = today.strftime('%d/%m/%Y')
        return {
            'numero_envio': tracking_number,
            'separador_numero_envio': '',
            'fecha_inicio': today_str,
            'tipo_etiqueta_envio': self.mrw_label_type,
            'margin_top': self.mrw_margin_top,
            'margin_left': self.mrw_margin_left,
        }

    def mrw_request_label(self, tracking_number):
        wsdl_file = self._get_mrw_wsdl_file()
        mrw_request = MrwRequest(
            wsdl_file, self.mrw_api_franchise, self.mrw_api_subscriber,
            self.mrw_api_user, self.mrw_api_password, self.mrw_api_dept_code)
        vals = self._prepare_mrw_request_label(tracking_number)
        response = mrw_request._request_label(vals)
        return response

    def mrw_rate_shipment(self, order):
        """Maybe there's a public MRW API method to compute price
        but it is not implemented, just define this function to be able
        to develop a personalized method"""
        raise NotImplementedError(_("""
            Computation of delivery price is not implemented. You should
            develope it.
        """))

    def _prepare_mrw_tracking(self, picking):
        self.ensure_one()
        return {
            'login': self.mrw_api_user,
            'password': self.mrw_api_password,
            'language': self.mrw_api_language,
            'filtertype': self.mrw_api_filter_type,
            'filter_init': picking.carrier_tracking_ref,
            'filter_finish': picking.carrier_tracking_ref,
            'date_from': '',
            'date_until': '',
            'information_type': self.mrw_api_information_type,
        }

    def mrw_tracking_state_update(self, picking):
        """Tracking state update"""
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        wsdl_file = self._get_mrw_wsdl_tracking_file()
        mrw_request = MrwRequest(
            wsdl_file, self.mrw_api_franchise, self.mrw_api_subscriber,
            self.mrw_api_user, self.mrw_api_password, self.mrw_api_dept_code)
        vals = self._prepare_mrw_tracking(picking)
        tracking_states = mrw_request._get_tracking_states(vals)
        if not tracking_states:
            return
        picking.tracking_state_history = '\n'.join([
            '%s %s - [%s] %s' % (
                t.get('date'), t.get('time'), t.get('state_code'),
                t.get('description'))
            for t in tracking_states
        ])
        tracking = tracking_states.pop()
        picking.tracking_state = '[{}] {}'.format(
            tracking.get('state_code'), tracking.get('description'))
        picking.delivery_state = MRW_DELIVERY_STATES_STATIC.get(
            tracking.get('state_code'), 'incidence')
