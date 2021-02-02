# Copyright 2009-2017 Noviat.
# Copyright 2020 Tecnativa - Manuel Calero
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _get_intrastat_state(self):
        if not self:
            return False
        location = self
        locations = self
        while location.location_id:
            locations += location.location_id
            location = location.location_id
        warehouse = self.env["stock.warehouse"].search(
            [
                ("lot_stock_id", "in", locations.ids),
                ("partner_id.state_id", "!=", False),
            ],
            limit=1,
        )
        return warehouse.partner_id.state_id
