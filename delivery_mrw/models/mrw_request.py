# Copyright 2021 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import UserError
import logging
import binascii
import os

_logger = logging.getLogger(__name__)

try:
    from zeep import Client as ZeepClient
    from zeep.transports import Transport as ZeepTransport
    from zeep import helpers as ZeepHelpers
    from suds.client import Client
    from suds.sax.text import Raw
    from suds.sudsobject import asdict
    from suds.sax.element import Element
except (ImportError, IOError) as err:
    _logger.debug(err)

MRW_SERVICES = [
    ('0000', 'Urgente 10'),
    ('0005', 'Urgente Hoy'),
    ('0010', 'Promociones'),
    ('0100', 'Urgente 12'),
    ('0110', 'Urgente 14'),
    ('0120', 'Urgente 22'),
    ('0200', 'Urgente 19'),
    ('0205', 'Urgente 19 Expedicion'),
    ('0210', 'Urgente 19 Mas 40 Kilos'),
    ('0220', 'Urgente 19 Portugal'),
    ('0230', 'Bag 19'),
    ('0235', 'Bag 14'),
    ('0300', 'Economico'),
    ('0310', 'Economico Mas 40 Kilos'),
    ('0350', 'Economico Interinsular'),
    ('0400', 'Express Documentos'),
    ('0450', 'Express 2 Kilos'),
    ('0480', 'Caja Express 3 Kilos'),
    ('0490', 'Documentos 14'),
    ('0800', 'Ecommerce'),
    ('0810', 'Ecommerce Canje'),
]

MRW_IN_FRANCHISE = [
    ('N', 'No collection or delivery in franchise'), # Sin recogida ni entrega en franquicia.
    ('R', 'Collection in Franchise'), # Con recogida en franquicia.
    ('E', 'Delivery in Franchise'), # Con entrega en franquicia.
    ('A', 'Collection and delivery in franchise'), # Con recogida y entrega en franquicia.
]

MRW_BOOLEAN = [
    ('S', 'Yes'),
    ('N', 'No'),
]

MRW_RETURN = [
    ('N', 'No return'),
    ('O', 'Return Collect at Origin'),
    ('D', 'Return Collect at Destiny'),
    ('S', 'Return of merchandise'),
]

MRW_REFUND = [
    ('N', 'Without Refund'),
    ('O', 'Refund at Origin'),
    ('D', 'Refund at Destiny'),
]

MRW_TIPO_VIA = [
    ('AB', 'ARRABAL'),
    ('AC', 'ACERA'),
    ('AD', 'ALDA'),
    ('AE', 'ACCESO'),
    ('AI', 'PATIO'),
    ('AL', 'ALAMEDA'),
    ('AN', 'ANTIGUO'),
    ('AO', 'ARCO'),
    ('AP', 'APARTAMENTO'),
    ('AR', 'ARA'),
    ('AS', 'CASAS'),
    ('AT', 'ALTO'),
    ('AU', 'AUTOVIA'),
    ('AV', 'AVENIDA'),
    ('AY', 'ARROYO'),
    ('AZ', 'PLAZUELA'),
    ('BA', 'BARRIADA'),
    ('BB', 'RCANTOS'),
    ('BJ', 'BAJADA'),
    ('BL', 'BLOQUE'),
    ('BO', 'BARRIO'),
    ('BR', 'BARRANCO'),
    ('BU', 'BULEVAR'),
    ('CA', 'CALLEJA'),
    ('CB', 'CIRCUNVALACION'),
    ('CC', 'CAMPO'),
    ('CD', 'CUADRA'),
    ('CE', 'CARRERA'),
    ('CG', 'COLGIO'),
    ('CH', 'CHALET'),
    ('CI', 'CARRIL'),
    ('CJ', 'CALLEJON'),
    ('CL', 'CALLE'),
    ('CM', 'CAMINO'),
    ('CN', 'CONJUNTO'),
    ('CÑ', 'CAÑADA'),
    ('CO', 'CORTIJO'),
    ('CP', 'CAMPING'),
    ('CQ', 'ACEQUIA'),
    ('CR', 'CARRETERA'),
    ('CS', 'CASERIO'),
    ('CT', 'CINTURON'),
    ('CU', 'CUESTA'),
    ('CV', 'CAMINO VIEJO'),
    ('CZ', 'CALZADA'),
    ('DA', 'RINCONADA'),
    ('DC', 'CORRDOR'),
    ('DE', 'DHESA'),
    ('DS', 'DISEMINADO'),
    ('EA', 'ESCALAS'),
    ('EC', 'ESTACION'),
    ('ED', 'DIFICIO'),
    ('EJ', 'CALLEJUELA'),
    ('EM', 'EXTRAMUROS'),
    ('EN', 'ENTRADA'),
    ('EO', 'CERRO'),
    ('ER', 'EXTRARRADIO'),
    ('ES', 'ESCALINATA'),
    ('ET', 'ESTRADA'),
    ('EX', 'EXPLANADA'),
    ('FC', 'FERROCARRIL'),
    ('FN', 'FINCA'),
    ('FU', 'FUENTE'),
    ('GL', 'GLORIETA'),
    ('GR', 'GRUPO'),
    ('GV', 'GRAN VIA'),
    ('HO', 'HORTA'),
    ('HT', 'HUERTA'),
    ('IN', 'RCINTO'),
    ('IS', 'ISLA'),
    ('IU', 'CIUDADELA'),
    ('JP', 'PARAJE'),
    ('JR', 'JARDINES'),
    ('KO', 'COOPERATIVA'),
    ('LA', 'PLACETA'),
    ('LD', 'LADO'),
    ('LG', 'LUGAR'),
    ('LL', 'PASILLO'),
    ('LM', 'LOMA'),
    ('LN', 'LLANO'),
    ('LQ', 'ALQUERIA'),
    ('MA', 'MALCON'),
    ('MC', 'MERCADO'),
    ('ML', 'MUELLE'),
    ('MN', 'MUNICIPIO'),
    ('MO', 'MONTAÑA'),
    ('MR', 'MONASTERIO'),
    ('EMS', 'MASIA'),
    ('MT', 'MONTE'),
    ('MU', 'MURO'),
    ('MZ', 'MANZANA'),
    ('NC', 'NUCLEO'),
    ('ND', 'NUDO'),
    ('NI', 'COSTANILLA'),
    ('NL', 'CANAL'),
    ('NO', 'PANTANO'),
    ('NR', 'ANDADOR'),
    ('NT', 'CANTON'),
    ('OA', 'CORRAL'),
    ('OE', 'COSTERA'),
    ('OL', 'COLONIA'),
    ('ON', 'CONVENTO'),
    ('OS', 'POSADA'),
    ('OT', 'POSTIGO'),
    ('PA', 'PARCELA'),
    ('PB', 'POBLADO'),
    ('PC', 'PARTICULAR'),
    ('PD', 'PARTIDA'),
    ('PE', 'PLAZOLETA'),
    ('PG', 'POLIGONO'),
    ('PI', 'PASADIZO'),
    ('PJ', 'PASAJE'),
    ('PL', 'PARALELA'),
    ('PM', 'PASEO MARITIMO'),
    ('PN', 'PARCELACION'),
    ('PO', 'PORTAL'),
    ('PP', 'PORTA'),
    ('PQ', 'PARROQUIA'),
    ('PR', 'PROLONGACION'),
    ('PS', 'PASEO'),
    ('PT', 'PUENTE'),
    ('PU', 'PUERTA'),
    ('PY', 'PLAYA'),
    ('PZ', 'PLAZA'),
    ('QE', 'PARQUE'),
    ('QT', 'QUINTA'),
    ('RA', 'RIBERA'),
    ('RB', 'RAMBLA'),
    ('RC', 'RINCON'),
    ('RD', 'RONDA'),
    ('RE', 'REPLACETA'),
    ('RI', 'RIO'),
    ('RL', 'RAVAL'),
    ('RM', 'RAMAL'),
    ('RN', 'RONDIN'),
    ('RO', 'ROTONDA'),
    ('RP', 'RAMPA'),
    ('RR', 'RIERA'),
    ('RS', 'RESIDENCIAL'),
    ('RT', 'RAMBLETA'),
    ('RU', 'CRUCE'),
    ('SA', 'SALON'),
    ('SB', 'SUBIDA'),
    ('SC', 'SCTOR'),
    ('SD', 'SENDA'),
    ('SE', 'SCCION'),
    ('SL', 'SOLAR'),
    ('SN', 'SENDERO'),
    ('SP', 'PASO'),
    ('SR', 'ESCALERA'),
    ('ST', 'SANTUARIO'),
    ('TA', 'COSTA'),
    ('TE', 'TRASERA'),
    ('TI', 'PORTICO'),
    ('TJ', 'ATAJO'),
    ('TL', 'TUNEL'),
    ('TN', 'TERRENOS'),
    ('TO', 'TORRENTE'),
    ('TP', 'AUTOPISTA'),
    ('TR', 'TRAVESIA'),
    ('TS', 'TRANSITO'),
    ('TV', 'TRANSVERSAL'),
    ('UE', 'PUBLO'),
    ('UR', 'URBANIZACION'),
    ('UT', 'PUERTO'),
    ('VA', 'VIAL'),
    ('VC', 'CUEVAS'),
    ('VD', 'VIADUCTO'),
    ('VI', 'VIA'),
    ('VL', 'VILLA'),
    ('VP', 'VIA PUBLICA'),
    ('VR', 'VERDA'),
    ('VV', 'VIVIENDAS'),
    ('ZN', 'ZONA')
]

MRW_DELIVERY_STATES_STATIC = {
    '00': 'customer_delivered',  # ENTREGADO
}


class MrwRequest():
    """Interface between MRW SOAP API and Odoo recordset
       Abstract MRW API Operations to connect them with Odoo

       Not all the features are implemented, but could be easily extended with
       the provided API. We leave the operations empty for future.
    """

    def __init__(self, wsdl_file, franchise, subscriber, user_id, password,
                 dept_code):
        """As the wsdl isn't public, we have to load it from local"""
        self.wsdl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            '../api/%s' % wsdl_file)
        self.franchise = franchise or ''
        self.subscriber = subscriber
        self.mrw_user_id = user_id
        self.mrw_pass = password
        self.dept_code = dept_code or ''
        self.client = Client('file:{}'.format(self.wsdl_path))

    def _recursive_asdict(self, suds_object):
        """As suds response is an special object, we convert it into
        a more usable python dict. Taken form:
        https://stackoverflow.com/a/15678861
        """
        out = {}
        for k, v in asdict(suds_object).items():
            if hasattr(v, '__keylist__'):
                out[k] = self._recursive_asdict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, '__keylist__'):
                        out[k].append(self._recursive_asdict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out

    def _get_mrw_header(self):
        mrw_ns = ('mrw', 'http://www.mrw.es/')
        mrw_franchise = Element('CodigoFranquicia', ns=mrw_ns).setText(
            self.franchise)
        mrw_subscriber = Element('CodigoAbonado', ns=mrw_ns).setText(
            self.subscriber)
        mrw_dept_code = Element('CodigoDepartamento', ns=mrw_ns).setText(
            self.dept_code)
        mrw_username = Element('UserName', ns=mrw_ns).setText(
            self.mrw_user_id)
        mrw_passwd = Element('Password', ns=mrw_ns).setText(
            self.mrw_pass)
        mrw_authinfo = Element('AuthInfo', ns=mrw_ns).append([
            mrw_franchise, mrw_subscriber, mrw_dept_code, mrw_username,
            mrw_passwd])
        return mrw_authinfo

    def _prepare_transmenvio(self, **kwargs):
        """MRW API is not very standard. Prepare parameters to pass them raw in
           the SOAP message"""
        return """
        <mrw:DatosEntrega>
            <mrw:Direccion>
                <mrw:CodigoDireccion>{entrega_codigo_direccion}</mrw:CodigoDireccion>
                <mrw:CodigoTipoVia>{entrega_tipo_via}</mrw:CodigoTipoVia>
                <mrw:Via>{entrega_via}</mrw:Via>
                <mrw:Numero>{entrega_numero}</mrw:Numero>
                <mrw:Resto>{entrega_resto}</mrw:Resto>
                <mrw:CodigoPostal>{entrega_codigo_postal}</mrw:CodigoPostal>
                <mrw:Poblacion>{entrega_poblacion}</mrw:Poblacion>
                <mrw:Estado>{entrega_estado}</mrw:Estado>
                <mrw:CodigoPais>{entrega_codigo_pais}</mrw:CodigoPais>
            </mrw:Direccion>
            <mrw:Nif>{entrega_nif}</mrw:Nif>
            <mrw:Nombre>{entrega_nombre}</mrw:Nombre>
            <mrw:Telefono>{entrega_telefono}</mrw:Telefono>
            <mrw:Contacto>{entrega_contacto}</mrw:Contacto>
            <mrw:ALaAtencionDe>{entrega_atencion}</mrw:ALaAtencionDe>
            <mrw:Horario>
                <mrw:Rangos>
                    <!--Zero or more repetitions:-->
                    <mrw:HorarioRangoRequest>
                        <mrw:Desde>{entrega_horario_rango_desde}</mrw:Desde>
                        <mrw:Hasta>{entrega_horario_rango_hasta}</mrw:Hasta>
                    </mrw:HorarioRangoRequest>
                </mrw:Rangos>
            </mrw:Horario>
            <mrw:Observaciones>{entrega_observaciones}</mrw:Observaciones>
        </mrw:DatosEntrega>
        <mrw:DatosServicio>
            <mrw:Fecha>{fecha}</mrw:Fecha>
            <mrw:Referencia>{referencia_albaran}</mrw:Referencia>
            <mrw:EnFranquicia>{en_franquicia}</mrw:EnFranquicia>
            <mrw:CodigoServicio>{codigo_servicio}</mrw:CodigoServicio>
            <mrw:DescripcionServicio>{descripcion_servicio}</mrw:DescripcionServicio>
            <mrw:Bultos/>
            <mrw:NumeroBultos>{numero_bultos}</mrw:NumeroBultos>
            <mrw:Peso>{peso}</mrw:Peso>
            <mrw:EntregaSabado>{entrega_sabado}</mrw:EntregaSabado>
            <mrw:Retorno>{retorno}</mrw:Retorno>
            <mrw:Reembolso>{reembolso}</mrw:Reembolso>
            <mrw:ImporteReembolso>{importe_reembolso}</mrw:ImporteReembolso>
        </mrw:DatosServicio>
        """.format(**kwargs)

    def _prepare_getenvios(self, **kwargs):
        return {
            'login': kwargs['login'],
            'pass': kwargs['password'],
            'codigoIdioma': kwargs['language'],
            'tipoFiltro': kwargs['filtertype'],
            'valorFiltroDesde': kwargs['filter_init'],
            'valorFiltroHasta': kwargs['filter_finish'],
            'fechaDesde': kwargs['date_from'],
            'fechaHasta': kwargs['date_until'],
            'tipoInformacion': kwargs['information_type'],
        }

    def _send_shipping(self, vals):
        """Create new shipment
        :params vals dict of needed values
        :returns dict with MRW response containing the shipping codes, labels,
        an other relevant data
        """
        xml = Raw(self._prepare_transmenvio(**vals))
        _logger.debug(xml)
        try:
            mrw_authinfo = self._get_mrw_header()
            self.client.set_options(soapheaders=(mrw_authinfo))
            res = self.client.service.TransmEnvio(xml)
        except Exception as e:
            raise UserError(_(
                'No response from server recording MRW delivery {}.\n'
                'Traceback:\n{}').format(vals.get('referencia_c', ''), e))
        # Convert result suds object to dict:
        res_mrw = self._recursive_asdict(res)
        if res_mrw['Estado'] == '0':
            # Bad Credentials:
            raise UserError(_('MRW Error\n%s') % res['Mensaje'])
        res = {
            'mrw_sent_xml': xml,
            'warnings': res_mrw['Mensaje'],
            'request_number': res_mrw['NumeroSolicitud'],
            'tracking_number': res_mrw['NumeroEnvio'],
            'response': res_mrw,
        }
        return res

    def _prepare_request_label(self, **kwargs):
        return """
        <mrw:NumeroEnvio>{numero_envio}</mrw:NumeroEnvio>
        <mrw:SeparadorNumerosEnvio></mrw:SeparadorNumerosEnvio>
        <mrw:FechaInicioEnvio>{fecha_inicio}</mrw:FechaInicioEnvio>
        <mrw:TipoEtiquetaEnvio>{tipo_etiqueta_envio}</mrw:TipoEtiquetaEnvio>
        <mrw:ReportTopMargin>{margin_top}</mrw:ReportTopMargin>
        <mrw:ReportLeftMargin>{margin_left}</mrw:ReportLeftMargin>
        """.format(**kwargs)

    def _request_label(self, vals):
        """Get delivery info recorded in MRW for the given reference
        :param str vals -- MRW dictionary data
        :returns: shipping info dict
        """
        try:
            mrw_authinfo = self._get_mrw_header()
            self.client.set_options(soapheaders=(mrw_authinfo))

            xml = Raw(self._prepare_request_label(**vals))
            res = self.client.service.EtiquetaEnvio(xml)
        except Exception as e:
            raise UserError(_(
                'MRW: No response from server getting label from ref {}.\n'
                'Traceback:\n{}').format(vals['numero_envio'], e))
        res_mrw = self._recursive_asdict(res)
        res = {
            'mrw_sent_xml': xml,
            'warnings': res_mrw.get('Mensaje', False),
            'label_file': binascii.a2b_base64(
                res_mrw.get('EtiquetaFile', '')),
            'response': res_mrw,
        }
        return res

    def _read_tracking_response(self, response):
        json_res = ZeepHelpers.serialize_object(response, dict)

        subscribers = json_res.get('Seguimiento', {}).get('Abonado', [])
        if not subscribers:
            return False
        trackings = subscribers[0].get('SeguimientoAbonado', {}).get(
            'Seguimiento', {})
        if not trackings:
            return False
        states = []
        for tracking in trackings:
            track_dict = {
                'state_code': tracking.get('Estado', False),
                'description': tracking.get('EstadoDescripcion'),
                'date': tracking.get('FechaEntrega'),
                'time': tracking.get('HoraEntrega'),
            }
            states.append(track_dict)

        return states

    def _get_tracking_states(self, vals):
        """Get just tracking states from MRW info for the given reference"""
        try:
            data = self._prepare_getenvios(**vals)
            _logger.debug(data)
            transport = ZeepTransport(timeout=10)
            zeep_client = ZeepClient(self.wsdl_path, transport=transport)
            response = zeep_client.service.GetEnvios(**data)
            _logger.debug(response)
        except Exception as e:
            raise UserError(_(
                'MRW: No response from server getting state from ref {}.\n'
                'Traceback:\n{}').format(vals['filter_init'], e))
        states = self._read_tracking_response(response)
        return states
