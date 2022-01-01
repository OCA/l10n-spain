# Copyright (C) 2020 C2i Change 2 improve (<http://c2i.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Channel(models.Model):
    _inherit = "slide.channel"

    fundae_bonificable = fields.Boolean(string="Bonificable")
    fundae_code = fields.Char(string="Código")
    fundae_type = fields.Selection(
        [
            ("teletraining", "Teleformación"),
            ("classroom", "Presencial"),
            ("mixed", "Mixta"),
        ],
        "Modalidad",
        default="teletraining",
    )
    fundae_guiapdf = fields.Binary(string="PDF Guía didáctica", attachment=True)
    fundae_guiapdffile = fields.Char("Archivo Guía didáctica")
    fundae_profesor_id = fields.Many2one(
        "res.partner", ondelete="set null", string="Profesor", index=True
    )
    fundae_inspector_id = fields.Many2one(
        "res.users", ondelete="set null", string="Inspector de Fundae", index=True
    )
    encuesta_id = fields.Many2one(
        "survey.survey", ondelete="set null", string="Encuestas", index=True
    )
    fundae_group_ids = fields.One2many(
        "slide.channel.group",
        "channel_id",
        string="Grupos",
    )
