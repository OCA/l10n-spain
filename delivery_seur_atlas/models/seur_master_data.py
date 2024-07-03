# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
SERVICE_CODES = [
    ("1", "SEUR 24"),
    ("3", "SEUR 10"),
    ("5", "Mismo día"),
    ("7", "Courier"),
    ("9", "SEUR 13:30"),
    ("13", "SEUR 72"),
    ("15", "SEUR 48"),
    ("17", "Marítimo"),
    ("19", "NETEXPRESS"),
    ("31", "Entrega particular"),
    ("77", "Classic"),
    ("83", "SEUR 8:30"),
]

PRODUCT_CODES = [
    ("2", "Estandar"),
    ("4", "Multipack"),
    ("6", "Multi Box"),
    ("18", "Frio"),
    ("48", "Seur 24 Pickup"),
    ("52", "Multi Doc"),
    ("54", "Documentos"),
    ("70", "Internacional T"),
    ("72", "Internacional A"),
    ("76", "Classic"),
    ("86", "Ecommerce Return 2home"),
    ("88", "Ecommerce Return 2shop"),
    ("104", "Crossborder Netexpres Internacional"),
    ("108", "Courier Muestras"),
    ("116", "Classic Multiparcel"),
    ("118", "Vino"),
    ("122", "Neumaticos B2B"),
    ("124", "Neumaticos B2C"),
]

TRACKING_STATES_MAP = {
    "II716": "incidence",  # ERROR EN BULTO
    "LC001": "in_transit",  # EN REPARTO CONFIRMADO
    "LC002": "in_transit",  # EN REPARTO CONFIRMADO STR
    "LC003": "in_transit",  # EN REPARTO CONFIRMADO - BULTOS
    "LC004": "in_transit",  # EN REPARTO CONFIRMADO  OTROS
    "LC005": "in_transit",  # EN REPARTO CONFIRMADO OMR
    "LC006": "in_transit",  # EN RPTO CONFIRMAD POR RELACION
    "LC014": "in_transit",  # CONFIRMADO PARA ENLACE
    "LC101": "in_transit",  # Salió de reparto a una ISLA
    "LC103": "in_transit",  # CONFIRMADA A REPARTO EN ISLA
    "LC845": "in_transit",  # FINAL DE RETENCION
    "LC860": "in_transit",  # EN REPARTO INTERNACIONAL
    "LC870": "incidence",  # ENTREGA POR ERROR YA RECUPERAD
    "LD221": "incidence",  # RETENIDO ADUANA
    "LD841": "in_transit",  # ENTRA EN ADUANA
    "LD846": "in_transit",  # SALE DE ADUANAS
    "LI300": "in_transit",  # SITUACIÓN DE CONVIVENCIA
    "LI308": "in_transit",  # MERCANCÍA EN N.T. ZAL
    "LI310": "in_transit",  # MERCANCÍA EN N.T. NAVALMORAL
    "LI313": "in_transit",  # MERCANCIA EN N.T. MANZANARES
    "LI314": "in_transit",  # MERCANCÍA EN N.T. CORDOBA
    "LI323": "in_transit",  # MERCANCÍA EN N.T. BAILÉN
    "LI328": "in_transit",  # MERCANCÍA EN N.T. CENTRAL
    "LI329": "in_transit",  # MERCANCÍA EN N.T. ANTEQUERA
    "LI335": "in_transit",  # MERCANCÍA EN N.T. LAS PALMAS
    "LI346": "in_transit",  # MERCANCÍA EN N.T. VALENCIA
    "LI349": "in_transit",  # MERCANCÍA EN N.T. BENAVENTE
    "LI350": "in_transit",  # MERCANCÍA EN N.T. ZARAGOZA
    "LI351": "in_transit",  # MERCANCÍA EN PT HUERCAL OVERA
    "LI352": "in_transit",  # MERCANCÍA EN PT NAVALMORAL
    "LI353": "in_transit",  # MERCANCÍA EN PT UBRIQUE
    "LI354": "in_transit",  # MERCANCÍA EN PT MANZANARES
    "LI355": "in_transit",  # MERCANCÍA EN PT BAILÉN
    "LI356": "in_transit",  # MERCANCÍA EN PT ALCAÑÍZ
    "LI357": "in_transit",  # MERCANCÍA EN PT CALAMOCHA
    "LI358": "in_transit",  # MERCANCÍA EN PT VALENCIA NORTE
    "LI359": "in_transit",  # MERCANCÍA EN PT LLODIO
    "LI360": "in_transit",  # MSI ENVIADA A ALMACÉN REGULADO
    "LI361": "in_transit",  # MERCANCÍA EN PT BILBAO
    "LI362": "in_transit",  # MERCANCÍA EN PT BENAVENTE
    "LI363": "in_transit",  # MERCANCÍA EN PT GGSS GRE
    "LI364": "in_transit",  # MERCANCÍA EN N.T. MERIDA
    "LI365": "in_transit",  # MERCANCÍA EN IGUALADA
    "LI366": "in_transit",  # MERCANCÍA EN PT SANLÚCAR
    "LI367": "in_transit",  # MERCANCÍA EN N.T. MIRANDA
    "LI368": "in_transit",  # MERCANCÍA EN N.T. PONFERRADA
    "LI369": "in_transit",  # MERCANCÍA EN PT CHICLANA
    "LI370": "in_transit",  # MERCANCÍA EN PT CONIL
    "LI371": "in_transit",  # MERCANCÍA EN PT TARANCÓN
    "LI372": "in_transit",  # MERCANCÍA EN PT MOTRIL
    "LI373": "in_transit",  # MERCANCÍA EN PT LEÓN SUR
    "LI374": "in_transit",  # MERCANCÍA EN PT 3 MADRID
    "LI375": "in_transit",  # MERCANCÍA EN PT 4 MADRID
    "LI376": "in_transit",  # MERCANCÍA EN PT PANTANOS
    "LI377": "in_transit",  # MERCANCÍA EN PT RIVAS
    "LI378": "in_transit",  # MERCANCÍA EN PT JARAMA
    "LI379": "in_transit",  # MERCANCÍA EN PT TUDELA
    "LI380": "in_transit",  # MERCANCÍA EN VERÍN
    "LI381": "in_transit",  # MERCANCÍA EN PT CARMONA
    "LI382": "in_transit",  # MERCANCÍA EN PT VENDRELL
    "LI383": "in_transit",  # MERCANCÍA EN PT TORTOSA
    "LI384": "in_transit",  # MERCANCÍA EN PT OSONA
    "LI388": "in_transit",  # MERCANCÍA EN N.T. EL PRAT
    "LI399": "in_transit",  # MERCANCÍA EN PLAT. MANZANARES
    "LI400": "in_transit",  # SITUACIÓN DE CONVIVENCIA
    "LI401": "in_transit",  # MERCANCÍA EN VITORIA
    "LI402": "in_transit",  # MERCANCÍA EN ALBACETE
    "LI403": "in_transit",  # MERCANCÍA EN ALICANTE
    "LI404": "in_transit",  # MERCANCÍA EN ALMERIA
    "LI405": "in_transit",  # MERCANCÍA EN AVILA
    "LI406": "in_transit",  # MERCANCÍA EN BADAJOZ
    "LI407": "in_transit",  # MERCANCÍA EN MALLORCA
    "LI408": "in_transit",  # MERCANCÍA EN BARCELONA
    "LI409": "in_transit",  # MERCANCÍA EN BURGOS
    "LI410": "in_transit",  # MERCANCÍA EN CACERES
    "LI411": "in_transit",  # MERCANCÍA EN CADIZ
    "LI412": "in_transit",  # MERCANCÍA EN CASTELLON
    "LI413": "in_transit",  # MERCANCÍA EN CIUDAD REAL
    "LI414": "in_transit",  # MERCANCÍA EN CORDOBA
    "LI415": "in_transit",  # MERCANCÍA EN LA CORUÑA
    "LI416": "in_transit",  # MERCANCÍA EN CUENCA
    "LI417": "in_transit",  # MERCANCÍA EN GERONA
    "LI418": "in_transit",  # MERCANCÍA EN GRANADA
    "LI419": "in_transit",  # MERCANCÍA EN GUADALAJARA
    "LI420": "in_transit",  # MERCANCÍA EN SAN SEBASTIAN
    "LI421": "in_transit",  # MERCANCÍA EN HUELVA
    "LI422": "in_transit",  # MERCANCÍA EN HUESCA
    "LI423": "in_transit",  # MERCANCÍA EN JAEN
    "LI424": "in_transit",  # MERCANCÍA EN LEON
    "LI425": "in_transit",  # MERCANCÍA EN LLEIDA
    "LI426": "in_transit",  # MERCANCÍA EN LOGROÑO
    "LI427": "in_transit",  # MERCANCÍA EN LUGO
    "LI428": "in_transit",  # MERCANCÍA EN MADRID
    "LI429": "in_transit",  # MERCANCÍA EN MALAGA
    "LI430": "in_transit",  # MERCANCÍA EN MURCIA
    "LI431": "in_transit",  # MERCANCÍA EN PAMPLONA
    "LI432": "in_transit",  # MERCANCÍA EN ORENSE
    "LI433": "in_transit",  # MERCANCÍA EN OVIEDO
    "LI434": "in_transit",  # MERCANCÍA EN PALENCIA
    "LI435": "in_transit",  # MERCANCÍA EN LAS PALMAS G.C.
    "LI436": "in_transit",  # MERCANCÍA EN PLAT. CALDAS
    "LI437": "in_transit",  # MERCANCÍA EN SALAMANCA
    "LI438": "in_transit",  # MERCANCÍA EN TENERIFE
    "LI439": "in_transit",  # MERCANCÍA EN SANTANDER
    "LI440": "in_transit",  # MERCANCÍA EN SEGOVIA
    "LI441": "in_transit",  # MERCANCÍA EN SEVILLA
    "LI442": "in_transit",  # MERCANCÍA EN SORIA
    "LI443": "in_transit",  # MERCANCÍA EN TARRAGONA
    "LI444": "in_transit",  # MERCANCÍA EN TERUEL
    "LI445": "in_transit",  # MERCANCÍA EN TOLEDO
    "LI446": "in_transit",  # MERCANCÍA EN VALENCIA
    "LI447": "in_transit",  # MERCANCÍA EN VALLADOLID
    "LI448": "in_transit",  # MERCANCÍA EN PT VIZCAYA
    "LI449": "in_transit",  # MERCANCÍA EN ZAMORA
    "LI450": "in_transit",  # MERCANCÍA EN ZARAGOZA
    "LI451": "in_transit",  # MERCANCÍA EN ALGECIRAS
    "LI452": "in_transit",  # MERCANCÍA EN LANZAROTE
    "LI453": "in_transit",  # MERCANCÍA EN VALLÉS OCCIDENTAL
    "LI454": "in_transit",  # MERCANCÍA EN GRANOLLERS
    "LI455": "in_transit",  # MERCANCÍA EN CARTEGENA
    "LI456": "in_transit",  # MERCANCÍA EN MELILLA
    "LI457": "in_transit",  # MERCANCÍA EN EIBAR
    "LI458": "in_transit",  # MERCANCÍA EN EL FERROL
    "LI459": "in_transit",  # MERCANCÍA EN PLASENCIA
    "LI460": "in_transit",  # MERCANCÍA EN FUERTEVENTURA
    "LI461": "in_transit",  # MERCANCÍA EN PLAT. SEU URGELL
    "LI462": "in_transit",  # MERCANCÍA EN IBIZA
    "LI463": "in_transit",  # MERCANCÍA EN PT MARINA ALTA
    "LI464": "in_transit",  # MERCANCÍA EN PT MERIDA
    "LI465": "in_transit",  # MERCANCÍA EN PLAT. ARANDA
    "LI466": "in_transit",  # MERCANCÍA EN PLAT. CLI GETAFE
    "LI467": "in_transit",  # MERCANCÍA EN PLAT. MIRANDA
    "LI468": "in_transit",  # MERCANCÍA EN PONFERRADA
    "LI469": "in_transit",  # MERCANCÍA EN PT BARCO
    "LI470": "in_transit",  # MERCANCÍA EN STA.CRUZ PALMA
    "LI471": "in_transit",  # MERCANCÍA EN SANTIAGO
    "LI472": "in_transit",  # MERCANCÍA EN VIGO
    "LI473": "in_transit",  # MERCANCÍA EN MENORCA
    "LI474": "in_transit",  # MERCANCÍA EN CEUTA
    "LI475": "in_transit",  # MERCANCÍA EN PT DON BENITO
    "LI476": "in_transit",  # MERCANCÍA EN PLAT. SANTARÉN
    "LI477": "in_transit",  # MERCANCÍA EN ANDORRA
    "LI478": "in_transit",  # MERCANCÍA EN LORCA
    "LI479": "in_transit",  # MERCANCÍA EN PLAT. LUCENA
    "LI480": "in_transit",  # MERCANCÍA EN INTNAL. MADRID
    "LI481": "in_transit",  # MERCANCÍA EN PLAT. LEIRÍA
    "LI482": "in_transit",  # MERCANCÍA EN GUARDA
    "LI483": "in_transit",  # MERCANCÍA EN LISBOA
    "LI484": "in_transit",  # MERCANCÍA EN PORTO
    "LI485": "in_transit",  # MERCANCÍA EN EVORA
    "LI486": "in_transit",  # MERCANCÍA EN FARO
    "LI487": "in_transit",  # MERCANCÍA EN AVEIRO
    "LI488": "in_transit",  # MERCANCÍA EN PLAT. COSLADA
    "LI489": "in_transit",  # MERCANCÍA EN INTNAL. BCN
    "LI490": "in_transit",  # MERCANCÍA EN PT BADALONA
    "LI491": "in_transit",  # MERCANCÍA EN BAIX LLOBREGAT
    "LI492": "in_transit",  # MERCANCÍA EN PT HOSPITALET
    "LI493": "in_transit",  # MERCANCÍA EN B-TARRAGONA
    "LI494": "in_transit",  # MERCANCÍA EN ALMACENAJE-BCN
    "LI495": "in_transit",  # MERCANCÍA EN MANRESA
    "LI496": "in_transit",  # MERCANCÍA EN PLAT. VLC. SUR
    "LI497": "in_transit",  # MERCANCÍA EN SEUR ESPAÑA
    "LI498": "in_transit",  # MERCANCÍA EN PLAT. ECIJA
    "LI499": "in_transit",  # MERCANCÍA EN PLAT. CONDADO
    "LI500": "in_transit",  # INCIDENCIA SACADA A REPARTO
    "LI501": "in_transit",  # INCIDENCIA EN GESTION SEUR
    "LI502": "in_transit",  # DEMORA REPARTO PREFERENTES
    "LI510": "incidence",  # FALTAN BULTOS
    "LI511": "incidence",  # FALTA EXPEDICIÓN COMPLETA
    "LI512": "incidence",  # FALTA POR SERVICIO (48 HORAS)
    "LI513": "incidence",  # FALTA DOCUMENTACIÓN
    "LI514": "incidence",  # CONFIRMADO PARCIAL PARA ENLACE
    "LI515": "in_transit",  # PENDIENTE DE REPARTO EN PLAZA
    "LI516": "in_transit",  # EXPEDICIÓN PARCIAL EN REPARTO
    "LI517": "incidence",  # INCIDENCIA EN DESPACHO ADUANA
    "LI518": "incidence",  # EXP. SIN CONTROLAR POR FIESTA
    "LI519": "customer_delivered",  # EXPEDICIÓN PARCIAL ENTREGADA
    "LI520": "canceled_shipment",  # DESTINATARIO DESCONOCIDO
    "LI521": "canceled_shipment",  # DOMICILIO DESCONOCIDO
    "LI522": "canceled_shipment",  # AUSENCIA PROLONGADA
    "LI523": "canceled_shipment",  # CERRADO O PRIMERA AUSENCIA
    "LI524": "incidence",  # CAMBIO DE DOMICILIO
    "LI525": "incidence",  # FIESTA LOCAL
    "LI526": "incidence",  # ACCESO IMPOSIBLE AL CLIENTE
    "LI527": "incidence",  # NO CONTESTA TELÉFONO
    "LI528": "incidence",  # VACACIONES DEL CLIENTE
    "LI529": "canceled_shipment",  # CERRADO DEFINITIVAMENTE
    "LI530": "incidence",  # RECEPCIONADO EN PUNTO
    "LI531": "incidence",  # RETENER EN PLAZA
    "LI532": "incidence",  # NO HAY PERSONA DE CONTACTO
    "LI533": "incidence",  # FALTA DE TIEMPO FLOTA
    "LI534": "incidence",  # COMPROBAR SI ES REEMBOLSO
    "LI535": "no_update",  # EXPEDICIÓN EXTRAVIADA
    "LI536": "incidence",  # ACCIDENTE/AVERÍA VEHÍCULO
    "LI537": "incidence",  # EXPEDICIÓN DETERIORADA
    "LI538": "incidence",  # EXP. DETERIORADA EN REPARTO
    "LI539": "incidence",  # PAQUETE ABIERTO
    "LI540": "incidence",  # AVISARÁN
    "LI541": "incidence",  # SIN EFECTIVO A LA ENTREGA
    "LI542": "canceled_shipment",  # RECHAZO. INDICAN DEVOLUCIÓN
    "LI543": "incidence",  # PDTE REPARTO DEVOLUCIÓN MASIVA
    "LI544": "incidence",  # CLIMA ADVERSO
    "LI545": "canceled_shipment",  # NO CONOCEN AL REMITENTE
    "LI546": "incidence",  # QUIEREN ABRIR EL PAQUETE
    "LI547": "in_transit",  # CONCERTADO PRÓXIMO REPARTO
    "LI548": "in_transit",  # CONCERTADA ENTREGA CON RMTE.
    "LI549": "in_transit",  # PENDIENTE ENTREGA CC/GS
    "LI550": "canceled_shipment",  # NO ACEPTAN POR ROTURA
    "LI551": "canceled_shipment",  # NO ACEPTAN PORTES
    "LI552": "incidence",  # NO ACEPTAN REEMBOLSO
    "LI553": "incidence",  # NO ACEPTAN DESPACHO O IMPUESTO
    "LI554": "incidence",  # NO QUIERE FIRMAR ALBARÁN/CDE
    "LI555": "incidence",  # NO ACEPTAN GASTOS REEMBOLSO
    "LI556": "canceled_shipment",  # ROTURA. CERTIFICAR DESTRUCCIÓN
    "LI557": "in_transit",  # SEGUNDA OLEADA
    "LI558": "in_transit",  # FALTA DE TIEMPO NAVE
    "LI559": "incidence",  # PENDIENTE CONCERTACIÓN CC/GS
    "LI560": "in_transit",  # NO TIENE PREPARADO EL CAMBIO
    "LI561": "incidence",  # ERROR DESTINO
    "LI562": "in_transit",  # SOBREINYECCIÓN DEL CLIENTE
    "LI563": "canceled_shipment",  # NO SALIÓ A REPARTO. CERRADO
    "LI564": "in_transit",  # ENTREGA CON MEDIOS ADICIONALES
    "LI565": "in_transit",  # PENDIENTE CONCERTAR ENTREGA
    "LI566": "in_transit",  # CONCERTADO SIN GESTIÓN
    "LI567": "in_transit",  # PDTE. CONCERTACIÓN AUTOMÁTICA
    "LI568": "in_transit",  # POSICIONADORA FALTAN BULTOS
    "LI569": "customer_delivered",  # DEPOSITADO REPARTIDOR PICK UP
    "LI570": "incidence",  # INCIDENCIA EN PUDO
    "LI571": "canceled_shipment",  # DEVOLVER.DEST.RECHAZA PUDO
    "LI572": "canceled_shipment",  # DEVOLVER.PLZO.CUMPLIDO PUDO
    "LI573": "incidence",  # INCIDENCIA EN LOCKER
    "LI574": "customer_delivered",  # RECEPCIONADO EN PICK UP
    "LI575": "incidence",  # DESTINATARIO SIN IDENTIFICAR
    "LI576": "customer_delivered",  # DEPOSITADO PUNTO REPARTIDOR
    "LI577": "customer_delivered",  # DEPOSITADO REPARTIDOR LOCKER
    "LI578": "customer_delivered",  # RECEPCIONADO EN LOCKER
    "LI579": "customer_delivered",  # RECOGIDO REPARTIDOR LOCKER
    "LI580": "in_transit",  # EN GESTIÓN ADUANA
    "LI581": "incidence",  # FALTA EN ORIGEN CLIENTE
    "LI599": "canceled_shipment",  # EXPEDICIÓN EN BAUL
    "LI600": "incidence",  # MERCANCÍA SIN IDENTIFICAR
    "LI717": "incidence",  # FALTA FACTURA
    "LI718": "incidence",  # FALTA DESCRIPCIÓN DE MERCANCÍA
    "LI719": "incidence",  # FALTA VALOR DE LA MERCANCÍA
    "LI721": "incidence",  # FALTA NIF/CIF DEL REMITENTE
    "LI722": "incidence",  # FALTA NIF/CIF DEL DESTINATARIO
    "LI725": "incidence",  # FALTA BULTO Y FACTURA
    "LI730": "SEE MESSAGE",  # INCIDENCIA DESCRITA EN MENSAJE
    "LI731": "incidence",  # FALTA TITULAR CIF/NIF REMITENT
    "LI732": "incidence",  # FALTA TITULAR CIF/NIF DESTINAT
    "LI752": "incidence",  # DATOS DOCUMENTADOS INCORRECTOS
    "LI799": "in_transit",  # MERCANCÍA PDTE DE EMBARCAR
    "LI810": "no_update",  # FALTAN BULTOS
    "LI811": "no_update",  # FALTA EXPEDICIÓN COMPLETA
    "LI813": "incidence",  # FALTA DOCUMENTACIÓN
    "LI840": "canceled_shipment",  # MERCANCIA DESECHADA
    "LI843": "no_update",  # PERDIDO DESPUES DE RECOGER
    "LI847": "incidence",  # INSPECCIÓN ADUANERA
    "LI848": "incidence",  # RETENIDO EN ADUANA
    "LI849": "incidence",  # INSPECCION NO ADUANERA
    "LI850": "incidence",  # CONFISCADO P/ADUANA
    "LI851": "incidence",  # RECIBIDO NO COMUNICADO
    "LI852": "incidence",  # DATOS COMUNICADOS INCORRECTOS
    "LI853": "incidence",  # EMBALAJE INSUFICIENTE
    "LI854": "incidence",  # REPRECINTADO
    "LI855": "incidence",  # ERROR EN PESO
    "LI862": "incidence",  # DECLARACION ERRONEA
    "LI863": "incidence",  # CUARENTENA
    "LI864": "incidence",  # ESPERANDO PAGO DE IMPUESTOS
    "LI865": "incidence",  # ADUANAS:DATOS INSUF./INCORRECT
    "LI866": "incidence",  # MATERIAL RESTRINGIDO
    "LI867": "incidence",  # INFORMACIÓN ACTUALIZADA
    "LI868": "incidence",  # PO BOX SIN TELEFONO
    "LI869": "incidence",  # ESPERANDO INSTRUCCION REMITENT
    "LI871": "incidence",  # LUGAR NO SEGURO
    "LI873": "customer_delivered",  # ENTREGADO A BROKER
    "LI876": "in_transit",  # PERDIDA CONEXION ARRASTRE INTL
    "LI877": "in_transit",  # EN GESTIÓN ALMACEN DESTINO
    "LI879": "incidence",  # MAL TIEMPO
    "LI880": "incidence",  # HUELGA
    "LI881": "no_update",  # ENVIO ROBADO
    "LI882": "no_update",  # BULTO DAÑADO
    "LI888": "incidence",  # MISS ROUTED-MISS LOADED
    "LI891": "incidence",  # INFORMACIÓN ADICIONAL
    "LI892": "incidence",  # RETENER
    "LI893": "incidence",  # IMPOSIBLE EJECUTAR SOLUC NOS
    "LI894": "incidence",  # INCIDENCIA EN DESPACHO ADUANA
    "LI895": "incidence",  # INCIDENCIA DOCUMENTACIÓN ADUAN
    "LK510": "incidence",  # Error en plaza de destino
    "LK511": "incidence",  # Error en servicio
    "LK512": "incidence",  # Error en peso
    "LK513": "incidence",  # Error en volumen
    "LK514": "incidence",  # Error en tarifa
    "LK515": "incidence",  # Error tipo de portes
    "LK516": "incidence",  # Error en bultos
    "LK517": "canceled_shipment",  # Anulado cambio destinatario
    "LK520": "incidence",  # Falta expedición parcial
    "LK521": "canceled_shipment",  # ANUL. FALTA Y ACUERDO FRANQ.
    "LK522": "canceled_shipment",  # ANULADA POR NO SALIÓ/DUPLICADA
    "LK523": "canceled_shipment",  # Expedición duplicada
    "LK524": "incidence",  # CAMBIO DIRECCIÓN DESTINATARIO
    "LK525": "no_update",  # ANULADA POR RETORNO INSULAR
    "LK530": "canceled_shipment",  # Cobro-origen portes
    "LK531": "canceled_shipment",  # Cobro-origen gastos reembolso
    "LK532": "canceled_shipment",  # Cobro-origen prima seguro
    "LK533": "canceled_shipment",  # Anulado por reenvio
    "LK535": "canceled_shipment",  # ANULADA EXPEDICIÓN EXTRAVIADA
    "LK536": "canceled_shipment",  # Cambio valor reembolso
    "LK537": "canceled_shipment",  # Suprimir valor reembolso
    "LK545": "canceled_shipment",  # Retasación llegadas a debidos
    "LK551": "incidence",  # Error reembolso
    "LK552": "incidence",  # Error CDE
    "LK553": "canceled_shipment",  # Error seguro
    "LK554": "canceled_shipment",  # ANULADA ERROR SC SEUR PLUS
    "LK555": "canceled_shipment",  # ANULADO ERROR SC CAMBIO
    "LK556": "canceled_shipment",  # ANULACIÓN POR SC SÁBADO
    "LK560": "no_update",  # Siniestro
    "LK570": "no_update",  # Cobro imposible-exp.entregada
    "LK571": "no_update",  # Imposible entregar destinatar.
    "LK572": "no_update",  # Imposible devolver al remiten.
    "LK573": "canceled_shipment",  # Anulado mercancía desechada
    "LK574": "no_update",  # DEVOLUCIÓN ANULADA REEMBOLSO
    "LK583": "incidence",  # Error POBLACIÓN
    "LK590": "incidence",  # Cargo reexpedición
    "LK596": "incidence",  # Cargo por indemnización
    "LK597": "incidence",  # Cargo dscto a cliente nacional
    "LK598": "incidence",  # ANULACION FRANQUCIA FUSIONADA
    "LL001": "customer_delivered",  # Entregado
    "LL003": "customer_delivered",  # ENTREGADO POR BULTO
    "LL007": "canceled_shipment",  # Liquidada entrega parcial
    "LL009": "customer_delivered",  # LIQUIDADO SIN DEPURAR
    "LL010": "customer_delivered",  # ENTREGADO EN PUNTO
    "LL011": "no_update",  # LIQUIDADO EXPEDIC. EXTRAVIADA
    "LL020": "customer_delivered",  # ENTREGADO AL VECINO
    "LL030": "customer_delivered",  # ENTREGADO EN LOCKER
    "LL060": "customer_delivered",  # ENTREGADO CAMBIO SIN RETORNO
    "LL080": "canceled_shipment",  # POSICIONADORA CERRADA
    "LL081": "canceled_shipment",  # POSICIONADORA BULTOS DEVUELTOS
    "LL082": "canceled_shipment",  # POSICIONADORA BULTOS DESTRUIDO
    "LL091": "no_update",  # LIQUIDADO EXPEDIC. EXTRAVIADA
    "LL092": "no_update",  # LIQUIDADO EXPEDICION ARCHIVADA
    "LL099": "incidence",  # Provisional dado de baja
    "LL100": "incidence",  # Liquidado CARGO
    "LL200": "incidence",  # Liquidado CASACION PROVISIONAL
    "LL300": "no_update",  # Liquidado DEVUELTO
    "LL301": "incidence",  # LIQUIDADO REENVIO A OTRA PLAZA
    "LL303": "canceled_shipment",  # Liquidado MERCANCIA DESECHADA
    "LL310": "canceled_shipment",  # Liquida-Indemniza FALTA PARCIA
    "LL360": "no_update",  # POSICIONADORA ALMACÉN REGULADO
    "LL600": "no_update",  # MSI RECLAMADA ENVIADA A FRANQU
    "LL830": "canceled_shipment",  # ABANDONADA INTERNACIONAL
    "LL832": "canceled_shipment",  # DESTRUIDA INTERNACIONAL
    "LL833": "no_update",  # DEVOLVER A ORIGEN
    "LL834": "no_update",  # DEVUELTA A INTERNACIONAL
    "LL835": "no_update",  # DEVUELTA A CORRESPONSAL/CLIENT
    "LL838": "incidence",  # REEXPEDIR
    "LL872": "customer_delivered",  # ENTREGADO A VECINO
    "LL873": "customer_delivered",  # ENTREGADO A BROKER
    "LL874": "incidence",  # CONFISCADO P/ADUANA
    "LM001": "customer_delivered",  # Error tipo pago cobrado
    "LM002": "customer_delivered",  # Error tipo pago factura
    "LM003": "customer_delivered",  # Error tipo pago recibo
    "LM004": "customer_delivered",  # Error tipo pago sin cargo
    "LM005": "customer_delivered",  # Error tipo pagado
    "LM006": "customer_delivered",  # Error tipo pago talón
    "LM009": "customer_delivered",  # Error sin tipo pago
    "LM010": "customer_delivered",  # Cobrada con talón
    "LM011": "customer_delivered",  # Error total cobrado distinto
    "LM012": "customer_delivered",  # Error no tiene código contable
    "LM013": "customer_delivered",  # Error no tiene teléfono
    "LM014": "customer_delivered",  # Cliente distinto al de cartera
    "LM015": "customer_delivered",  # Cliente estricto contado
    "LM016": "customer_delivered",  # No existe el código contable
    "LM017": "customer_delivered",  # Más de un cliente con = Tlfno.
    "LM018": "customer_delivered",  # No existe el teléfono
    "LM019": "customer_delivered",  # Repartidor distinto en cartera
    "LM020": "customer_delivered",  # Cliente contable sin chequear
    "LM021": "customer_delivered",  # Falta Nombre Firma Receptor
    "LM022": "customer_delivered",  # POSIBLE LIQUIDACIÓN PARCIAL
    "LM023": "customer_delivered",  # ENTREGA SIN VERIFICAR FIRMA
    "LM024": "customer_delivered",  # ENTREGA SIN VERIFICAR DESTINAT
    "LM025": "incidence",  # ENTREGA PENDIENTE FIRMA VÁLIDA
    "LM026": "customer_delivered",  # CDE PENDIENTE DIGITALIZAR
    "LM027": "customer_delivered",  # CDE PENDIENTE RECIBIR IMAGEN
    "LM060": "customer_delivered",  # ENTREGA SIN CONTRASTAR RETORNO
    "LM999": "incidence",  # ENTREGA  RELACIÓN A VERIFICAR
    "LR802": "incidence",  # PERDIDA DE CONEXIÓN CAUSA AJENA
    "LS001": "in_transit",  # ASIGNADA AUTOMÁTICAMENTE
    "LS002": "in_transit",  # ASIGNADA MANUALMENTE
    "LS003": "in_transit",  # REASIGNADA
    "LS004": "in_transit",  # Asignada por almacén
    "LS005": "in_transit",  # Reasignado por desanulación
    "LS006": "in_transit",  # ASIGNACIÓN AUTO. TRAS. INC.
    "LS007": "in_transit",  # ASIGNACION AUT. NORMALIZACION
    "LS008": "in_transit",  # ASIGNADO A REPARTO POR ENLACE
    "LS014": "in_transit",  # ASIGNADO A REPARTO POR ENLACE
    "LS857": "in_transit",  # RECIBIDO DELEGACION DESTINO
    "LT859": "in_transit",  # TRANSITO
    "SW189": "in_transit",  # SALIO DE INTERNACIONAL
    "SW89": "in_transit",  # RECIBIDO SIE
    "SW089": "in_transit",  # RECIBIDO SIE
    "SX001": "in_transit",  # RECIBIDO SIE
    "SX010": "in_transit",  # ENVÍO REGISTRADO
}
