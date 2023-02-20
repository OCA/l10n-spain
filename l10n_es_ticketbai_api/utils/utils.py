# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re
from enum import Enum

from odoo import _, exceptions


class EnumValues(Enum):
    @classmethod
    def values(cls):
        return [x.value for _, x in cls.__members__.items()]


def split_vat(vat):
    vat_country, vat_number = vat[:2].lower(), vat[2:].replace(" ", "")
    return vat_country, vat_number


def check_str_decimal(field, value, no_digits=12, no_decimal_digits=2):
    pattern = r"(\+|-)?\d{1,%d}(\.\d{0,%d})?" % (no_digits, no_decimal_digits)
    match_res = re.match(pattern, value)
    if not match_res or (match_res and match_res.group(0) != value):
        raise exceptions.ValidationError(
            _(
                "%(field)s value must be a string of a float with maximum %("
                "digits)d digits and "
                "%(dec_digits)d decimal points. The decimal separator must be "
                "'.'"
            )
            % {"fields": field, "digits": no_digits, "dec_digits": no_decimal_digits}
        )


def check_str_percentage(field, value, no_digits=3, no_decimal_digits=2):
    check_str_decimal(
        field, value, no_digits=no_digits, no_decimal_digits=no_decimal_digits
    )
    if not 0.0 <= float(value) <= 100.0:
        raise exceptions.ValidationError(
            _("%s value must be a positive percentage.") % field
        )


def check_spanish_vat_number(field, value):
    pattern = (
        r"(([a-z|A-Z]{1}\d{7}[a-z|A-Z]{1})|(\d{8}[a-z|A-Z]{1})|" r"([a-z|A-Z]{1}\d{8}))"
    )
    match_res = re.match(pattern, value)
    if not match_res or (match_res and match_res.group(0) != value) or 9 != len(value):
        raise exceptions.ValidationError(
            _("Invalid %(field)s format '%(" "value)s'.")
            % {"field": field, "value": value}
        )


def check_date(field, value):
    pattern = r"(\d{2,2}-\d{2,2}-\d{4,4})"
    match_res = re.match(pattern, value)
    if not match_res or (match_res and match_res.group(0) != value) or 10 != len(value):
        raise exceptions.ValidationError(
            _("Invalid %(field)s format '%(value)" "s'.")
            % {"field": field, "value": value}
        )


def check_hour(field, value):
    pattern = r"(\d{2,2}:\d{2,2}:\d{2,2})"
    match_res = re.match(pattern, value)
    if not match_res or (match_res and match_res.group(0) != value):
        raise exceptions.ValidationError(
            _("Invalid %(field)s format '%(value)s'.")
            % {"field": field, "value": value}
        )
