from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    ecoembes_inscription = fields.Char(related="company_id.ecoembes_inscription")
    ecoembes_partner_member = fields.Char(related="company_id.ecoembes_partner_member")
