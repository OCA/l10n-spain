# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re
from email.utils import parseaddr

# Official Logista Parcel (Integra2) Web Service Endpoints (API v5 & Labelling v4)
LOGISTA_TEST_SHIPMENT_URL = (
    "https://qua-clientes.integra2.es/EnlaceB2B/app/integrations/shipment/v1"
)
LOGISTA_PROD_SHIPMENT_URL = (
    "https://clientes.integra2.es/EnlaceB2B/app/integrations/shipment/v1"
)
LOGISTA_TEST_PLAZA_URL = (
    "https://qua-clientes.integra2.es/Visor/rest/unauthenticated/"
    "wsRepartoProductoPorPlazas"
)
LOGISTA_PROD_PLAZA_URL = (
    "https://clientes.integra2.es/Visor/rest/unauthenticated/"
    "wsRepartoProductoPorPlazas"
)
LOGISTA_TRACKING_URL_TEMPLATE = "https://www.logistaparcel.com/seguimiento-de-envios/"

# ServiceId / Product Line Enumeration (API v5 p.2-3 & Labelling v4 p.2)
LOGISTA_SERVICES = [
    ("1", "1 - AMBIPAQ"),
    ("2", "2 - URGEPAQ"),
    ("3", "3 - FRIOFARMA"),
    ("4", "4 - FRIOPAQ"),
    ("5", "5 - URGEFRIO"),
    ("6", "6 - FARMAPLUS"),
    ("7", "7 - AEREO FRIO"),
    ("8", "8 - FARMA < 25"),
    ("9", "9 - I2GOURMET"),
]

LOGISTA_SERVICE_NAMES = {
    "1": "AMBIPAQ",
    "2": "URGEPAQ",
    "3": "FRIOFARMA",
    "4": "FRIOPAQ",
    "5": "URGEFRIO",
    "6": "FARMAPLUS",
    "7": "AEREO FRIO",
    "8": "FARMA < 25",
    "9": "I2GOURMET",
}

# Sector Codes (Labelling v4 p.1-2: Position 1 of barcode & keyact in plaza WS)
LOGISTA_SECTORS = [
    ("0", "0 - Generic"),
    ("1", "1 - Pharma"),
    ("2", "2 - Food"),
    ("3", "3 - Electronics"),
    ("4", "4 - Convenience"),
    ("5", "5 - Books / Stationery"),
    ("6", "6 - Textile"),
    ("7", "7 - Cosmetics"),
    ("8", "8 - Automotive"),
]

LOGISTA_SECTOR_LABELS = {
    "0": "GENÉRICO",
    "1": "FARMA",
    "2": "ALIMENTACIÓN",
    "3": "ELECTRÓNICA",
    "4": "CONVENIENCIA",
    "5": "LIBROS/PAPELERÍA",
    "6": "TEXTIL",
    "7": "COSMÉTICA",
    "8": "AUTOMOCIÓN",
}

# FreightType (API v5 p.3)
LOGISTA_FREIGHT_TYPES = [
    ("P", "P - Prepaid (Pagados)"),
    ("D", "D - Collect (Debidos)"),
]

LOGISTA_INCOTERM_TO_FREIGHT = {
    "EXW": "D",
    "FCA": "D",
    "FAS": "D",
    "FOB": "D",
    "CPT": "P",
    "CIP": "P",
    "CFR": "P",
    "CIF": "P",
    "DAP": "P",
    "DPU": "P",
    "DDP": "P",
}

# Notifications.Type (API v5 p.3)
LOGISTA_NOTIFICATION_TYPES = [
    ("none", "No Status Notification"),
    ("1", "1 - Out for Delivery (Reparto)"),
    ("2", "2 - Delivered (Entrega)"),
    ("3", "3 - Out for Delivery & Delivered (Reparto y entrega)"),
    ("4", "4 - Documentation (Documentación)"),
]

# DeliveryNoteAction (API v5 p.3)
LOGISTA_DELIVERY_NOTE_ACTIONS = [
    ("0", "0 - Default / No Action"),
    ("1", "1 - Scan Signed Customer Delivery Note"),
    ("2", "2 - Return Signed Customer Delivery Note"),
]

# CustomerReferences.ReferenceType (API v5 p.3)
LOGISTA_REFERENCE_TYPES = [
    ("1", "1 - Logistics Operator"),
    ("7", "7 - Consignee / Delivery Point (PdE)"),
]

# Authorization Header Scheme
LOGISTA_AUTH_SCHEMES = [
    ("raw", "Token (<token>)"),
    ("bearer", "Bearer (Bearer <token>)"),
]

# Shipping Label Formats
LOGISTA_LABEL_FORMATS = [
    ("PDF", "PDF (100x150mm Label)"),
    ("ZPL", "ZPL (Zebra Thermal Printer)"),
]

# Package Classification (Bultos vs Palets)
LOGISTA_PACKAGE_KINDS = [
    ("parcel", "Parcel (Bulto)"),
    ("pallet", "Pallet (Palet)"),
]

# Supported Country Mappings (API v5 p.3 & Labelling v4 p.2)
# Note: Odoo uses ISO 'AD' for Andorra; Logista Parcel API uses 'AN' and barcode '03'.
LOGISTA_ISO_TO_COUNTRY_ID = {
    "ES": "ES",
    "PT": "PT",
    "AD": "AN",
    "AN": "AN",
}

LOGISTA_ISO_TO_BARCODE_COUNTRY = {
    "ES": "01",
    "PT": "02",
    "AD": "03",
    "AN": "03",
}


def get_logista_country_id(country_code):
    """Map ISO 3166-1 alpha-2 country code to Logista Parcel CountryId (ES/PT/AN)."""
    code = (country_code or "").strip().upper()
    return LOGISTA_ISO_TO_COUNTRY_ID.get(code, "")


def get_logista_barcode_country_code(country_code, default="01"):
    """Map country code to 2-digit Logista Parcel barcode country code (01/02/03)."""
    code = (country_code or "").strip().upper()
    return LOGISTA_ISO_TO_BARCODE_COUNTRY.get(code, default)


def sanitize_logista_phone(phone_str):
    """Format phone per API v5 p.3: without separators, prefixes, or extensions,
    maximum 15 digits.
    """
    if not phone_str:
        return ""
    raw = str(phone_str).strip()
    raw = re.split(r"(?i)\b(?:ext\.?|anexo|x)\s*\d+", raw)[0].strip()
    raw = re.sub(r"^(?:\+|00)\s*(?:34|351|376)\b", "", raw).strip()
    if raw.startswith("+"):
        raw = re.sub(r"^\+\d{1,3}\s*", "", raw)
    digits = re.sub(r"\D", "", raw)
    if len(digits) > 9 and digits.startswith(("0034", "00351", "00376")):
        for pfx in ("00351", "00376", "0034"):
            if digits.startswith(pfx):
                digits = digits[len(pfx) :]
                break
    elif len(digits) == 11 and digits.startswith("34"):
        digits = digits[2:]
    return digits[:15]


def sanitize_logista_email(email_str):
    """Extract a single valid email address (max 100 chars) per API v5 p.3-4."""
    if not email_str:
        return ""
    first_chunk = re.split(r"[;,]", str(email_str))[0].strip()
    _realname, addr = parseaddr(first_chunk)
    candidate = (addr or first_chunk).strip()
    if "@" not in candidate or " " in candidate:
        return ""
    return candidate[:100]


def sanitize_logista_nif(vat_str):
    """Format NIF/CIF (max 15 chars), stripping spaces, hyphens, and ISO prefix."""
    if not vat_str:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", str(vat_str).upper())
    for iso_prefix in ("ES", "PT", "AD", "AN"):
        if cleaned.startswith(iso_prefix) and len(cleaned) > len(iso_prefix) + 5:
            cleaned = cleaned[len(iso_prefix) :]
            break
    return cleaned[:15]


def format_logista_postal_code_api(zip_code, country_code="ES"):
    """Format Consignee.PostalCode (max 10 chars) for POST /shipment/v1.
    For Andorra (AD/AN), normalizes 'AD500' -> '00500' so I2MS hub discovery succeeds.
    """
    raw = re.sub(r"\s+", "", str(zip_code or "").upper())
    if not raw:
        return ""
    c_id = get_logista_country_id(country_code) or "ES"
    if c_id == "AN":
        replaced = raw.replace("AD", "00")
        digits = re.sub(r"\D", "", replaced)
        return digits.zfill(5)[:10] if digits else raw[:10]
    if c_id == "ES":
        digits = re.sub(r"\D", "", raw)
        return digits.zfill(5)[:10] if digits else raw[:10]
    return raw[:10]


def format_logista_postal_code_plaza(zip_code, country_code="ES"):
    """Format `codpos` query parameter for `wsRepartoProductoPorPlazas`."""
    raw = re.sub(r"\s+", "", str(zip_code or "").upper())
    if not raw:
        return ""
    c_id = get_logista_country_id(country_code) or "ES"
    if c_id == "AN":
        digits = re.sub(r"\D", "", raw.replace("AD", "00"))
        return digits.zfill(5) if digits else ""
    if c_id == "PT":
        return re.sub(r"\D", "", raw)
    digits = re.sub(r"\D", "", raw)
    return digits.zfill(5) if digits else ""


def format_logista_postal_code_barcode(zip_code, country_code="ES"):
    """Format 6-digit numeric postal code for positions 3-8 of the 34-digit barcode
    (Características de etiquetaje_v4 p.2):
    - Andorra: replace 'AD' with '00', left-pad to 6 digits ('AD500' -> '000500').
    - Portugal: use first 4 digits, left-pad to 6 digits ('15012012' -> '001501').
    - Spain: left-pad with '0' to 6 digits ('28021' -> '028021').
    """
    raw = re.sub(r"\s+", "", str(zip_code or "").upper())
    c_id = get_logista_country_id(country_code) or "ES"
    if c_id == "AN":
        digits = re.sub(r"\D", "", raw.replace("AD", "00"))
        return (digits[-6:] if len(digits) > 6 else digits).zfill(6)
    if c_id == "PT":
        digits = re.sub(r"\D", "", raw)[:4]
        return digits.zfill(6)
    digits = re.sub(r"\D", "", raw)[:6]
    return digits.zfill(6)


def format_logista_main_reference(raw_ref):
    """Normalize a picking/customer reference to at most 9 uppercase alphanumeric
    characters (no spaces or '%', which is the barcode padding separator).
    - For segmented Odoo sequences like 'WH/OUT/00026' or 'WH/OUT/00112084', extracts
      the trailing document number ('00026' / '00112084') so prefix letters do not
      break Code 128 Subset C numeric compression on automatic sorters.
    - When a non-segmented reference exceeds 9 characters, prefers trailing digits
      (up to 9) if present, otherwise keeps the trailing 9 alphanumeric characters.
    """
    raw_str = str(raw_ref or "").strip().upper()
    if "/" in raw_str:
        parts = [re.sub(r"[^A-Z0-9]", "", p) for p in raw_str.split("/")]
        parts = [p for p in parts if p]
        candidate = parts[-1] if parts else ""
    else:
        candidate = re.sub(r"[^A-Z0-9]", "", raw_str)

    if not candidate:
        return "0"
    if len(candidate) <= 9:
        return candidate
    trailing_digits = re.search(r"\d+$", candidate)
    if trailing_digits:
        return trailing_digits.group(0)[-9:]
    return candidate[-9:]


def format_logista_barcode_reference(main_ref):
    """Format the 9-character barcode reference field (Positions 17-25) per
    Características de etiquetaje_v4 p.2:
    - Complete right side with '%' as separator followed by '0's up to 9 chars.
    - Examples:
      * '10821' (5 chars) -> '10821%000'
      * '99002143' (8 chars) -> '99002143%'
      * '123456789' (9 chars) -> '123456789'
    """
    ref = format_logista_main_reference(main_ref)
    if len(ref) == 9:
        return ref
    return f"{ref}%{'0' * (8 - len(ref))}"


def build_logista_barcode_34(
    sector_code,
    service_id,
    postal_code,
    origin_delegation_code,
    customer_code,
    reference,
    package_index,
    dest_country_code="ES",
    origin_country_code="ES",
):
    """Build the official 34-character Code 128 Logista Parcel barcode
    (Características de etiquetaje_v4 p.2):
      Pos 1     (1 Num) : Sector code (0-8)
      Pos 2     (1 Num) : Product / Service line (1-9)
      Pos 3-8   (6 Num) : Destination postal code (zero-padded)
      Pos 9-10  (2 Num) : Origin delegation code (zero-padded)
      Pos 11-16 (6 Num) : Customer code (zero-padded)
      Pos 17-25 (9 Alfa): Customer reference (padded right with '%' + '0's)
      Pos 26-28 (3 Num) : Package order number in shipment (001..999)
      Pos 29-30 (2 Num) : Destination country code (01=ES, 02=PT, 03=AD)
      Pos 31-32 (2 Num) : Origin country code (default '01')
      Pos 33-34 (2 Num) : Transit country code (= Destination country code)
    """
    p1_sector = re.sub(r"\D", "", str(sector_code or "0"))[:1] or "0"
    p2_service = re.sub(r"\D", "", str(service_id or "1"))[:1] or "1"
    p3_8_zip = format_logista_postal_code_barcode(postal_code, dest_country_code)
    deleg_digits = re.sub(r"\D", "", str(origin_delegation_code or "0"))
    p9_10_deleg = (deleg_digits[-2:] if len(deleg_digits) > 2 else deleg_digits).zfill(
        2
    )
    cust_digits = re.sub(r"\D", "", str(customer_code or "0"))
    p11_16_cust = (cust_digits[-6:] if len(cust_digits) > 6 else cust_digits).zfill(6)
    p17_25_ref = format_logista_barcode_reference(reference)
    idx_int = min(999, max(1, int(package_index or 1)))
    p26_28_idx = f"{idx_int:03d}"
    p29_30_dest = get_logista_barcode_country_code(dest_country_code, default="01")
    p31_32_orig = get_logista_barcode_country_code(origin_country_code, default="01")
    p33_34_tran = p29_30_dest
    return (
        f"{p1_sector}{p2_service}{p3_8_zip}{p9_10_deleg}{p11_16_cust}"
        f"{p17_25_ref}{p26_28_idx}{p29_30_dest}{p31_32_orig}{p33_34_tran}"
    )


def format_logista_code128_subsets(barcode_34, mode="at"):
    """Apply Code 128 subset C / B switching per `Características de etiquetaje
    CB-Programación.pdf` to compact even-digit numeric runs into Code 128C pairs:
    - `mode="at"`: uses `@C` and `@B` markers as shown in CB-Programación.pdf
      (e.g. `@C040410110819141099002143@B%0@C01010101`).
    - `mode="zpl"`: uses Zebra ZPL `^BC` invocation codes (`>:` Start C, `>;` Start B,
      `>5` Mode C, `>6` Mode B).
    """
    code = str(barcode_34 or "")
    if not code:
        return ""
    tokens = []
    i = 0
    n = len(code)
    while i < n:
        j = i
        while j < n and code[j].isdigit():
            j += 1
        digit_len = j - i
        if digit_len >= 4:
            even_len = digit_len - (digit_len % 2)
            tokens.append(("C", code[i : i + even_len]))
            i += even_len
        else:
            k = i
            while k < n:
                m = k
                while m < n and code[m].isdigit():
                    m += 1
                if m - k >= 4:
                    if (m - k) % 2 == 1:
                        k += 1
                    break
                k = max(k + 1, m)
            tokens.append(("B", code[i:k]))
            i = k

    merged = []
    for subset, chunk in tokens:
        if merged and merged[-1][0] == subset:
            merged[-1] = (subset, merged[-1][1] + chunk)
        else:
            merged.append((subset, chunk))

    if mode == "zpl":
        out = []
        for idx, (subset, chunk) in enumerate(merged):
            if idx == 0:
                prefix = ">:" if subset == "C" else ">;"
            else:
                prefix = ">5" if subset == "C" else ">6"
            out.append(f"{prefix}{chunk}")
        return "".join(out)

    return "".join(f"@{subset}{chunk}" for subset, chunk in merged)
