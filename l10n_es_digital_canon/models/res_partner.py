# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_digital_canon_exempt = fields.Boolean(
        string="Exempt from digital canon",
        help="Enable this option if the customer or vendor is exempt from the "
        "digital canon.",
        default=False,
    )
    digital_canon_exempt_type = fields.Selection(
        selection=[
            ("administracion", "Administraciones Públicas"),
            (
                "certificado",
                "Personas jurídicas o físicas con certificado de exceptuación",
            ),
            ("productores", "Productores audiovisuales y/o productores fonográficos"),
            ("no_desglosa", "Proveedor nacional que no desglosa el canon"),
        ],
        string="Exemption type",
        help="Type of exemption applied to the customer/vendor for the digital canon.",
    )
