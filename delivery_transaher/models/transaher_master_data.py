# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re
from datetime import datetime

# Default Transaher SOAP Base URLs (Test vs Production)
TRANSAHER_TEST_MCLIENT_URL = "https://clientes.transaher.es/mclient_test"
TRANSAHER_TEST_MBRIDGE_URL = "https://clientes.transaher.es/mbridge_test"

TRANSAHER_PROD_MCLIENT_URL = "https://clientes.transaher.es/mclient"
TRANSAHER_PROD_MBRIDGE_URL = "https://clientes.transaher.es/mbridge"

TRANSAHER_TRACKING_URL_TEMPLATE = "https://clientes.transaher.es/"

# Fixed Protocol & Default Keys per Transaher Technical Manual
TRANSAHER_DEFAULT_HOLDING = 0
TRANSAHER_DEFAULT_SECCION = 10
TRANSAHER_DEFAULT_CENTRO = 461
TRANSAHER_DEFAULT_PROTOCOLO = 20

# Security Token TTL: server expires in 20 minutes; renew proactively at 18 minutes
TRANSAHER_TOKEN_TTL_MINUTES = 18

# SOAP Namespaces & SOAPAction Headers (verified against Transaher WSDLs)
NS_SOAPENV = "http://schemas.xmlsoap.org/soap/envelope/"
NS_MTRANS_WEB = "MTRANS_WEB"
NS_MWSBRIDGE = "MWSBridge"
NS_WSGETTOKEN = "MWSBridge.wsgettoken_services"
NS_WSETIEXP = "MWSBridge.wsetiexpsoap_services"
NS_WSINFOTRN = "MWSBridge.wsinformaciontransporte_services"

SOAP_ACTION_TOKEN = "MWSBridge.wsgettoken_services/wsgettoken_services/execute"
SOAP_ACTION_ALTA = "MTRANS_WEBaction/AWSPRCSATSOAP.Execute"
SOAP_ACTION_BAJA = "MTRANS_WEBaction/AWSEXPBAJA.Execute"
SOAP_ACTION_ETIQUETAS = "MWSBridge.wsetiexpsoap_services/wsetiexpsoap_services/execute"
SOAP_ACTION_INFO_TRANSPORTE = (
    "MWSBridge.wsinformaciontransporte_services/"
    "wsinformaciontransporte_services/execute"
)
SOAP_ACTION_MANIFIESTO = "MTRANS_WEBaction/AWSMNFPRTSOAP.Execute"

# Country ISO-2 to Transaher 3-digit Numeric Country Code (Section 3.2, Field 3)
# Manual explicitly specifies: 011 = Spain, 010 = Portugal
TRANSAHER_COUNTRY_CODES = {
    "ES": "011",
    "PT": "010",
    "FR": "001",
    "BE": "017",
    "NL": "003",
    "DE": "004",
    "IT": "005",
    "GB": "006",
    "IE": "007",
    "DK": "008",
    "GR": "009",
    "LU": "018",
    "NO": "028",
    "SE": "030",
    "FI": "032",
    "AD": "037",
    "AT": "038",
    "CH": "039",
    "PL": "060",
    "CZ": "061",
    "SK": "063",
    "HU": "064",
    "RO": "066",
    "BG": "068",
    "MA": "204",
}

# Freight Payment Terms (Section 3.2, Field 8: 1 = Pagados, 2 = Debidos)
TRANSAHER_PORTES_TYPES = [
    ("1", "1 - Freight Prepaid (Portes Pagados)"),
    ("2", "2 - Freight Collect (Portes Debidos)"),
]

# Automatic mapping from standard Incoterms to Transaher Tipo de Portes
TRANSAHER_INCOTERM_TO_PORTES = {
    "EXW": "2",
    "FCA": "2",
    "FAS": "2",
    "FOB": "2",
    "CFR": "1",
    "CIF": "1",
    "CPT": "1",
    "CIP": "1",
    "DAP": "1",
    "DPU": "1",
    "DDP": "1",
}

# Label Source & Print Modes (Sections 5 & 6)
TRANSAHER_LABEL_MODES = [
    ("ws_with_fallback", "Transaher Web Service PDF (with Local QWeb Label Fallback)"),
    ("ws_only", "Transaher Web Service Only (wsEtiExpSOAP)"),
    ("local_qweb", "Local Standard Transaher Label PDF (24-digit Barcode)"),
]

TRANSAHER_BULTOS_TAG_MODES = [
    ("reprint_all", "All Shipment Packages (-1)"),
    ("pending", "Pending Unprinted Packages Only (Empty tag)"),
]

# Packaging Type Codes
TRANSAHER_PACKAGING_CODES = [
    ("BUL", "BUL - Standard Parcel / Box (Bulto)"),
    ("CAJ", "CAJ - Cardboard Box (Caja)"),
    ("PAL", "PAL - Pallet (Palet)"),
    ("EUR", "EUR - Euro Pallet (120 x 80 cm)"),
    ("MED", "MED - Half Pallet (80 x 60 cm)"),
    ("SOB", "SOB - Envelope / Document (Sobre)"),
]

TRANSAHER_PALLET_CODES = {"PAL", "EUR", "MED"}

# Local Tariff Calculation Modes
TRANSAHER_RATE_TYPES = [
    ("fixed", "Fixed Bracket Price"),
    ("per_kg", "Base + Price per Total Kg"),
    ("per_excess_kg", "Base + Price per Excess Kg (above Included Kg)"),
    ("per_100kg", "Base + Price per 100 Kg Fraction"),
    ("per_package", "Base + Price per Package / Pallet"),
]

# Cancellation Error Codes (Section 4.3 & Section 10)
TRANSAHER_BAJA_ERROR_MAP = {
    0: "OK",
    1: "Non-existent expedition (Expedición inexistente)",
    2: (
        "Invalid expedition status — cancellation is only allowed in Received, "
        "Documented, or Labelled status (Situación de expedición incorrecta)"
    ),
    3: "Invalid web status (Situación web incorrecta)",
}

# Token Validation Codes (Section 2.4 & Section 10)
TRANSAHER_TOKEN_ERROR_MAP = {
    0: "OK, valid token",
    1: "Missing security token (No tiene token de seguridad)",
    2: "Expired security token (Token de seguridad caducado)",
}

# OCA delivery_state values where Section 4.1 allows awsExpBaja cancellation
TRANSAHER_CANCELLABLE_DELIVERY_STATES = {
    False,
    "",
    "shipping_recorded_in_carrier",
}


def normalize_soap_base_url(url, fallback=""):
    """Normalize a configured MClient / MBridge URL so that even if a user pastes
    a full WSDL endpoint (e.g. `.../awsprcsatsoap.aspx?wsdl`), the clean base
    directory URL is returned without trailing slash.
    """
    raw = (url or fallback or "").strip()
    if not raw:
        return ""
    raw = raw.split("?", 1)[0].rstrip("/")
    raw = re.sub(r"/[^/]+\.(?:aspx|svc)$", "", raw, flags=re.IGNORECASE)
    return raw.rstrip("/")


def sanitize_transaher_field(value, max_len=None):
    """Sanitize a text value for pipe-delimited `Datosentrada` (Section 3.2):
    replaces `|` and control characters so alignment is preserved, truncating
    to `max_len`.
    """
    if value is None or value is False:
        return ""
    cleaned = (
        str(value)
        .replace("|", "/")
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("\t", " ")
    )
    cleaned = " ".join(cleaned.split()).strip()
    if max_len and max_len > 0:
        cleaned = cleaned[:max_len].strip()
    return cleaned


def format_transaher_decimal(value, max_len=8, max_decimals=3, empty_if_zero=False):
    """Format a float value using Transaher's comma decimal format
    (e.g. `12345,123` per Section 3.2) within `max_len` characters.
    """
    num = float(value or 0.0)
    if num <= 0.0 and empty_if_zero:
        return ""
    num = max(0.0, num)

    for dec in range(max_decimals, -1, -1):
        if dec == 0:
            candidate = str(int(round(num)))
        else:
            formatted = f"{num:.{dec}f}"
            int_part, dec_part = formatted.split(".")
            dec_part = dec_part.rstrip("0")
            candidate = f"{int_part},{dec_part}" if dec_part else int_part
        if len(candidate) <= max_len:
            return candidate

    return str(int(round(num)))[:max_len]


def get_transaher_country_code(country, fallback="011"):
    """Return the 3-digit numeric Transaher country code for a `res.country`."""
    if not country:
        return fallback
    iso_code = (country.code if hasattr(country, "code") else str(country)) or ""
    iso_code = iso_code.strip().upper()
    if iso_code.isdigit() and len(iso_code) <= 3:
        return iso_code.zfill(3)
    return TRANSAHER_COUNTRY_CODES.get(iso_code, fallback)


def format_transaher_postal_code(postal_code, country_code="ES", for_barcode=False):
    """Normalize postal code for `Datosentrada` (Field 4) or 24-digit barcode.
    In Section 5.2 (Barcode positions 18-22):
    - Standard (Spain, etc.): 5 digits zero-padded on the left.
    - Portugal (`PT`): first 4 digits completed with `9` at the 5th position.
    """
    raw = sanitize_transaher_field(postal_code)
    digits = re.sub(r"\D", "", raw)
    iso = (country_code or "ES").strip().upper()

    if for_barcode:
        if iso == "PT":
            pt_prefix = (digits[:4]).ljust(4, "0") if digits else "0000"
            return f"{pt_prefix}9"
        return (digits[:5]).zfill(5)

    if iso == "PT" and digits:
        return digits[:4] if len(digits) >= 4 else digits.zfill(4)
    if digits:
        return digits[:5].zfill(5) if len(digits) < 5 and iso == "ES" else digits[:5]
    return raw[:5]


def build_transaher_barcode_24(
    centro_origen,
    cod_expedicion,
    bulto_num=1,
    postal_code="00000",
    country_code="ES",
):
    """Build the 24-character Transaher package barcode (Section 5.2):
    - Pos 1-2  (2): Fixed '10'
    - Pos 3-5  (3): Origin Center padded to 3 digits (e.g. '081')
    - Pos 6-14 (9): Expedition Number zero-padded to 9 digits ('012685535')
    - Pos 15-17(3): Package index padded to 3 digits (e.g. '002')
    - Pos 18-22(5): Destination Postal Code (5 digits; for Portugal 4 digits + '9')
    - Pos 23-24(2): Fixed '01'
    Example: 10 + 081 + 012685535 + 002 + 96600 + 01 = '100810126855350029660001'
    """
    centro_digits = re.sub(r"\D", "", str(centro_origen or "0"))
    exp_digits = re.sub(r"\D", "", str(cod_expedicion or "0"))
    bulto_digits = re.sub(r"\D", "", str(max(1, int(bulto_num or 1))))

    part_prefix = "10"
    part_centro = centro_digits.zfill(3)[-3:]
    part_exp = exp_digits.zfill(9)[-9:]
    part_bulto = bulto_digits.zfill(3)[-3:]
    part_cp = format_transaher_postal_code(
        postal_code=postal_code,
        country_code=country_code,
        for_barcode=True,
    )
    part_suffix = "01"
    return f"{part_prefix}{part_centro}{part_exp}{part_bulto}{part_cp}{part_suffix}"


def map_transaher_status_to_delivery_state(
    situacion="",
    description="",
    has_incidence=False,
    is_return=False,
):
    """Map Transaher `Situacion` / event text to OCA `delivery_state` keys:
    - `shipping_recorded_in_carrier`
    - `in_transit`
    - `canceled_shipment`
    - `incident`
    - `customer_delivered`
    - `warehouse_delivered`
    """
    if has_incidence:
        return "incident"
    combined = f"{situacion or ''} {description or ''}".strip().lower()
    if not combined:
        return "shipping_recorded_in_carrier"

    if any(k in combined for k in ("anulad", "baja", "cancel")):
        return "canceled_shipment"
    if any(
        k in combined
        for k in (
            "incidencia",
            "ausente",
            "rehusa",
            "rechaz",
            "averi",
            "falt",
            "error",
            "retenid",
        )
    ):
        return "incident"
    if any(
        k in combined
        for k in ("entregad", "conform", "deliver", "ok entrega", "cumpliment")
    ):
        return "warehouse_delivered" if is_return else "customer_delivered"
    if any(
        k in combined
        for k in (
            "reparto",
            "distribucion",
            "distribución",
            "calle",
            "chofer",
            "transito",
            "tránsito",
            "arrastre",
            "ruta",
            "canaliz",
            "recogid",
            "almacen",
            "almacén",
            "plataforma",
        )
    ):
        return "in_transit"
    if any(
        k in combined
        for k in ("etiquetad", "documentad", "recepcionad", "pendiente", "alta", "grab")
    ):
        return "shipping_recorded_in_carrier"
    return "in_transit"


def parse_transaher_datetime(raw_value):
    """Parse a Transaher timestamp string into a naive `datetime` (or `None`)."""
    if not raw_value:
        return None
    text = str(raw_value).strip().replace("T", " ")
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
