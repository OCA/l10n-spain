# Copyright 2026 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, exceptions, fields, models


class PosOder(models.Model):
    _inherit = "pos.order"

    # It is necessary to define a group to prevent point_of_sale at
    # https://github.com/odoo/odoo/blob/404b839566fbc1a72d3e68c7a02ddbfa3b18980d/addons/point_of_sale/models/pos_order.py# L1166  # noqa: E501
    # from returning an error when attempting to access the
    # l10n.es.aeat.sii.match.difference model of the field if the user does not have
    # sufficient permissions.
    sii_match_difference_ids = fields.One2many(groups="l10n_es_aeat.group_account_aeat")

    def contrast_aeat(self):
        invalid_orders = self.filtered(
            lambda x: not x.sii_enabled or x.aeat_state != "sent"
        )
        if invalid_orders:
            raise exceptions.UserError(
                _(
                    "The orders must be sent to SII in order to be matched."
                    "\nNon-matchable orders: %(order_names)s",
                    order_names=", ".join(i.name for i in invalid_orders),
                )
            )
        return super().contrast_aeat()
