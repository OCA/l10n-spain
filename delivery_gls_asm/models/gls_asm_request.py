# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import binascii
import logging
import os

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from suds.client import Client
    from suds.sax.text import Raw
    from suds.sudsobject import asdict
except (ImportError, IOError) as err:
    _logger.debug(err)


GLS_ASM_SERVICES = [
    ("1", "COURIER"),
    ("2", "VALIJA"),
    ("5", "BICI"),
    ("6", "CARGA"),
    ("7", "RECOGIDA"),
    ("8", "RECOGIDA CRUZADA"),
    ("9", "DEVOLUCION"),
    ("10", "RETORNO"),
    ("11", "IBEX"),
    ("12", "INTERNACIONAL EXPRESS"),
    ("13", "INTERNACIONAL ECONOMY"),
    ("14", "DISTRIBUCION PROPIA"),
    ("15", "OTROS PUENTES"),
    ("16", "PROPIO AGENTE"),
    ("17", "RECOGIDA SIN MERCANCIA"),
    ("18", "DISTRIBUCION  RED"),
    ("19", "OPERACIONES RED"),
    ("20", "CARGA MARITIMA"),
    ("21", "GLASS"),
    ("22", "EURO SMALL"),
    ("23", "PREPAGO"),
    ("24", "OPTIPLUS"),
    ("25", "EASYBAG"),
    ("26", "CORREO INTERNO"),
    ("27", "14H SOBRES"),
    ("28", "24H SOBRES"),
    ("29", "72H SOBRES"),
    ("30", "ASM0830"),
    ("31", "CAN MUESTRAS"),
    ("32", "RC.SELLADA"),
    ("33", "RECANALIZA"),
    ("34", "INT PAQUET"),
    ("35", "dPRO"),
    ("36", "Int. WEB"),
    ("37", "ECONOMY"),
    ("38", "SERVICIOS RUTAS"),
    ("39", "REC. INT"),
    ("40", "SERVICIO LOCAL MOTO"),
    ("41", "SERVICIO LOCAL FURGONETA"),
    ("42", "SERVICIO LOCAL F. GRANDE"),
    ("43", "SERVICIO LOCAL CAMION"),
    ("44", "SERVICIO LOCAL"),
    ("45", "RECOGIDA MEN. MOTO"),
    ("46", "RECOGIDA MEN. FURGONETA"),
    ("47", "RECOGIDA MEN. F.GRANDE"),
    ("48", "RECOGIDA MEN. CAMION"),
    ("49", "RECOGIDA MENSAJERO"),
    ("50", "SERVICIOS ESPECIALES"),
    ("51", "REC. INT WW"),
    ("52", "COMPRAS"),
    ("53", "MR1"),
    ("54", "EURO ESTANDAR"),
    ("55", "INTERC. EUROESTANDAR"),
    ("56", "RECOGIDA ECONOMY"),
    ("57", "REC. INTERCIUDAD ECONOMY"),
    ("58", "RC. PARCEL SHOP"),
    ("59", "ASM BUROFAX"),
    ("60", "ASM GO"),
    ("66", "ASMTRAVELLERS"),
    ("74", "EUROBUSINESS PARCEL"),
    ("76", "EUROBUSINESS SMALL PARCEL"),
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

GLS_POSTAGE_TYPE = [("P", "Prepaid"), ("D", "Cash On Delivery")]

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

GLS_SHIPMENT_TYPE_STATES = {
    "-10": "recorded",  # GRABADO
    "0": "manifested",  # MANIFESTADA
    "2": "transit",  # EN TRANSITO A DESTINO
    "3": "agency_transit",  # EN DELEGACION DESTINO
    "20": "closed",  # CERRADO POR SINIESTRO
    "5": "cancel",  # ANULADA
    "6": "shipping",  # EN REPARTO
    "7": "delivered",  # ENTREGADO
    "8": "partially_delivered",  # ENTREGA PARCIAL
    "9": "warehouse",  # ALMACENADO
    "10": "return_agency",  # DEVUELTA
    "11": "pending",  # PENDIENTE DATOS. EN DELEGACIÓN
    "1": "held",  # PENDIENTE AUTORIZACIÓN
    "91": "incidence",  # CON INCIDENCIA
    "90": "closed_final",  # CERRADO DEFINITIVO
    "50": "preconfirmed",  # PRECONFIRMADA ENTREGA
    "51": "cancel_returned",  # ENTREGA ANULADA (DEVUELTA)
    "12": "return_customer",  # DEVUELTA AL CLIENTE
    "13": "possible_return",  # POSIBLE DEVOLUCIÓN
    "14": "requested_return",  # SOLICITUD DE DEVOLUCIÓN
    "15": "returning",  # EN DEVOLUCIÓN
    "16": "origin",  # EN DELEGACIÓN ORIGEN
    "17": "destroyed",  # DESTRUIDO POR ORDEN DEL CLIENTE
    "18": "held_order",  # RETENIDO POR ORDEN DE PAGA
    "19": "in_platform",  # EN PLATAFORMA DE DESTINO
    "21": "extinguished",  # RECANALIZADA (A EXTINGUIR)
    "22": "parcelshop",  # ENTREGADO EN ASM PARCELSHOP,
    "25": "parcelshop_confirm",  # ASM PARCELSHOP CONFIRMA RECEPCIÓN
}

GLS_PICKUP_STATES_STATIC = {
    "0": "canceled_shipment",  # ANULADA
    "1": "shipping_recorded_in_carrier",  # SOLICITADA
    "2": "customer_delivered",  # REALIZADA CON ÉXITO
    "3": "in_transit",  # NO REALIZADA
    "4": "customer_delivered",  # RECIBIDA
    "5": "incidence",  # REALIZADA CON INCIDENCIA
    "6": "in_transit",  # RECOGIDO EN CLIENTE
    "7": "in_transit",  # RECEPCIONADA EN AGENCIA
    "9": "shipping_recorded_in_carrier",  # ASIGNADA
    "10": "shipping_recorded_in_carrier",  # A PRECONFIRMAR
    "11": "shipping_recorded_in_carrier",  # PENDIENTE GESTIÓN
    "12": "customer_delivered",  # CERRADO
    "13": "shipping_recorded_in_carrier",  # PENDIENTE AUTORIZACIÓN
    "20": "customer_delivered",  # CERRADO DEFINITIVO
}

GLS_PICKUP_TYPE_STATES = {
    "0": "cancel",  # ANULADA
    "1": "recorded",  # SOLICITADA
    "2": "done",  # REALIZADA CON ÉXITO
    "3": "not_done",  # NO REALIZADA
    "4": "received",  # RECIBIDA
    "5": "incidence",  # REALIZADA CON INCIDENCIA
    "6": "picked_up_customer",  # RECOGIDO EN CLIENTE
    "7": "picked_up_agency",  # RECEPCIONADA EN AGENCIA
    "9": "assigned",  # ASIGNADA
    "10": "preconfirm",  # A PRECONFIRMAR
    "11": "pending",  # PENDIENTE GESTIÓN
    "12": "closed",  # CERRADO
    "13": "pending_auth",  # PENDIENTE AUTORIZACIÓN
    "20": "closed_final",  # CERRADO DEFINITIVO
}

GLS_SHIPMENT_ERROR_CODES = {
    36: "Error, Consignee Zipcode, wrong format.",
    38: "Error, Invalid consignee phone number.",
    -36: "Error, Consignee Zipcode, wrong format.",
    -38: "Error, Invalid consignee phone number.",
    -1: (
        "Exception. Timeout expired."
        "Se ha forzado la interrupcion de una conexion existente por el host remoto."
    ),
    -3: "Error, The barcode of the shipment already exists.",
    -33: """Error, Various reasons:
        Cp destino no existe o no es de esa plaza
        El reembolso debe ser mayor o igual a 0
        Este contrato de valija no existe/esta dado de baja
        Formato de codigo de barras no reconocido
        Fecha expedición anterior a hoy
        Los bultos no pueden ser 0 o negativos
        No estas autorizado a grabar envíos de ese cliente
        Sin tienda ps y horario ps
        El servicio / horario es incorrecto""",
    -48: "Error, EuroEstandar/EBP service: the number of parcels should always be 1.",
    -49: "Error, EuroEstandar/EBP service: weight should be <= 31.5 kgs (<Peso>).",
    -50: "Error, EuroEstandar/EBP service: there can be no RCS (return stamped copy).",
    -51: "Error, EuroEstandar/EBP service: there can be no SWAP (<Retorno>).",
    -52: (
        "Error, EuroEstandar/EBP service:"
        "reported a country that is not included on the service."
    ),
    -53: (
        "Error, EuroEstandar/EBP service:"
        "agency is not authorized to insert EuroEstandar/EBP service."
    ),
    -54: (
        "Error, EuroEstandar/EBP service:"
        "The consignee mail address is required (<Destinatario>.<Email>)."
    ),
    -55: (
        "Error, EuroEstandar/EBP service:"
        "The consignee mobile phone is required (<Destinatario>.<Movil>)."
    ),
    -57: (
        "Error, EuroEstandar/EBP service:"
        "reported a country that is not included on the service (<Destinatario>.<Pais>)."
    ),
    -69: "Error, I can not Channeling, wrong consignee zipcode.",
    -70: "Error, The order number already exists to this date and customer code.",
    -80: "EuroBusiness shipments. A mandatory field is missing.",
    -81: "EuroBusiness shipments. A wrong format is transmitted in field.",
    -82: (
        "EuroBusiness shipments."
        "Wrong zipcode /wrong country code."
        "Error in zip code or its format, "
        "and maybe a bad combination of city and zip code."
    ),
    -83: (
        "EuroBusiness shipments."
        "GLS internal error."
        "No free parcel number is available within the range."
    ),
    -84: (
        "EuroBusiness shipments."
        "GLS internal error."
        "A parameter is missing within the configuration file of the UNI-BOX."
    ),
    -85: "EuroBusiness shipments. Is not able to make the routing.",
    -86: (
        "EuroBusiness shipments."
        "GLS internal error."
        "A needed template-file cannot be found or opened."
    ),
    -87: "EuroBusiness shipments. GLS internal error. Duplicated sequence.",
    -88: "EuroBusiness shipments. Other errors.",
    -96: "Error, EBP service: Sequential error.",
    -97: (
        "Error, EuroEstandar/EBP service:"
        "<Portes> can't be 'D', <Reembolso> can't be > 0."
    ),
    -99: "Warning, Webservices are temporarily out of service.",
    -103: "Error, plaza solicita es null (alta).",
    -104: "Error, plaza origen es null (alta).",
    -106: "Error, CodCli es null (alta).",
    -107: "Error, CodCliRed es null (alta).",
    -108: "Error, Sender Name must be at least three characters.",
    -109: "Error, Sender Address must be at least three characters.",
    -110: "Error, Sender City must be at least three characters.",
    -111: "Error, Sender Zipcode must be at least four characters.",
    -117: "Error, los locales solo en la plaza de origen para la web.",
    -118: "Error, customer reference is duplicated.",
    -119: "Error, exception, uncontrolled error.",
    -128: "Error, Consignee Name must be at least three characters.",
    -129: "Error, Consignee Address must be at least three characters.",
    -130: "Error, Consignee City must be at least three characters.",
    -131: "Error, Consignee Zipcode must be at least four characters.",
    -6565: "Error, Volume is incorrect, remember that the unit is m3.",
}

GLS_PICKUP_ERROR_CODES = {
    -1: "Connection exception",
    -103: "Impossible get the requesting agency",
    -104: "Impossible get the origin agency.",
    -105: "Collection date is empty o not informed.",
    -106: "Impossible get the customer code (CodCli).",
    -107: "Impossible get the CodCliRed.",
    -108: "Collection name is empty or not informed.",
    -109: "Collection Address name is empty or not informed.",
    -110: "Collection City name is empty or not informed.",
    -111: "Collection Zipcode is empty or not informed.",
    -112: "Codsolicitud of agency is not valid.",
    -113: "Generic zipcodes are not allowed.",
    -114: "Collection interval must be greater than 2 hours.",
    -115: "Minimum collection time is 8h.",
    -116: "Maximum collection time is 22h.",
    -117: "Los locales solo en la plaza de origen para la web.",
    -118: "Customer reference is duplicated.",
    -119: "Zonzoo no puede recoger en islas Portugal.",
    -120: "Zipcode of consignee is incorrect.",
    -122: "Login not exists or is deleted.",
    -123: "Don't have permissions to insert on this agency.",
    -125: "Can not ask a collect on festive.",
    -126: (
        "When country is not Spain (34) the Phone and Celullar are mandatory"
        "(tags <Telefono> and <Movil> inside <RecogerEn>)."
    ),
    -128: (
        "It is mandatory to inform the Telephone or Email "
        "where GLS must to collect (<RecogerEn>.<Telefono>, <RecogerEn>.<Movil> "
        "or <RecogerEn>.<Email>)."
    ),
    -303: "Currency amounts must be allways greater than 0.",
    -402: (
        "If Amount of insured goods > 0 (in Seguro), "
        "then tipo and descripcion are mandatory."
    ),
    -504: (
        "Impossible get the last mile agency, "
        "probably the consignee zipcode is wrong or not exists."
    ),
    -505: "Consignee name is not informed.",
    -506: "Consignee address is not informed.",
    -507: "Consignee city is not informed.",
    -508: "Consignee zipcode is not informed.",
    -602: "The reference must be informed.",
    -603: "Shipment References, tipo not exists.",
    -676: "Collection Zipcode is wrong, not exists.",
}


class GlsAsmRequest:
    """Interface between GLS-ASM SOAP API and Odoo recordset
    Abstract GLS-ASM API Operations to connect them with Odoo

    Not all the features are implemented, but could be easily extended with
    the provided API. We leave the operations empty for future.
    """

    def __init__(self, uidcustomer=None):
        """As the wsdl isn't public, we have to load it from local"""
        wsdl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../api/gls_asm_api.wsdl"
        )
        self.uidcustomer = uidcustomer or ""
        self.client = Client("file:{}".format(wsdl_path))

    def _recursive_asdict(self, suds_object):
        """As suds response is an special object, we convert it into
        a more usable python dict. Taken form:
        https://stackoverflow.com/a/15678861
        """
        out = {}
        for k, v in asdict(suds_object).items():
            if hasattr(v, "__keylist__"):
                out[k] = self._recursive_asdict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, "__keylist__"):
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
        """.format(
            **kwargs
        )

    def _prepare_cancel_pickup_docin(self, **kwargs):
        return """
            <Servicios uidcliente="{uidcustomer}"
                       xmlns="http://www.asmred.com/">
                <Recogida referencia="{referencia}" />
            </Servicios>
        """.format(
            **kwargs
        )

    def _prepare__get_manifest_docin(self, **kwargs):
        """ASM API is not very standard. Prepare parameters to pass them raw in
        the SOAP message"""
        return """
            <Servicios uidcliente="{uidcustomer}"
                       xmlns="http://www.asmred.com/">
                <FechaDesde>{date_from}</FechaDesde>
                <FechaHasta></FechaHasta>
            </Servicios>
        """.format(
            **kwargs
        )

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
        """.format(
            **kwargs
        )

    def _prepare_send_pickup_docin(self, **kwargs):
        """ASM API is not very standard. Prepare parameters to pass them raw in
        the SOAP message"""
        return """
            <Servicios uidcliente="{uidcustomer}"
                       xmlns="http://www.asmred.com/">
                <Recogida codrecogida="">
                    <Horarios>
                        <Fecha dia="{fecha}">
                            <Horario desde="09:00" hasta="18:00" />
                        </Fecha>
                    </Horarios>
                    <RecogerEn>
                        <Nombre>{remite_nombre}</Nombre>
                        <Direccion>{remite_direccion}</Direccion>
                        <Poblacion>{remite_poblacion}</Poblacion>
                        <Provincia>{remite_provincia}</Provincia>
                        <Pais>{remite_pais}</Pais>
                        <CP>{remite_cp}</CP>
                        <Telefono>{remite_telefono}</Telefono>
                        <Movil>{remite_movil}</Movil>
                        <Email>{remite_email}</Email>
                        <Contacto></Contacto>
                    </RecogerEn>
                    <Entregas>
                        <Envio>
                            <FechaPrevistaEntrega>{fechaentrega}</FechaPrevistaEntrega>
                            <Portes>{portes}</Portes>
                            <Servicio>{servicio}</Servicio>
                            <Horario>{horario}</Horario>
                            <Bultos>{bultos}</Bultos>
                            <Peso>{peso}</Peso>
                            <Destinatario>
                                <Nombre>{destinatario_nombre}</Nombre>
                                <Direccion>{destinatario_direccion}</Direccion>
                                <Poblacion>{destinatario_poblacion}</Poblacion>
                                <Provincia>{destinatario_provincia}</Provincia>
                                <Pais>{destinatario_pais}</Pais>
                                <CP>{destinatario_cp}</CP>
                                <Telefono>{destinatario_telefono}</Telefono>
                                <Movil>{destinatario_movil}</Movil>
                                <Email>{destinatario_email}</Email>
                                <Observaciones>{observaciones}</Observaciones>
                            </Destinatario>
                        </Envio>
                    </Entregas>
                    <Referencias>
                        <Referencia tipo="C">{referencia_c}</Referencia>
                        <Referencia tipo="A">{referencia_a}</Referencia>
                    </Referencias>
                </Recogida>
            </Servicios>
        """.format(
            **kwargs
        )

    def _send_shipping(self, vals):
        """Create new shipment
        :params vals dict of needed values
        :returns dict with GLS response containing the shipping codes, labels,
        an other relevant data
        """
        vals.update({"uidcustomer": self.uidcustomer})
        xml = Raw(self._prepare_send_shipping_docin(**vals))
        _logger.debug(xml)
        try:
            res = self.client.service.GrabaServicios(docIn=xml)
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording GLS delivery {}.\n"
                    "Traceback:\n{}"
                ).format(vals.get("referencia_c", ""), e)
            )
        # Convert result suds object to dict and set the root conveniently
        # GLS API Errors have codes below 0 so we have to
        # convert to int as well
        res = self._recursive_asdict(res)["Servicios"]["Envio"]
        res["gls_sent_xml"] = xml
        _logger.debug(res)
        res["_return"] = int(res["Resultado"]["_return"])
        if res["_return"] < 0:
            raise UserError(
                _(
                    "GLS returned an error trying to record the shipping for {}.\n"
                    "Error:\n{}"
                ).format(
                    vals.get("referencia_c", ""),
                    GLS_SHIPMENT_ERROR_CODES.get(res["_return"], res["_return"]),
                )
            )
        if res.get("Etiquetas", {}).get("Etiqueta", {}).get("value"):
            res["gls_label"] = binascii.a2b_base64(
                res["Etiquetas"]["Etiqueta"]["value"]
            )
        return res

    def _send_pickup(self, vals):
        """Create new pickup
        :params vals dict of needed values
        :returns dict with GLS response containing the shipping codes, labels,
        an other relevant data
        """
        vals.update({"uidcustomer": self.uidcustomer})
        xml = Raw(self._prepare_send_pickup_docin(**vals))
        _logger.debug(xml)
        try:
            res = self.client.service.GrabaServicios(docIn=xml)
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording GLS delivery {}.\n"
                    "Traceback:\n{}"
                ).format(vals.get("referencia_c", ""), e)
            )
        # Convert result suds object to dict and set the root conveniently
        # GLS API Errors have codes below 0 so we have to
        # convert to int as well
        res = self._recursive_asdict(res)["Servicios"]["Recogida"]
        res["gls_sent_xml"] = xml
        _logger.debug(res)
        res["_return"] = int(res["Resultado"]["_return"])
        if res["_return"] < 0:
            raise UserError(
                _(
                    "GLS returned an error trying to record the shipping for {}.\n"
                    "Error:\n{}"
                ).format(
                    vals.get("referencia_c", ""),
                    GLS_PICKUP_ERROR_CODES.get(res["_return"], res["_return"]),
                )
            )
        return res

    def _get_delivery_info(self, reference=False):
        """Get delivery info recorded in GLS for the given reference
        :param str reference -- GLS tracking number
        :returns: shipping info dict
        """
        try:
            res = self.client.service.GetExpCli(codigo=reference, uid=self.uidcustomer)
            _logger.debug(res)
        except Exception as e:
            raise UserError(
                _(
                    "GLS: No response from server getting state from ref {}.\n"
                    "Traceback:\n{}"
                ).format(reference, e)
            )
        res = self._recursive_asdict(res)
        return res

    def _get_pickup_info(self, reference=False):
        xml = Raw(
            """
            <Servicios uidcliente="{uidcustomer}" xmlns="http://www.asmred.com/">
                <Recogida codrecogida="{codrecogida}" />
            </Servicios>
        """.format(
                uidcustomer=self.uidcustomer, codrecogida=reference
            )
        )
        res = self.client.service.Tracking(docIn=xml)
        _logger.debug(res)
        return self._recursive_asdict(res)

    def _get_tracking_states(self, reference=False):
        """Get just tracking states from GLS info for the given reference
        :param str reference -- GLS tracking number
        :returns: list of tracking states
        """
        res = self._get_delivery_info(reference)
        res = (res.get("expediciones") or {}).get("exp", {})
        return res

    def _get_pickup_tracking_states(self, reference=False):
        res = self._get_pickup_info(reference)
        res = (
            res.get("Servicios", {})
            .get("Recogida", {})
            .get("Tracking", {})
            .get("TrackingCliente", {})
        )
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
            res = self.client.service.EtiquetaEnvio(reference, "PDF")
            _logger.debug(res)
        except Exception as e:
            raise UserError(
                _(
                    "GLS: No response from server printing label with ref {}.\n"
                    "Traceback:\n{}"
                ).format(reference, e)
            )
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
        xml = Raw(
            self._prepare_cancel_shipment_docin(
                uidcustomer=self.uidcustomer, referencia=reference
            )
        )
        _logger.debug(xml)
        try:
            response = self.client.service.Anula(docIn=xml)
            _logger.debug(response)
        except Exception as e:
            _logger.error(
                "No response from server canceling GLS ref {}.\n"
                "Traceback:\n{}".format(reference, e)
            )
            return {}
        response = self._recursive_asdict(response.Servicios.Envio.Resultado)
        response["gls_sent_xml"] = xml
        response["_return"] = int(response["_return"])
        return response

    def _cancel_pickup(self, reference=False):
        """Cancel shipment for a given reference
        :param str reference -- shipping reference to cancel
        :returns: dict -- result of operation with format
        {
            'value': str - response message,
            '_return': int  - response status
        }
        Possible response values:
             0 -> Recogida anulada
            -1 -> No existe recogida
            -2 -> Tiene tracking operativo
        """
        xml = Raw(
            self._prepare_cancel_pickup_docin(
                uidcustomer=self.uidcustomer, referencia=reference
            )
        )
        _logger.debug(xml)
        try:
            response = self.client.service.Anula(docIn=xml)
            _logger.debug(response)
        except Exception as e:
            _logger.error(
                "No response from server canceling GLS ref {}.\n"
                "Traceback:\n{}".format(reference, e)
            )
            return {}
        response = self._recursive_asdict(response.Servicios.Recogida.Resultado)
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
        xml = Raw(
            self._prepare__get_manifest_docin(
                uidcustomer=self.uidcustomer, date_from=date_from
            )
        )
        _logger.debug(xml)
        try:
            res = self.client.service.GetManifiesto(docIn=xml)
            _logger.debug(res)
        except Exception as e:
            raise UserError(
                _(
                    "No response from server getting manifisto for GLS.\n"
                    "Traceback:\n{}"
                ).format(e)
            )
        res = self._recursive_asdict(res.Servicios.Envios).get("Envio", [])
        return res
