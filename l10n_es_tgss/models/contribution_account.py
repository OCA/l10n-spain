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
        size=11,
        help="Company account to interact with the Social Security as person, "
             "or account where the person is hired.")
    affiliation_number = fields.Char(
        size=12,
        help="Number to interact with the Social Security as person.")

    @api.model
    def check_ss_code(self, code, is_company):
        """Check validity of contribution account code.

        :param str code:
            Code to be evaluated. It must be a numeric string.

        :param bool is_company:
            Indicates if the code belongs to a company. In such case, it is
            evaluated as a contribution account code. Otherwise, it is
            evaluated as an affiliation number code.
        """
        # Ensure it is numeric
        if not code.isnumeric():
            raise ex.NonNumericCodeError(code)

        # Ensure it has the right length
        expected_length = 11 if is_company else 12
        if is_company and len(code) != expected_length:
            raise ex.BadLengthError(code=code, expected=expected_length)

        # Perform control digit validation
        code, control = code[:-2], code[-2:]
        if code[2] == "0":
            code = code[:2] + code[3:]
        if "%02d" % (int(code) % 97) != control:
            raise ex.ControlDigitValidationError(code)
        return True

    @api.multi
    @api.constrains("contribution_account")
    def _check_contribution_account(self):
        """Ensure a good contribution account code is saved."""
        for s in self:
            if s.contribution_account:
                s.check_ss_code(s.contribution_account, s.is_company)

    @api.multi
    @api.constrains("affiliation_number")
    def _check_affiliation_number(self):
        """Ensure a good affiliation number is saved."""
        for s in self:
            if s.affiliation_number:
                s.check_ss_code(s.affiliation_number, s.is_company)
