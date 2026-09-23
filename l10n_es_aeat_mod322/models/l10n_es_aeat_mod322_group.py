# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class L10nEsAeatMod322Group(models.Model):
    _name = "l10n.es.aeat.mod322.group"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Grupo de IVA para el modelo 322"

    name = fields.Char(
        string="Group Number",
        required=True,
        tracking=True,
        help="Number assigned by AEAT to the group",
    )
    main_company_id = fields.Many2one(
        "res.company",
        string="Dominant Company",
        required=True,
        tracking=True,
        default=lambda r: r.env.company.id,
    )
    company_ids = fields.Many2many(
        "res.company",
        string="Dependent Companies",
        tracking=True,
        default=lambda r: (r.env.companies - r.env.company).ids,
    )
    vinculated_partner_ids = fields.Many2many(
        "res.partner",
        tracking=True,
        help="""Use this field if you have other vinculated partners""",
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name, main_company_id)", "Name must be unique!"),
    ]

    @api.constrains("main_company_id", "company_ids")
    def _check_group_companies(self):
        for group in self:
            if group.main_company_id in group.company_ids:
                raise ValidationError(
                    self.env._(
                        "The dominant company can't also be a dependent company."
                    )
                )
            companies = group.main_company_id | group.company_ids
            other_group = self.search(
                [
                    ("id", "!=", group.id),
                    "|",
                    ("main_company_id", "in", companies.ids),
                    ("company_ids", "in", companies.ids),
                ],
                limit=1,
            )
            if other_group:
                raise ValidationError(
                    self.env._(
                        "A company can only belong to one VAT group. "
                        "Group %(group)s already includes some of these companies.",
                        group=other_group.name,
                    )
                )
