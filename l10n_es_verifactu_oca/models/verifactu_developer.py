# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VerifactuDeveloper(models.Model):
    _name = "verifactu.developer"
    _inherit = "mail.thread"

    name = fields.Char(string="Developer Name", required=True, tracking=True)
    vat = fields.Char(string="Developer VAT", required=True, tracking=True)
    sif_name = fields.Char("SIF Name", required=True, tracking=True)
    version = fields.Char(default="1.0", required=True, tracking=True)
    responsibility_declaration = fields.Binary(
        attachment=True, copy=False, tracking=True
    )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_used_developer(self):
        if self.env["res.company"].search(
            [("verifactu_developer_id", "in", self.ids)], limit=1
        ):
            raise UserError(
                _("You cannot delete a developer that is in use by a company.")
            )
