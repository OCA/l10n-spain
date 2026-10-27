# Copyright 2026 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    siltra_leave_type_id = fields.Many2one("hr.leave.type")
    ss_number_ids = fields.One2many(
        "res.company.seguridad.social", inverse_name="company_id"
    )


class ResCompanySeguridadSocial(models.Model):
    _name = "res.company.seguridad.social"
    _description = "Número de la Seguridad Social de la empresa"

    company_id = fields.Many2one(
        "res.company", string="Empresa", required=True, ondelete="cascade"
    )
    ss_number = fields.Char(
        string="Número de la Seguridad Social", required=True, copy=False
    )
