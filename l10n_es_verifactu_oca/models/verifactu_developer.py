# Copyright 2024 Aures TIC - Almudena de La Puente
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class VerifactuDeveloper(models.Model):
    _name = "verifactu.developer"
    _description = "VERI*FACTU developer"
    _inherit = "mail.thread"

    name = fields.Char(string="Developer Name", required=True, tracking=True)
    vat = fields.Char(string="Developer VAT", required=True, tracking=True)
    sif_name = fields.Char("SIF Name", required=True, tracking=True)
    version = fields.Char(default="1.0", required=True, tracking=True)
    responsibility_declaration = fields.Binary(attachment=True, copy=False)
