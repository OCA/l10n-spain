# Copyright (C) 2020 C2i Change 2 improve (<http://c2i.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "slide.channel.partner"

    partner_bonificable = fields.Boolean(string="Bonificable", default=False)
    partner_profesor = fields.Boolean(string="Profesor", default=False)
    partner_inspector = fields.Boolean(string="Inspector", default=False)
