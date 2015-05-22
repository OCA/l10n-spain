# -*- encoding: utf-8 -*-

# Odoo, Open Source Management Solution
# Copyright (C) 2014-2015  Grupo ESOC <www.grupoesoc.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
