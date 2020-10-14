# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _
from odoo.exceptions import UserError
import logging
import binascii
import os
_logger = logging.getLogger(__name__)

try:
    from suds.client import Client
    from suds.sax.text import Raw
    from suds.sudsobject import asdict
except (ImportError, IOError) as err:
    _logger.debug(err)


GLS_ASM_SERVICES = [
    ('1', 'COURIER'),
    ('2', 'VALIJA'),
    ('5', 'BICI'),
    ('6', 'CARGA'),
    ('7', 'RECOGIDA'),
    ('8', 'RECOGIDA CRUZADA'),
    ('9', 'DEVOLUCION'),
    ('10', 'RETORNO'),
    ('11', 'IBEX'),
    ('12', 'INTERNACIONAL EXPRESS'),
    ('13', 'INTERNACIONAL ECONOMY'),
    ('14', 'DISTRIBUCION PROPIA'),
    ('15', 'OTROS PUENTES'),
    ('16', 'PROPIO AGENTE'),
    ('17', 'RECOGIDA SIN MERCANCIA'),
    ('18', 'DISTRIBUCION  RED'),
    ('19', 'OPERACIONES RED'),
    ('20', 'CARGA MARITIMA'),
    ('21', 'GLASS'),
    ('22', 'EURO SMALL'),
    ('23', 'PREPAGO'),
    ('24', 'OPTIPLUS'),
    ('25', 'EASYBAG'),
    ('26', 'CORREO INTERNO'),
    ('27', '14H SOBRES'),
    ('28', '24H SOBRES'),
    ('29', '72H SOBRES'),
    ('30', 'ASM0830'),
    ('31', 'CAN MUESTRAS'),
    ('32', 'RC.SELLADA'),
    ('33', 'RECANALIZA'),
    ('34', 'INT PAQUET'),
    ('35', 'dPRO'),
    ('36', 'Int. WEB'),
    ('37', 'ECONOMY'),
    ('38', 'SERVICIOS RUTAS'),
    ('39', 'REC. INT'),
    ('40', 'SERVICIO LOCAL MOTO'),
    ('41', 'SERVICIO LOCAL FURGONETA'),
    ('42', 'SERVICIO LOCAL F. GRANDE'),
    ('43', 'SERVICIO LOCAL CAMION'),
    ('44', 'SERVICIO LOCAL'),
    ('45', 'RECOGIDA MEN. MOTO'),
    ('46', 'RECOGIDA MEN. FURGONETA'),
    ('47', 'RECOGIDA MEN. F.GRANDE'),
    ('48', 'RECOGIDA MEN. CAMION'),
    ('49', 'RECOGIDA MENSAJERO'),
    ('50', 'SERVICIOS ESPECIALES'),
    ('51', 'REC. INT WW'),
    ('52', 'COMPRAS'),
    ('53', 'MR1'),
    ('54', 'EURO ESTANDAR'),
    ('55', 'INTERC. EUROESTANDAR'),
    ('56', 'RECOGIDA ECONOMY'),
    ('57', 'REC. INTERCIUDAD ECONOMY'),
    ('58', 'RC. PARCEL SHOP'),
    ('59', 'ASM BUROFAX'),
    ('60', 'ASM GO'),
    ('66', 'ASMTRAVELLERS'),
    ('74', 'EUROBUSINESS PARCEL'),
    ('76', 'EUROBUSINESS SMALL PARCEL'),
]

GLS_SHIPPING_TIMES = [
    ("0", "10:00 Service"),
    ("2", "14:00 Service"),
    ("3", "BusinessParcel"),
    ("5", "SaturdayService"),
    ("7", "INTERDIA"),
    ("9", "Franja Horaria"),
    ("4", "Masivo"),
    ("10", "Maritimo"),
    ("11", "Rec. en NAVE."),
    ("13", "Ent. Pto. ASM"),
    ("18", "EconomyParcel"),
    ("19", "ParcelShop"),
]

GLS_POSTAGE_TYPE = [
    ("P", "Prepaid"),
    ("D", "Cash On Delivery"),
]

GLS_DELIVERY_STATES_STATIC = {
    "-10": "shipping_recorded_in_carrier",  # GRABADO
    "0": "shipping_recorded_in_carrier",  # MANIFESTADA
    "2": "in_transit",  # EN TRANSITO A DESTINO
    "3": "in_transit",  # EN DELEGACION DESTINO
    "20": "incidence",  # PERDIDA / ROTURA
    "5": "canceled_shipment",  # ANULADA
    "6": "in_transit",  # EN REPARTO
    "7": "customer_delivered",  # ENTREGADO
    "8": "customer_delivered",  # ENTREGA PARCIAL
    "9": "in_transit",  # ALMACENADO
    "10": "incidence",  # DEVUELTA
    "11": "incidence",  # PENDIENTE DATOS, EN  DELEGACION
    "1": "incidence",  # RETENIDA EN DELEGACION
    "91": "incidence",  # CON INCIDENCIA
    "90": "incidence",  # CERRADO DEFINITIVO
    "50": "in_transit",  # PRECONFIRMADA ENTREGA
    "51": "incidence",  # ENTREGA ANULADA (DEVUELTA)
    "12": "incidence",  # DEVUELTA AL CLIENTE
    "13": "incidence",  # POSIBLE DEVOLUCION
    "14": "incidence",  # SOLICITUD DE DEVOLUCION
    "15": "incidence",  # EN DEVOLUCION
    "16": "in_transit",  # EN DELEGACION ORIGEN
    "17": "incidence",  # DESTRUIDO POR ORDEN DEL CLIENTE
    "18": "incidence",  # RETENIDO POR ORDEN DE PAGA
    "19": "in_transit",  # EN PLATAFORMA DE DESTINO
    "21": "incidence",  # RECANALIZADA (A EXTINGUIR)
    "22": "in_transit",  # ENTREGADO EN ASM PARCELSHOP
    "25": "in_transit",  # ASM PARCELSHOP CONFIRMA RECEPCION
}


class GlsAsmRequest():
    """Interface between GLS-ASM SOAP API and Odoo recordset
       Abstract GLS-ASM API Operations to connect them with Odoo

       Not all the features are implemented, but could be easily extended with
       the provided API. We leave the operations empty for future.
    """

    def __init__(self, uidcustomer=None):
        """As the wsdl isn't public, we have to load it from local"""
        wsdl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            '../api/gls_asm_api.wsdl')
        self.uidcustomer = uidcustomer or ""
        self.client = Client("file:{}".format(wsdl_path))

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

    def _prepare_cancel_shipment_docin(self, **kwargs):
        """ASM API is not very standard. Prepare parameters to pass them raw in
           the SOAP message"""
        return """
            <Servicios uidcliente="{uidcustomer}"
                       xmlns="http://www.asmred.com/">
                <Envio referencia="{referencia}" />
            </Servicios>
        """.format(**kwargs)

    def _prepare__get_manifest_docin(self, **kwargs):
        """ASM API is not very standard. Prepare parameters to pass them raw in
           the SOAP message"""
        return """
            <Servicios uidcliente="{uidcustomer}"
                       xmlns="http://www.asmred.com/">
                <FechaDesde>{date_from}</FechaDesde>
                <FechaHasta></FechaHasta>
            </Servicios>
        """.format(**kwargs)

    def _prepare_send_shipping_docin(self, **kwargs):
        """ASM API is not very standard. Prepare parameters to pass them raw in
           the SOAP message"""
        return """
            <Servicios uidcliente="{uidcustomer}"
                       xmlns="http://www.asmred.com/">
                <Envio codbarras="">
                    <Fecha>{fecha}</Fecha>
                    <Portes>{portes}</Portes>
                    <Servicio>{servicio}</Servicio>
                    <Horario>{horario}</Horario>
                    <Bultos>{bultos}</Bultos>
                    <Peso>{peso}</Peso>
                    <Volumen>{volumen}</Volumen>
                    <Declarado>{declarado}</Declarado>
                    <DNINomb>{dninomb}</DNINomb>
                    <FechaPrevistaEntrega>{fechaentrega}</FechaPrevistaEntrega>
                    <Retorno>{retorno}</Retorno>
                    <Pod>{pod}</Pod>
                    <PODObligatorio>{podobligatorio}</PODObligatorio>
                    <Remite>
                        <Plaza>{remite_plaza}</Plaza>
                        <Nombre>{remite_nombre}</Nombre>
                        <Direccion>{remite_direccion}</Direccion>
                        <Poblacion>{remite_poblacion}</Poblacion>
                        <Provincia>{remite_provincia}</Provincia>
                        <Pais>{remite_pais}</Pais>
                        <CP>{remite_cp}</CP>
                        <Telefono>{remite_telefono}</Telefono>
                        <Movil>{remite_movil}</Movil>
                        <Email>{remite_email}</Email>
                        <Departamento>{remite_departamento}</Departamento>
                        <NIF>{remite_nif}</NIF>
                        <Observaciones>{remite_observaciones}</Observaciones>
                    </Remite>
                    <Destinatario>
                        <Codigo>{destinatario_codigo}</Codigo>
                        <Plaza>{destinatario_plaza}</Plaza>
                        <Nombre>{destinatario_nombre}</Nombre>
                        <Direccion>{destinatario_direccion}</Direccion>
                        <Poblacion>{destinatario_poblacion}</Poblacion>
                        <Provincia>{destinatario_provincia}</Provincia>
                        <Pais>{destinatario_pais}</Pais>
                        <CP>{destinatario_cp}</CP>
                        <Telefono>{destinatario_telefono}</Telefono>
                        <Movil>{destinatario_movil}</Movil>
                        <Email>{destinatario_email}</Email>
                        <Observaciones>
                            {destinatario_observaciones}
                        </Observaciones>
                        <ATT>{destinatario_att}</ATT>
                        <Departamento>{destinatario_departamento}</Departamento>
                        <NIF>{destinatario_nif}</NIF>
                    </Destinatario>
                    <Referencias>
                        <Referencia tipo="C">{referencia_c}</Referencia>
                        <Referencia tipo="0">{referencia_0}</Referencia>
                    </Referencias>
                    <Importes>
                        <Debidos>{importes_debido}</Debidos>
                        <Reembolso>{importes_reembolso}</Reembolso>
                    </Importes>
                    <Seguro tipo="{seguro}">
                        <Descripcion>{seguro_descripcion}</Descripcion>
                        <Importe>{seguro_importe}</Importe>
                    </Seguro>
                    <DevuelveAdicionales>
                        <PlazaDestino />
                        <Etiqueta tipo="{etiqueta}" />
                        <EtiquetaDevolucion tipo="{etiqueta_devolucion}" />
                    </DevuelveAdicionales>
                    <DevolverDatosASMDestino />
                    <Cliente>
                        <Codigo>{cliente_codigo}</Codigo>
                        <Plaza>{cliente_plaza}</Plaza>
                        <Agente>{cliente_agente}</Agente>
                    </Cliente>
                </Envio>
            </Servicios>
        """.format(**kwargs)

    def _send_shipping(self, vals):
        """Create new shipment
        :params vals dict of needed values
        :returns dict with GLS response containing the shipping codes, labels,
        an other relevant data
        """
        vals.update({
            'uidcustomer': self.uidcustomer,
        })
        xml = Raw(self._prepare_send_shipping_docin(**vals))
        _logger.debug(xml)
        try:
            res = self.client.service.GrabaServicios(docIn=xml)
        except Exception as e:
            raise UserError(_(
                "No response from server recording GLS delivery {}.\n"
                "Traceback:\n{}").format(vals.get("referencia_c", ""), e))
        # Convert result suds object to dict and set the root conveniently
        # GLS API Errors have codes below 0 so we have to
        # convert to int as well
        res = self._recursive_asdict(res)['Servicios']['Envio']
        res["gls_sent_xml"] = xml
        _logger.debug(res)
        res["_return"] = int(res["Resultado"]["_return"])
        if res["_return"] < 0:
            raise UserError(_(
                "GLS returned an error trying to record the shipping for {}.\n"
                "Error:\n{}").format(
                    vals.get("referencia_c", ""),
                    res.get("Errores", {}).get(
                        "Error", "code {}".format(res["_return"]))))
        if res.get('Etiquetas', {}).get('Etiqueta', {}).get("value"):
            res["gls_label"] = (
                binascii.a2b_base64(res["Etiquetas"]["Etiqueta"]["value"]))
        return res

    def _get_delivery_info(self, reference=False):
        """Get delivery info recorded in GLS for the given reference
        :param str reference -- GLS tracking number
        :returns: shipping info dict
        """
        try:
            res = self.client.service.GetExpCli(
                codigo=reference, uid=self.uidcustomer)
            _logger.debug(res)
        except Exception as e:
            raise UserError(_(
                "GLS: No response from server getting state from ref {}.\n"
                "Traceback:\n{}").format(reference, e))
        res = self._recursive_asdict(res)
        return res

    def _get_tracking_states(self, reference=False):
        """Get just tracking states from GLS info for the given reference
        :param str reference -- GLS tracking number
        :returns: list of tracking states
        """
        res = self._get_delivery_info(reference)
        res = res.get("expediciones", {}).get("exp", {}).get(
            "tracking_list", {}).get("tracking", [])
        # If there's just one state, we'll get a single dict, otherwise we
        # get a list of dicts
        if isinstance(res, dict):
            return [res]
        return res

    def _shipping_label(self, reference=False):
        """Get shipping label for the given ref
        :param str reference -- public shipping reference
        :returns: base64 with pdf label or False
        """
        try:
            res = self.client.service.EtiquetaEnvio(reference, 'PDF')
            _logger.debug(res)
        except Exception as e:
            raise UserError(_(
                "GLS: No response from server printing label with ref {}.\n"
                "Traceback:\n{}").format(reference, e))
        res = self._recursive_asdict(res)
        label = res.get("base64Binary")
        return label and binascii.a2b_base64(str(label[0]))

    def _cancel_shipment(self, reference=False):
        """Cancel shipment for a given reference
        :param str reference -- shipping reference to cancel
        :returns: dict -- result of operation with format
        {
            'value': str - response message,
            '_return': int  - response status
        }
        Possible response values:
             0 -> Expedición anulada
            -1 -> No existe envío
            -2 -> Tiene tracking operativo
        """
        xml = Raw(self._prepare_cancel_shipment_docin(
            uidcustomer=self.uidcustomer, referencia=reference))
        _logger.debug(xml)
        try:
            response = self.client.service.Anula(docIn=xml)
            _logger.debug(response)
        except Exception as e:
            _logger.error(
                "No response from server canceling GLS ref {}.\n"
                "Traceback:\n{}".format(reference, e))
            return {}
        response = self._recursive_asdict(response.Servicios.Envio.Resultado)
        response["gls_sent_xml"] = xml
        response["_return"] = int(response["_return"])
        return response

    def _get_manifest(self, date_from):
        """Get shipping manifest for a given range date
        :param str date_from -- date in format "%d/%m&Y"
        :returns: list of dicts with format
            {
                'codplaza_pag': 771, 'codcli': 601, 'cliente': Pruebas WS
                'codplaza_org': 771, 'codexp': 468644476, 'codservicio': 74,
                'servicio': EUROBUSINESS PARCEL, 'codhorario': 3,
                'horario': BusinessParcel, 'codestado': -10, 'estado': GRABADO,
                'bultos': 1, 'kgs': 7,0, 'nombre_dst': TEST USER,
                'calle_dst': direccion, 'localidad_dst': Fontenay-Trésigny,
                'cp_dst': 77610, 'departamento_dst': , 'pais_dst': FR,
            }
        """
        xml = Raw(self._prepare__get_manifest_docin(
            uidcustomer=self.uidcustomer, date_from=date_from))
        _logger.debug(xml)
        try:
            res = self.client.service.GetManifiesto(docIn=xml)
            _logger.debug(res)
        except Exception as e:
            raise UserError(_(
                "No response from server getting manifisto for GLS.\n"
                "Traceback:\n{}").format(e))
        res = self._recursive_asdict(res.Servicios.Envios).get("Envio", [])
        return res
