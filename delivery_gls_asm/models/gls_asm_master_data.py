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

GLS_ERROR_CODES = {
    "-1": """
Exception.
Important to mention that usually the D case can be solved if you remove all
unnecessary spaces, tabs and enters. Just like Shipment_Example0_Basic_IN_Compressed.xml

Examples:
  A) Timeout expired.  The timeout period elapsed prior to completion of the operation
or the server is not responding.
  B) Object reference not set to an instance of an object.
  C) Error en el nivel de transporte al enviar la solicitud al servidor. (provider:
Proveedor de TCP, error: 0 - Se ha forzado la interrupcion de una conexion existente
por el host remoto.)
  D) Unable to cast object of type 'System.Xml.XmlComment' to type
'System.Xml.XmlElement'.
""",
    "-99": "Warning, Webservices are temporarily out of service.",
    "-3": "Error, The barcode of the shipment already exists.",
    "-80": "EuroBusiness shipments. A mandatory field is missing.",
    "-81": "EuroBusiness shipments. A wrong format is transmitted in field.",
    "-82": (
        "EuroBusiness shipments. Wrong zipcode /wrong country code. Error in zip code "
        "or its format, and maybe, a bad combination of city and zip code."
    ),
    "-83": (
        "EuroBusiness shipments. GLS internal error. No free parcel number is "
        "available within the range."
    ),
    "-84": (
        "EuroBusiness shipments. GLS internal error. A parameter is missing within the "
        "configuration file of the UNI-BOX."
    ),
    "-85": "EuroBusiness shipments. Is not able to make the routing.",
    "-86": (
        "EuroBusiness shipments. GLS internal error. A needed template-file cannot be "
        "found or opened."
    ),
    "-87": "EuroBusiness shipments. GLS internal error. Duplicated sequence.",
    "-33": """
Error, Various reasons:
  - Consignee zipcode does not exist or is not from that place.
  - Refunt amount (CAD: cash on delivery) must be greater than or equal to 0.
  - Valija does not exist / eliminated.
  - Unrecognized barcode format.
  - Expedition date prior to today.
  - Number of packages can not be 0 or negative.
  - You are not authorized to record shipments from that customer.
  - Without Parcelshop store and Service's time frame.
  - Service / Service's time frame is wrong.
""",
    "-48": (
        "Error, EuroEstandar/EBP service: the number of parcels should always be 1 "
        "(<Bultos>)."
    ),
    "-49": "Error, EuroEstandar/EBP service: weight should be <= 31.5 kgs (<Peso>).",
    "-50": (
        "Error, EuroEstandar/EBP service: there can be no RCS (return stamped copy), "
        "<Pod>."
    ),
    "-51": "Error, EuroEstandar/EBP service: there can be no SWAP (<Retorno>).",
    "-52": (
        "Error, EuroEstandar/EBP service: reported a country that is not included on "
        "the service (<Destinatario>.<Pais>)."
    ),
    "-53": (
        "Error, EuroEstandar/EBP service: agency is not authorized to insert "
        "EuroEstandar/EBP service."
    ),
    "-54": (
        "Error, EuroEstandar/EBP service: The consignee mail address is required "
        "(<Destinatario>.<Email>)."
    ),
    "-55": (
        "Error, EuroEstandar/EBP service: The consignee mobile phone is required "
        "(<Destinatario>.<Movil>)."
    ),
    "-57": (
        "Error, EuroEstandar/EBP service: reported a country that is not included on "
        "the service (<Destinatario>.<Pais>)."
    ),
    "-69": "Error, I can not Channeling, wrong consignee zipcode.",
    "-70": (
        'Error, The order number already exists (<Referencia tipo="0"> or first 10 '
        'digits of the <Referencia tipo="C"> if not exists tipo="0") to this date '
        "and customer code."
    ),
    "-38": "Error, Invalid consignee phone number.",
    "-88": "Error, EBP service: some data is wrong.",
    "-96": "Error, EBP service: Sequential error.",
    "-97": (
        "Error, EuroEstandar/EBP service: <Portes> can't be \"D\", <Reembolso> can't "
        "be > 0."
    ),
    "-103": "Error, plaza solicita es null (alta).",
    "-104": "Error, plaza origen es null (alta).",
    "-106": "Error, CodCli es null (alta).",
    "-107": "Error, CodCliRed es null (alta).",
    "-108": "Error, Sender Name must be at least three characters.",
    "-109": "Error, Sender Address must be at least three characters.",
    "-110": "Error, Sender City must be at least three characters.",
    "-111": "Error, Sender Zipcode must be at least four characters.",
    "-117": "Error, los locales solo en la plaza de origen para la web.",
    "-118": "Error, customer reference is duplicated.",
    "-119": "Error, exception, uncontrolled error.",
    "-128": "Error, Consignee Name must be at least three characters.",
    "-129": "Error, Consignee Address must be at least three characters.",
    "-130": "Error, Consignee City must be at least three characters.",
    "-131": "Error, Consignee Zipcode must be at least four characters.",
    "-36": "Error, Consignee Zipcode, wrong format.",
    "-6565": "Error, Volume is incorrect, remember that the unit is m3.",
}
