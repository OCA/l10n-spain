# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from .common import _NS
from .. import exceptions as ex


class ABC(models.AbstractModel):
    """Models inheriting this ABC will have a contribution account code."""
    _name = "%s.ccc_abc" % _NS

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
