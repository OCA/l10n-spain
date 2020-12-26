# Copyright (C) 2020 C2i Change 2 improve (<http://c2i.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SlideChannelGroup(models.Model):
    _name = "slide.channel.group"
    _description = "Grupos formativos de FUNDAE"

    channel_id = fields.Many2one("slide.channel", string="Channel")
    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Código", required=True)
