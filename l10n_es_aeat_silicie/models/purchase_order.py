# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cae = fields.Char(
        related='partner_id.cae'
    )

    arc = fields.Char(
        string='ARC',
    )
