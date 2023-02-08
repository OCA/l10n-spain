# Copyright 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# Copyright 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2015 Tecon
# Copyright 2015 Juanjo Algaz (MalagaTIC)
# Copyright 2015 Omar Castiñeira (Comunitea)
# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Creu Blanca
# Copyright 2023 Jan Tugores (jan.tugores@qubiq.es)
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
    def create(self, vals):
        if not vals.get("move_id", False):
            move = self._get_move_from_context()
            vals.update(
                {
                    "move_id": move.id,
                }
            )
        res = super().create(vals)
        return res

    def create_facturae_file(self):
        # Validating mandatory fields
        self.move_id.validate_facturae_fields()
        skip_signature = self.env.context.get("skip_signature", False)
        if self.firmar_facturae and not skip_signature:
            move_file = self.env.ref("l10n_es_facturae.report_facturae_signed")._render(
                self.move_id.ids
            )[0]
            file_name = ("facturae_" + self.move_id.name + ".xsig").replace("/", "-")
        else:
            move_file = self.env.ref("l10n_es_facturae.report_facturae")._render(
                self.move_id.ids
            )[0]
            file_name = ("facturae_" + self.move_id.name + ".xml").replace("/", "-")
        file = base64.b64encode(move_file)
        self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": file,
                "res_model": "account.move",
                "res_id": self.move_id.id,
                "mimetype": "application/xml",
            }
        )
        self.write(
            {
                "facturae": file,
                "facturae_fname": file_name,
                "state": "second",
            }
        )
        self.move_id.write(
            {"l10n_es_facturae_attachment": file, "facturae_fname": file_name}
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "create.facturae",
            "view_mode": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    def _get_move_from_context(self):
        """
        Returns the move_id record from context
        """
        move_ids = self.env.context.get("active_ids", [])
        if not move_ids or len(move_ids) > 1:
            raise UserError(_("You can only select one move to export"))
        active_model = self.env.context.get("active_model", False)
        assert active_model == "account.move", "Bad context propagation"
        move = self.env["account.move"].browse(move_ids[0]).ensure_one()
        return move
