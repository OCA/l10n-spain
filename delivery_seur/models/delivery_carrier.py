# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from lxml import etree
from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

try:
    from zeep import Client, Plugin, helpers
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin

    class RewritePlugin(Plugin):
        def __init__(self, xpath, value):
            self.xpath = xpath
            self.value = value
            super().__init__()

        def egress(self, envelope, http_headers, operation, binding_options):
            node = envelope.xpath(self.xpath)
            if node:
                node[0].text = etree.CDATA(self.value.decode('utf-8'))

except (ImportError, IOError) as err:
    _logger.debug(err)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('seur', 'Seur')],
    )
    seur_vat = fields.Char(
        string='VAT',
        default=lambda self: self.env.user.company_id.vat,
    )
    seur_franchise_code = fields.Char(
        string='Franchise Code',
    )
    seur_accounting_code = fields.Char(
        string='Accounting Code (CCC)',
    )
    seur_integration_code = fields.Char(
        string='Integration Code (CI)',
    )
    seur_cit_username = fields.Char(
        string='Username CIT',
        help='Used for cit.seur.com webservice (generate labels)',
    )
    seur_cit_password = fields.Char(
        sting='Password CIT',
        help='Used for cit.seur.com webservice (generate labels)',
    )
    seur_ws_username = fields.Char(
        string='Username WS',
        help='Used for ws.seur.com webservice (pickup services)',
    )
    seur_ws_password = fields.Char(
        string='Password WS',
        help='Used for ws.seur.com webservice (pickup services)',
    )
    seur_service_code = fields.Selection(
        selection=[
            ('001', 'SEUR - 24'),
            ('003', 'SEUR - 10'),
            ('005', 'MISMO DIA'),
            ('007', 'COURIER'),
            ('009', 'SEUR 13:30'),
            ('013', 'SEUR - 72'),
            ('015', 'S-48'),
            ('017', 'MARITIMO'),
            ('019', 'NETEXPRESS'),
            ('031', 'ENTREGA PARTIC'),
            ('077', 'CLASSIC'),
            ('083', 'SEUR 8:30'),
        ],
        default='031',
        string='Service code',
    )
    seur_product_code = fields.Selection(
        selection=[
            ('002', 'ESTANDAR'),
            ('004', 'MULTIPACK'),
            ('006', 'MULTI BOX'),
            ('018', 'FRIO'),
            ('052', 'MULTI DOC'),
            ('054', 'DOCUMENTOS'),
            ('070', 'INTERNACIONAL ´T'),
            ('072', 'INTERNACIONAL A'),
            ('076', 'CLASSIC'),
            ('118', 'VINO')
        ],
        default='002',
        string='Product code',
    )
    seur_send_sms = fields.Boolean(
        string='Send SMS to customer',
        help='This feature has delivery cost',
    )
    seur_label_format = fields.Selection(
        selection=[
            ('pdf', 'PDF'),
            ('txt', 'TXT'),
        ],
        default='pdf',
        string='Label format',
    )
    seur_label_size = fields.Selection(
        selection=[
            ('1D', '1D'),
            ('2D', '2D'),
            ('2C', '2C'),
        ],
        default='2C',
        string='Label size',
    )
    seur_printer = fields.Selection(
        selection=[
            ('DATAMAX:E CLASS 4203', 'DATAMAX E CLASS 4203'),
            ('HP:LASERJET II', 'HP LASERJET II'),
            ('INTERMEC:C4', 'INTERMEC C4'),
            ('TEC:B430', 'TEC B430'),
            ('ZEBRA:LP2844-Z', 'ZEBRA LP2844-Z'),
            ('ZEBRA:S600', 'ZEBRA S600'),
            ('ZEBRA:Z4M PLUS', 'ZEBRA Z4M PLUS'),
        ],
        string='Printer',
        default='ZEBRA:LP2844-Z',
    )

    @api.model
    def seur_wsdl_get(self, service):
        if service in ['ImprimirECBWebService', 'IntAppletWebService']:
            return 'http://cit.seur.com/CIT-war/services/%s?wsdl' % service
        if service == 'WSConsultaExpediciones':
            return 'https://ws.seur.com/webseur/services/%s?wsdl' % service
        raise NotImplementedError

    @api.model
    def seur_soap_send(self, service, method, data):
        def trace(title, data):
            _logger.debug('%s %s: %s' % (
                method, title, etree.tostring(data['envelope'])))

        def create_rewrite_plugin(data):
            key = [k for k, v in data.items() if isinstance(v, dict)]
            if not key:
                return RewritePlugin('//no-dict', '')
            key = key[0]
            if 'total_bultos' not in data[key]:
                return RewritePlugin('//missing-key', '')
            xml_root = etree.Element('root')
            xml_exp = etree.SubElement(xml_root, 'exp')
            for _index in range(int(data[key].get('total_bultos') or 1)):
                package = etree.SubElement(xml_exp, 'bulto')
                for k, v in data[key].items():
                    etree.SubElement(package, k).text = str(v or '')
            xml = etree.tostring(xml_root, encoding='utf8', method='xml')
            data[key] = '-RewritePlugin-'
            return RewritePlugin('//*[text()="-RewritePlugin-"]', xml)

        history = HistoryPlugin()
        client = Client(
            wsdl=self.seur_wsdl_get(service),
            transport=Transport(),
            plugins=[history, create_rewrite_plugin(data)],
        )
        cli = client.bind(service)
        response = cli[method](**data)
        trace('Request', history.last_sent)
        trace('Response', history.last_received)
        response = helpers.serialize_object(response, dict)
        # Add the history to the response so we are able to use it
        response.update({
            'seur_last_request': history.last_sent,
            'seur_last_response': history.last_received,
        })
        return response

    def seur_test_connection(self):
        self.ensure_one()
        res = self.seur_soap_send(
            'ImprimirECBWebService', 'impresionIntegracionPDFConECBWS',
            {
                'in0': self.seur_cit_username,
                'in1': self.seur_cit_password,
                'in2': '',
                'in3': 'fichero.xml',
                'in4': self.seur_vat,
                'in5': self.seur_franchise_code,
                'in6': self.seur_accounting_code,
                'in7': 'odoo',
            }
        )
        return res and res['mensaje'] == 'ERROR'

    def seur_send_shipping(self, pickings):
        return [self.seur_create_shipping(p) for p in pickings]

    def _seur_prepare_create_shipping(self, picking):
        self.ensure_one()
        partner = picking.partner_id
        partner_name = partner.display_name
        # When we've got an specific delivery address we want to prioritize its
        # name over the commercial one
        if partner.parent_id and partner.type == "delivery" and partner.name:
            partner_name = "{} ({})".format(
                partner.name, partner.commercial_partner_id.name
            )
        partner_att = (
            partner.name if partner.parent_id and partner.type == "contact"
            else ""
        )
        company = picking.company_id
        phone = (partner.phone and partner.phone.replace(' ', '') or '')
        mobile = (partner.mobile and partner.mobile.replace(' ', '') or '')
        return {
            'ci': self.seur_integration_code,
            'nif': self.seur_vat,
            'ccc': self.seur_accounting_code,
            'servicio': self.seur_service_code,
            'producto': self.seur_product_code,
            'cod_centro': '',
            'total_bultos': picking.number_of_packages or 1,
            # The item pricelists in SEUR begin in a range o >1kg. So any item
            # below that weight will be invoiced with a minimum of 1kg.
            # http://ayuda.seur.com
            # /faq/tamano-peso-de-los-paquetes-a-enviar-a-traves-de-seur-com
            'total_kilos': picking.shipping_weight or 1,
            'pesoBulto': ((
                picking.shipping_weight / picking.number_of_packages or 1)
                or 1),
            'observaciones': picking.note,
            'referencia_expedicion': picking.name,
            'ref_bulto': '',
            'clavePortes': 'F',
            'clavePod': '',
            'claveReembolso': 'F',
            'valorReembolso': '',
            'libroControl': '',
            'nombre_consignatario': partner_name,
            'direccion_consignatario': ' '.join([
                s for s in [partner.street, partner.street2] if s]),
            'tipoVia_consignatario': '',
            'tNumVia_consignatario': '',
            'numVia_consignatario': '',
            'escalera_consignatario': '',
            'piso_consignatario': '',
            'puerta_consignatario': '',
            'poblacion_consignatario': partner.city,
            'codPostal_consignatario': partner.zip,
            'pais_consignatario': (
                partner.country_id and partner.country_id.code or ''),
            'email_consignatario': partner.email,
            'telefono_consignatario': phone or mobile,
            'sms_consignatario': self.seur_send_sms and mobile or '',
            'atencion_de': partner_att,
            'test_preaviso': 'S',
            'test_reparto': 'S',
            'test_email': partner.email and 'S' or 'N',
            'test_sms': mobile and 'S' or 'N',
            'id_mercancia': (
                company.country_id == partner.country_id and '400' or ''),
            'nombre_remitente': company.name,
            'direccion_remitente': ' '.join([
                s for s in [company.street, company.street2] if s]),
            'codPostal_remitente': company.zip,
            'poblacion_remitente': company.city,
            'tipoVia_remitente': '',
            'eci': 'N',
            'et': 'N',
        }

    def _zebra_label_custom(self, label):
        """Some printers might have special configurations so we could need
        to tweak the label in advance. For example, we could need to adjust
        initial position:
        label.replace("^LH105,40", "^LH50,0")
        """
        return label

    def seur_create_shipping(self, picking):
        self.ensure_one()
        package_info = self._seur_prepare_create_shipping(picking)
        if self.seur_label_format == 'txt':
            res = self.seur_soap_send(
                'ImprimirECBWebService', 'impresionIntegracionConECBWS',
                {
                    'in0': self.seur_cit_username,
                    'in1': self.seur_cit_password,
                    'in2': self.seur_printer.split(':')[0],
                    'in3': self.seur_printer.split(':')[1],
                    'in4': self.seur_label_size,
                    'in5': package_info,
                    'in6': 'fichero.xml',
                    'in7': self.seur_vat,
                    'in8': self.seur_franchise_code,
                    'in9': self.seur_accounting_code,
                    'in10': 'odoo',
                }
            )
        else:
            res = self.seur_soap_send(
                'ImprimirECBWebService', 'impresionIntegracionPDFConECBWS',
                {
                    'in0': self.seur_cit_username,
                    'in1': self.seur_cit_password,
                    'in2': package_info,
                    'in3': 'fichero.xml',
                    'in4': self.seur_vat,
                    'in5': self.seur_franchise_code,
                    'in6': self.seur_accounting_code,
                    'in7': 'odoo',
                }
            )
        # The error message could be more complex than a simple 'ERROR' sting.
        # For example, if there's wrong address info, it will return an
        # xml with the API error.
        seur_last_request = res.get("seur_last_request", False)
        seur_last_response = res.get("seur_last_response", False)
        try:
            error = (
                res['mensaje'] == 'ERROR' or
                not res.get('ECB', {}).get('string', []))
            if error:
                raise exceptions.UserError(
                    _('SEUR exception: %s') % res['mensaje'])
            picking.carrier_tracking_ref = res['ECB']['string'][0]
            if self.seur_label_format == 'txt':
                label_content = self._zebra_label_custom(res['traza'])
                # SEUR sends the label in spanish format (^CI10) so we need
                # to encode the file in such ISO as well so special characters
                # print fine
                label_content = label_content.encode("iso-8859-15")
                label_content = base64.b64encode(label_content)
            else:
                label_content = res['PDF']
            self.env['ir.attachment'].create({
                'name': 'SEUR %s' % picking.carrier_tracking_ref,
                'datas': label_content,
                'datas_fname': 'seur_%s.%s' % (
                    picking.carrier_tracking_ref, self.seur_label_format),
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'mimetype': 'application/%s' % self.seur_label_format,
            })
            res['tracking_number'] = picking.carrier_tracking_ref
            res['exact_price'] = 0
        # We'll write on the picking no matter what
        finally:
            picking.write({
                "seur_last_request": seur_last_request,
                "seur_last_response": seur_last_response,
            })
        return res

    def seur_tracking_state_update(self, picking):
        self.ensure_one()
        if not self.seur_ws_username:
            picking.tracking_state_history = _(
                'Status cannot be checked, enter webservice carrier '
                'credentials')
            return
        res = self.seur_soap_send(
            'WSConsultaExpediciones', 'consultaExpedicionesStr',
            {
                'in0': 'S',
                'in1': '',
                'in2': '',
                'in3': picking.carrier_tracking_ref,
                'in4': '',
                'in5': '',
                'in6': '',
                'in7': '',
                'in8': '',
                'in9': '',
                'in10': '',
                'in11': '0',
                'in12': self.seur_ws_username,
                'in13': self.seur_ws_password,
                'in14': 'S',
            },
        )
        xml = etree.fromstring(res)
        errors = [n.text for n in xml.xpath('//ERROR/DESCRIPCION')]
        if errors:
            picking.tracking_state_history = '\n'.join(errors)
            return
        picking.tracking_state_history = '\n'.join([
            '%s | %s' % (
                sit.find('FECHA_SITUACION').text,
                sit.find('DESCRIPCION_CLIENTE').text)
            for sit in xml.xpath('//SIT')])
        state = xml.xpath('(//DESCRIPCION_CLIENTE)[last()]')[0].text.strip()
        static_states = {
            'EN TRÁNSITO': 'in_transit',
            'MERCANCÍA EN REPARTO': 'in_transit',
            'ENTREGA EFECTUADA': 'customer_delivered',
            'ENTREGADO EN PUNTO': 'customer_delivered',
            'ENTREGADO CAMBIO SIN RETORNO': 'customer_delivered',
        }
        picking.delivery_state = static_states.get(state, 'incidence')

    def seur_cancel_shipment(self, pickings):
        for picking in pickings:
            res = picking.carrier_id.seur_soap_send(
                'IntAppletWebService', 'modificarEnvioCIT',
                {
                    'in0': {
                        'usuario': picking.carrier_id.seur_cit_username,
                        'password': picking.carrier_id.seur_cit_password,
                        'franquicia': picking.carrier_id.seur_franchise_code,
                        'nif': picking.carrier_id.seur_vat,
                        'ccc': picking.carrier_id.seur_accounting_code,
                        'referencia': picking.name,
                        'accion': 'A',
                        'valorReembolso': '',
                        'valorSeguro': '',
                        'pesoTotal': '',
                    },
                },
            )
            if res['estado'] == 'KO':
                raise UserWarning(_('Cancel SEUR shipment (%s): %s') % (
                    picking.carrier_tracking_ref, res['mensaje']))
        return True

    def seur_get_tracking_link(self, picking):
        return (
            'https://www.seur.com/livetracking/?segOnlineIdentificador=%s' % (
                picking.carrier_tracking_ref
            )
        )

    def seur_rate_shipment(self, order):
        """There's no public API so another price method should be used"""
        raise NotImplementedError(_("""
            SEUR API doesn't provide methods to compute delivery rates, so
            you should relay on another price method instead or override this
            one in your custom code.
        """))
