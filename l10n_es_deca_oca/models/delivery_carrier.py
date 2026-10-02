# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    carrier_contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="Carrier contact",
    )
