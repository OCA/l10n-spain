# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nEsAeatMod322Group(models.Model):

    _name = "l10n.es.aeat.mod322.group"
    _description = "Grupo de IVA para el modelo 322"

    name = fields.Char(required=True, help="Number assigned by AEAT to the group")
    main_company_id = fields.Many2one(
        "res.company", required=True, default=lambda r: r.env.company.id
    )
    company_ids = fields.Many2many("res.company", default=lambda r: r.env.companies.ids)
    vinculated_partner_ids = fields.Many2many(
        "res.partner", help="""Use this field if you have other vinculated partners"""
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name, main_company_id)", "Name must be unique!"),
    ]
