# Copyright 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# Copyright 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2015 Tecon
# Copyright 2015 Juanjo Algaz (MalagaTIC)
# Copyright 2015 Omar Castiñeira (Comunitea)
# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Creu Blanca
# Copyright 2023 Jan Tugores (jan.tugores@qubiq.es)
# Copyright 2023 Pol Reig (pol.reig@qubiq.es)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreateFacturae(models.TransientModel):
    _name = "create.facturae"
    _description = "Create Facturae Wizard"

    move_id = fields.Many2one("account.move")
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

    @api.model
    def default_get(self, fields):
        res = super(CreateFacturae, self).default_get(fields)
        # obtains the move_id record from context
        move_ids = self.env.context.get("active_ids", [])
        if not move_ids:
            raise UserError(_("You must select a move to export"))
        res.update({"move_id": move_ids[0]})
        return res

    def create_facturae_file(self):
        move = self.move_id
        # Validating mandatory fields
        move.validate_facturae_fields()
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
        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": file,
                "res_model": "account.move",
                "res_id": move.id,
                "mimetype": "application/xml",
            }
        )
        note = _("Export successful\n\nSummary:\nMove number: %s\n") % move.name
        self.write(
            {
                "note": note,
                "facturae": attachment.datas,
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
