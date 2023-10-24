# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nEsSigausAmount(models.Model):
    _name = "l10n.es.sigaus.amount"
    _description = "Sigaus Amount"

    name = fields.Char(required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date()
    price = fields.Float(digits="Product Price", required=True)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            date_from = rec.date_from
            date_to = rec.date_to
            if date_to and date_to < date_from:
                raise ValidationError(
                    _("The ending date must not be prior to the starting date.")
                )
            domain = [
                ("id", "!=", rec.id),
                "|",
                "|",
                "|",
                "|",
                "&",
                ("date_from", "<=", date_from),
                "|",
                ("date_to", ">=", date_from),
                ("date_to", "=", False),
                "&",
                ("date_from", "<=", date_to),
                ("date_to", ">=", date_to),
                "&",
                ("date_from", "<=", date_from),
                ("date_to", ">=", date_to),
                "&",
                ("date_from", ">=", date_from),
                ("date_to", "<=", date_to),
                "&",
                ("date_from", ">=", date_from),
                ("date_from", "<=", date_to),
            ]

            if self.search_count(domain) > 0:
                raise ValidationError(_("You can not have overlapping date ranges."))

    @api.model
    def get_sigaus_amount(self, date):
        l10n_es_sigaus_amount = self.search(
            [
                ("date_from", "<=", date),
                "|",
                ("date_to", ">=", date),
                ("date_to", "=", False),
            ],
            limit=1,
        )
        if not l10n_es_sigaus_amount:
            raise ValidationError(
                _(
                    "There is not a SIGAUS price set for the date: {}. Please, go to "
                    "Invoicing > Configuration > L10n Es Sigaus Amount and make sure "
                    "that the date is include in one of the configured date ranges."
                ).format(date)
            )
        return l10n_es_sigaus_amount.price
