# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class VerifactuDeveloper(models.Model):
    _name = "verifactu.developer"

    name = fields.Char(string="Developer Name", required=True)
    vat = fields.Char(string="Developer VAT", required=True)
    sif_name = fields.Char("SIF Name", default="Odoo", required=True)
    sif_id = fields.Char(string="SIF ID", default="11", required=True)
    version = fields.Char(default="1.0", required=True)
    installation_number = fields.Integer(default=1, required=True)
    responsible_declaration = fields.Binary(required=True)
