# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    sigaus_enable = fields.Boolean()
    sigaus_date_from = fields.Date(help="SIGAUS can only be applied from this date.")
    sigaus_show_in_reports = fields.Boolean(
        string="Show detailed SIGAUS amount in report lines",
        help="If active, SIGAUS amount is shown in reports.",
    )

    @api.constrains("sigaus_enable", "sigaus_date_from")
    def _check_sigaus_date(self):
        if self.filtered(lambda a: a.sigaus_enable and not a.sigaus_date_from):
            raise ValidationError(
                _("'Sigaus Date From' is mandatory for companies with SIGAUS enabled.")
            )
