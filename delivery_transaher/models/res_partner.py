# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    transaher_portes_default = fields.Selection(
        selection=[
            ("default", "Use Delivery Method Default"),
            ("1", "1 - Freight Prepaid (Portes Pagados)"),
            ("2", "2 - Freight Collect (Portes Debidos)"),
        ],
        string="Transaher Freight Terms",
        default="default",
        help=(
            "Default freight payment terms (Portes Pagados / Debidos) "
            "for Transaher shipments to this partner."
        ),
    )
    transaher_postal_rep_code = fields.Char(
        string="Postal Repetition Code (Transaher)",
        size=5,
        copy=False,
        help=(
            "Optional postal repetition code according to Correos database "
            "(Field 5 of Datosentrada)."
        ),
    )
    transaher_delivery_notes = fields.Char(
        string="Transaher Delivery Observations",
        size=140,
        help=(
            "Default delivery instructions sent to Transaher "
            "(automatically split across Observations 1 & 2, max 70 chars each)."
        ),
    )
