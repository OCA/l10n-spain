# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, exceptions


class TGSSError(exceptions.ValidationError):
    """Base class for this module's validation errors."""
    def __init__(self, record, value=None, *args, **kwargs):
        value = (value or self._value).format(record=record)
        super(TGSSError, self).__init__(value, *args, **kwargs)
        self.record = record


class ContributionAccountError(TGSSError):
    """Base class for contribution account validation errors."""
    def __init__(self, *args, **kwargs):
        super(ContributionAccountError, self).__init__(*args, **kwargs)
        self.name = _("Error(s) with the contribution account.")


class BadLengthCompanyError(ContributionAccountError):
    _value = _("The code {record.contribution_account} must have 11 digits "
               "because it is a company.")


class BadLengthPersonError(ContributionAccountError):
    _value = _("The code {record.contribution_account} must have 12 digits "
               "because it is a person.")


class ControlDigitValidationError(ContributionAccountError):
    _value = _("Control digit validation failed. "
               "The code {record.contribution_account} is not valid.")


class NonNumericCodeError(ContributionAccountError):
    _value = _("The code {record.contribution_account} is not numeric.")


