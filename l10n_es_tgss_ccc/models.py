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

from openerp import api, fields, models
from . import exceptions as ex


class ABC(models.AbstractModel):
    """Models with contribution account code."""
    _name = "l10n_es_tgss_ccc.abc"

    # Saved as Char because it can have leading zeroes
    contribution_account = fields.Char(
        size=12,
        help="Account to interact with the Social Security.")

    @api.one
    @api.constrains("contribution_account")
    def _check_contribution_account(self):
        """Ensure a good code is saved."""
        # Skip empty codes
        if not self.contribution_account:
            return

        # Ensure it is numeric
        if not self.contribution_account.isnumeric():
            raise ex.NonNumericCode(self)

        # Ensure it has the right length
        is_company = getattr(self, "is_company", False)
        if is_company and len(self.contribution_account) != 11:
            raise ex.BadLengthCompany(self)
        elif not is_company and len(self.contribution_account) != 12:
            raise ex.BadLengthPerson(self)

        # Perform control digit validation
        code, control = (self.contribution_account[:-2],
                         self.contribution_account[-2:])
        if code[2] == "0":
            code = code[:2] + code[3:]
        if "%02d" % (int(code) % 97) != control:
            raise ex.ControlDigitValidationFailed(self)


class Partner(models.Model):
    _name = "res.partner"
    _inherit = [_name, ABC._name]


class Employee(models.Model):
    _name = "hr.employee"
    _inherit = [_name, ABC._name]
