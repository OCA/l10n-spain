# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from .common import _NS
from .. import exceptions as ex


class ContributionAccountABC(models.Model):
    _name = "%s.contribution_account_abc" % _NS
    _rec_name = "code"

    # Saved as Char because it can have leading zeroes
    code = fields.Char(
        size=12,
        required=True,
        help="Company account to interact with the Social Security as person, "
             "or account where the person is hired.")
    is_company = fields.Boolean(
        help="Know if the code belongs to a company.")
    owner_id = fields.Many2one(
        "%s.ccc_company_abc" % _NS,  # Overwrite this in subclasses
        "Owner document",
        required=True,
        ondelete="cascade",
        help="Database object that owns this contribution account.")

    @api.multi
    @api.constrains("is_company", "code")
    def _check_code(self):
        """Ensure a good contribution account code is saved."""
        for s in self:
            if s.code:
                s.check_code(s.code, s.is_company)

    @api.model
    def check_code(self, code, is_company):
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


class CompanyABC(models.AbstractModel):
    """Models inheriting this ABC will have a company contribution account."""
    _name = "%s.ccc_company_abc" % _NS

    contribution_account_ids = fields.One2many(
        ContributionAccountABC._name,  # Overwrite this in subclasses
        "owner_id",
        "Contribution accounts",
        context={"default_is_company": True},
        help="Company accounts to interact with the Social Security.")


class PersonABC(models.AbstractModel):
    """Models inheriting this ABC will have a personal affiliation number."""
    _name = "%s.ccc_person_abc" % _NS

    contribution_account_id = fields.Many2one(
        ContributionAccountABC._name,  # Overwrite this in subclasses
        "Contribution account",
        ondelete="set null",
        context={"default_is_company": False},
        help="Company account where this person is hired.")
    affiliation_number_id = fields.Many2one(
        ContributionAccountABC._name,  # Overwrite this in subclasses
        "Affiliation number",
        ondelete="set null",
        context={"default_is_company": False},
        help="Person account to interact with the Social Security.")

    @api.multi
    @api.constrains("affiliation_number")
    def _check_affiliation_number(self):
        """Ensure a good affiliation number is saved."""
        for s in self:
            if s.affiliation_number_id:
                s.check_code(s.affiliation_number_id, s.is_company)


class ABC(models.AbstractModel):
    """Models inheriting this ABC will have a contribution account code."""
    _name = "%s.ccc_abc" % _NS
    _inherit = [CompanyABC._name, PersonABC._name]
