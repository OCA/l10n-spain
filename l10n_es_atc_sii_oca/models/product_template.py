# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sii_exempt_cause = fields.Selection(
        selection_add=[
            ("E8", "[E8] Other exemptions (ATC)"),
        ],
        ondelete={"E8": "set null"},
    )
