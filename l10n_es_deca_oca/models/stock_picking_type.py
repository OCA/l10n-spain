# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_es_deca_enabled = fields.Boolean(
        string="Enable DeCA",
        help="Allows printing the DeCA report for incoming shipments.",
    )
