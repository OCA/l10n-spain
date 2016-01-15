# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models
from openerp.addons.base.res.res_request import referencable_models
from .. import exceptions as ex


class ContributionAccount(models.Model):
    """Store unique codes for companies.

    Companies can have multiple contribution account codes, that is why this
    auxiliar table is needed.

    Persons can only have one, so for persons you will not need this.
    """
    _description = "Spanish Social Security contribution account codes"
    _name = "l10n.es.tgss.contribution_account"
    _rec_name = "code"
    _sql_constraints = [
        ("code_unique", "unique(code)", _("Duplicated code.")),
    ]

    # Saved as Char because it can have leading zeroes
    code = fields.Char(
        size=11,
        required=True,
        help="Company account code to interact with the Social Security.")

    # Instead of using a Many2one, use split model + id fields to allow
    # one-line inheritances, like the ``mail`` module does
    owner_id = fields.Integer(
        "Owner ID",
        index=True,
        readonly=True,
        required=True,
        help="ID of the database object that owns this contribution account.")
    owner_model = fields.Char(
        index=True,
        readonly=True,
        required=True)
    owner_record_id = fields.Reference(
        lambda self: referencable_models(
            self, self.env.cr, self.env.uid, context=self.env.context),
        "Owner",
        readonly=True,
        compute="_compute_owner_record_id")

    @api.multi
    @api.depends("owner_id", "owner_model")
    def _compute_owner_record_id(self):
        """Relate with owner in a user-friendly way."""
        for s in self:
            s.owner_record_id = "%s,%d" % (s.owner_model, s.owner_id)

    @api.multi
    @api.constrains("code")
    def _check_code(self):
        """Ensure a good contribution account code is saved."""
        for s in self.filtered("code"):
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
        main, control = code[:-2], code[-2:]
        if main[2] == "0":
            main = main[:2] + main[3:]
        if "%02d" % (int(main) % 97) != control:
            raise ex.ControlDigitValidationError(code)
        return True


class CommonABC(models.AbstractModel):
    _description = "Base for models related with contribution accounts"
    _name = "l10n.es.tgss.contribution_account.common.abc"

    model_name = fields.Char(compute="_compute_model_name")

    @api.multi
    def _compute_model_name(self):
        """This is needed to have a working domain."""
        for s in self:
            s.model_name = self._name


class CompanyABC(models.AbstractModel):
    """Any model inheriting this will have multiple contribution accounts.

    It will have to add a domain to contribution_account_ids like this::

        contribution_account_ids = fields.One2many(
            context={"default_owner_model": _name})

    Otherwise the UI will not work properly.
    """
    _description = "Base for models with multiple contribution accounts"
    _name = "l10n.es.tgss.contribution_account.company.abc"
    _inherit = "l10n.es.tgss.contribution_account.common.abc"

    contribution_account_ids = fields.One2many(
        "l10n.es.tgss.contribution_account",
        "owner_id",
        "Contribution accounts",
        auto_join=True,
        domain=lambda self: [("owner_model", "=", self._name)],
        help="Company accounts to interact with the Social Security.")

    @api.multi
    def unlink(self):
        """Remove related contribution accounts before removing self.

        This emulates a ``ondelete="cascade"``, but that cannot be used because
        we do not use a ``Many2one`` field in the other table.
        """
        self.mapped("contribution_account_ids").unlink()
        return super(CompanyABC, self).unlink()


class PersonABC(models.AbstractModel):
    """Models inheriting this ABC will have a personal affiliation number.

    Submodels need to add this field: ``contribution_account_owner_id``.

    It is used for the domain of :attr:`~.contribution_account_id` to restrict
    the account selection to the company where this person works. That's why
    you will need to expose it with :attr:`~.model_name` in the view, although
    it can be hidden.

    Normally it will be just a reference field to another field already
    available in the model. You do not need to store it.
    """
    _description = "Base for models with a single contribution account"
    _name = "l10n.es.tgss.contribution_account.person.abc"
    _inherit = "l10n.es.tgss.contribution_account.common.abc"

    contribution_account_id = fields.Many2one(
        "l10n.es.tgss.contribution_account",
        "Contribution account",
        ondelete="restrict",
        domain="""[
            ("owner_id", "=", contribution_account_owner_id),
            ("owner_model", "=", model_name),
        ]""",
        context="""{
            "default_owner_id": contribution_account_owner_id,
            "default_owner_model": model_name,
        }""",
        help="Company account where this person is hired.")
    affiliation_number = fields.Char(
        size=12,
        help="Personal account code to interact with the Social Security.")

    @api.multi
    @api.constrains("affiliation_number")
    def _check_affiliation_number(self):
        """Ensure a good affiliation number is saved."""
        check_code = self.env["l10n.es.tgss.contribution_account"].check_code
        for s in self.filtered("affiliation_number"):
            check_code(s.affiliation_number, getattr(s, "is_company", False))
