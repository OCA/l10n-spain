# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from enum import Enum


class TicketBaiCustomerCancellationResponseMessageCode(Enum):
    INCORRECT_SENDER_CERTIFICATE = '001'
    XSD_SCHEMA_NOT_COMPLY = '002'
    INVALID_SENDER_CERTIFICATE = '003'
    WRONG_SIGNATURE = '004'
    INVALID_SIGNER_CERTIFICATE = '005'
    REQUIRED_FIELD_MISSING = '006'
    INVALID_TBAI_LICENSE = '007'
    DEVICE_NOT_REGISTERED = '008'
    ADDRESSEE_NOT_REGISTERED = '009'
    INVOICE_NOT_REGISTERED = '010'
    INVOICE_ALREADY_CANCELLED = '011'
    SERVICE_NOT_AVAILABLE = '012'
