# Copyright 2015 Tecon
# Copyright 2015 Omar Castiñeira (Comunitea)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    facturae_version = fields.Selection(
        [("3_2", "3.2"), ("3_2_1", "3.2.1"), ("3_2_2", "3.2.2")]
    )
    facturae_hide_discount = fields.Boolean(
        string="Hide Facturae discount",
        help="The unit price will be recalculated applying the discount",
    )
    facturae_registration_book = fields.Char(size=20)
    facturae_registration_location = fields.Char(size=20)
    facturae_registration_sheet = fields.Char(size=20)
    facturae_registration_folio = fields.Char(size=20)
    facturae_registration_section = fields.Char(size=20)
    facturae_registration_volume = fields.Char(size=20)
    facturae_registration_additional = fields.Char(size=20)
