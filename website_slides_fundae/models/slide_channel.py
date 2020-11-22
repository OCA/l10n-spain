# Copyright (C) 2020 C2i Change 2 improve (<http://c2i.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Channel(models.Model):
    _inherit = "slide.channel"

    channel_type = fields.Selection(
        selection_add=[("bonificable", "Formación bonificable"), ("documentation",)],
        ondelete={
            "bonificable": "set default",
            "documentation": lambda r: r.write({"channel_type": "training"}),
        },
    )
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
    profesor_id = fields.Many2one(
        "res.partner", ondelete="set null", string="Profesor", index=True
    )
    inspector_id = fields.Many2one(
        "res.users", ondelete="set null", string="Inspector de Fundae", index=True
    )
    event_id = fields.Many2one(
        "event.event", ondelete="set null", string="Evento", index=True
    )
    encuesta_id = fields.Many2one(
        "survey.survey", ondelete="set null", string="Encuestas", index=True
    )
    fundae_group_ids = fields.One2many(
        string="Grupos",
		comodel_name="slide.channel.group",
		inverse_name="id",
    )

    nbr_teleconference = fields.Integer(
        "Videoconferencias", compute="_compute_slides_statistics", store=True
    )
