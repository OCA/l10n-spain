# Copyright 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# Copyright 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2015 Tecon
# Copyright 2015 Juanjo Algaz (MalagaTIC)
# Copyright 2015 Omar Castiñeira (Comunitea)
# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo import _, fields, models
from odoo.exceptions import UserError


class Log(Exception):
    def __init__(self):
        self.content = ""
        self.error = False

    def add(self, s, error=True):
        self.content = self.content + s
        if error:
            self.error = error

    def __call__(self):
        return self.content

    def __str__(self):
        return self.content


class CreateFacturae(models.TransientModel):
    _name = "create.facturae"
    _description = "Create Facturae Wizard"

    facturae = fields.Binary("Facturae file", readonly=True)
    facturae_fname = fields.Char("File name", size=64)
    note = fields.Text("Log")
    state = fields.Selection(
        [("first", "First"), ("second", "Second")],
        readonly=True,
        default="first",
    )
    firmar_facturae = fields.Boolean(
        "Do you want to digitally sign the generated file?",
        help="Requires certificate in the company file",
        default=True,
    )

    def create_facturae_file(self):
        log = Log()
        move_ids = self.env.context.get("active_ids", [])
        if not move_ids or len(move_ids) > 1:
            raise UserError(_("You can only select one move to export"))
        active_model = self.env.context.get("active_model", False)
        assert active_model == "account.move", "Bad context propagation"
        move = self.env["account.move"].browse(move_ids[0]).ensure_one()
        if self.firmar_facturae:
            move_file = self.env.ref("l10n_es_facturae.report_facturae_signed")._render(
                move.ids
            )[0]
            file_name = ("facturae_" + move.name + ".xsig").replace("/", "-")
        else:
            move_file = self.env.ref("l10n_es_facturae.report_facturae")._render(
                move.ids
            )[0]
            file_name = ("facturae_" + move.name + ".xml").replace("/", "-")
        file = base64.b64encode(move_file)
        self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": file,
                "res_model": "account.move",
                "res_id": move.id,
                "mimetype": "application/xml",
            }
        )
        log.add(_("Export successful\n\nSummary:\nMove number: %s\n") % move.name)
        self.write(
            {
                "note": log(),
                "facturae": file,
                "facturae_fname": file_name,
                "state": "second",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "create.facturae",
            "view_mode": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }
