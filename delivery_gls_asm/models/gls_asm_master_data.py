# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
    ("96", "BUSINESS PARCEL"),
]

GLS_SHIPPING_TIMES = [
    ("0", "Express 10:00"),
    ("2", "Express 14:00"),
    ("3", "Express 19:00"),
    ("5", "SaturdayService"),
    ("7", "INTERDIA"),
    ("9", "Franja Horaria"),
    ("4", "Masivo"),
    ("10", "Maritimo"),
    ("11", "Rec. en agencia"),
    ("13", "Ent. Pto. ASM"),
    ("16", "Economy"),
    ("17", "Express"),
    ("18", "Entrega 24-48h (serv. 96) o 48h (serv. 37)"),
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

GLS_TRACKING_LINKS = {
    "ASM": (
        "http://www.asmred.com/extranet/public/ExpedicionASM.aspx?codigo={}&cpDst={}"
    ),
    "INT": (
        "https://www.gls-spain.es/en/receiving-parcels/shipping-tracking/"
        "?match={}&international=1"
    ),
    "INT_PT": (
        "https://www.gls-portugal.pt/pt/seguimiento-envio/?match={}&international=1"
    ),
}
