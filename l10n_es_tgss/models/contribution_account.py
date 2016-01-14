# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models
from .. import exceptions as ex


class ContributionAccountABC(models.Model):
    """Store unique codes for companies.

    Companies can have multiple contribution account codes, that is why this
    auxiliar table is needed.

    Persons can only have one, so for persons you will not need this.
    """
    _name = "l10n_es_tgss.contribution_account_abc"
    _rec_name = "code"
    _sql_constraints = [
        ("code_unique", "unique(code)", _("Duplicated code.")),
    ]

    # Saved as Char because it can have leading zeroes
    code = fields.Char(
        size=11,
        required=True,
        help="Company account code to interact with the Social Security.")
    owner_id = fields.Many2one(
        "l10n_es_tgss.ccc_company_abc",  # Overwrite this in subclasses
        "Owner document",
        required=True,
        ondelete="cascade",
        help="Database object that owns this contribution account.")

    @api.multi
    @api.constrains("code")
    def _check_code(self):
        """Ensure a good contribution account code is saved."""
        for s in self:
            if s.code:
                s.check_code(s.code, True)

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
        if len(code) != expected_length:
            raise ex.BadLengthError(code=code, expected=expected_length)

        # Perform control digit validation
        code, control = code[:-2], code[-2:]
        if code[2] == "0":
            code = code[:2] + code[3:]
        if "%02d" % (int(code) % 97) != control:
            raise ex.ControlDigitValidationError(code)
        return True


class CompanyABC(models.AbstractModel):
    """Models inheriting this ABC will have a company contribution account.

    You will have to redeclare the field :attr:`~.contribution_account_ids`
    overwriting its ``comodel`` param to match the subclass of
    :class:`~.ContributionAccountABC` that you create in your submodule.
    """
    _name = "l10n_es_tgss.ccc_company_abc"

    contribution_account_ids = fields.One2many(
        ContributionAccountABC._name,  # Overwrite this in subclasses
        "owner_id",
        "Contribution accounts",
        help="Company accounts to interact with the Social Security.")


class PersonABC(models.AbstractModel):
    """Models inheriting this ABC will have a personal affiliation number.

    They will be able to belong to a company's account code too.

    You will have to redeclare the field :attr:`~.contribution_account_ids`
    overwriting its ``comodel`` param to match the subclass of
    :class:`~.ContributionAccountABC` that you create in your submodule, and
    you will probably want to add a domain to it too.
    """
    _name = "l10n_es_tgss.ccc_person_abc"

    contribution_account_id = fields.Many2one(
        ContributionAccountABC._name,  # Overwrite this in subclasses
        "Contribution account",
        ondelete="set null",
        help="Company account where this person is hired.")
    affiliation_number = fields.Char(
        size=12,
        help="Personal account code to interact with the Social Security.")

    @api.multi
    @api.constrains("affiliation_number")
    def _check_affiliation_number(self):
        """Ensure a good affiliation number is saved."""
        for s in self:
            if s.affiliation_number:
                s.contribution_account_id.check_code(
                    s.affiliation_number,
                    getattr(s, "is_company", False))


class ABC(models.AbstractModel):
    """Models inheriting this ABC will have a contribution account code."""
    _name = "l10n_es_tgss.ccc_abc"
    _inherit = [CompanyABC._name, PersonABC._name]
