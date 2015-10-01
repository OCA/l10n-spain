# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, exceptions


class ContributionAccountError(exceptions.ValidationError):
    def __init__(self, record, value=None):
        super(ContributionAccountError, self).__init__(value or self._value)
        self.name = _("Error(s) with the contribution account.")
        self.record = record


class BadLengthCompany(ContributionAccountError):
    _value = _("The code must have 11 digits because it is a company.")


class BadLengthPerson(ContributionAccountError):
    _value = _("The code must have 12 digits because it is a person.")


class ControlDigitValidationFailed(ContributionAccountError):
    _value = _("Control digit validation failed. This code is not valid.")


class NonNumericCode(ContributionAccountError):
    _value = _("The code must only contain numbers.")
