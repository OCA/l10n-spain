# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, exceptions


class TGSSError(exceptions.ValidationError):
    """Base class for this module's validation errors."""
    def __init__(self, *args, **kwargs):
        self._args, self._kwargs = args, kwargs
        value = self._message()
        super(TGSSError, self).__init__(value)

    def _message(self):
        """Format the message."""
        return self.__doc__.format(*self._args, **self._kwargs)


class ContributionAccountError(TGSSError):
    """Base class for contribution account validation errors."""


class BadLengthError(ContributionAccountError):
    __doc__ = _("The code {code} must have {expected} digits.")


class ControlDigitValidationError(ContributionAccountError):
    __doc__ = _("Control digit validation failed. The code {} is not valid.")


class NonNumericCodeError(ContributionAccountError):
    __doc__ = _("The code {} is not numeric.")


class OutOfRangeError(TGSSError):
    __doc__ = _("Disability {percent}% of {name} must be between 0 and 100.")
