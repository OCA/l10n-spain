# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .logista_master_data import (
    LOGISTA_FREIGHT_TYPES,
    LOGISTA_NOTIFICATION_TYPES,
)


class ResPartner(models.Model):
    _inherit = "res.partner"

    logista_customer_code = fields.Char(
        string="Logista Consignee Code",
        size=15,
        copy=False,
        help=(
            "Optional consignee CustomerCode (max 15 chars) sent in "
            "Logista Parcel API v5."
        ),
    )
    logista_freight_type = fields.Selection(
        selection=LOGISTA_FREIGHT_TYPES,
        string="Logista Default Freight Type",
        help="Default freight terms (Prepaid / Collect) for this partner.",
    )
    logista_notification_type = fields.Selection(
        selection=LOGISTA_NOTIFICATION_TYPES,
        string="Logista Notification Preference",
        default="none",
        help="Status notification preference (SMS / Email) for Logista Parcel.",
    )
