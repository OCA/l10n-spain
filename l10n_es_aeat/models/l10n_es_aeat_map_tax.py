# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import _, api, exceptions, fields, models


class L10nEsAeatMapTax(models.Model):
    _name = "l10n.es.aeat.map.tax"
    _description = "AEAT tax mapping"

    date_from = fields.Date(string="From Date")
    date_from_search = fields.Date(compute="_compute_date_from_search", store=True)
    date_to = fields.Date(string="To Date")
    date_to_search = fields.Date(compute="_compute_date_to_search", store=True)
    map_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.map.tax.line",
        inverse_name="map_parent_id",
        string="Map lines",
        required=True,
    )
    model = fields.Integer(string="AEAT Model", required=True)

    @api.depends("date_from")
    def _compute_date_from_search(self):
        for record in self:
            record.date_from_search = record.date_from or "1900-01-01"

    @api.depends("date_to")
    def _compute_date_to_search(self):
        for record in self:
            record.date_to_search = record.date_to or "2999-12-31"

    @api.constrains("date_from", "date_to", "model")
    def _unique_date_range(self):
        for map_tax in self:
            domain = ["&", ("model", "=", map_tax.model), ("id", "!=", map_tax.id)]
            if self.date_from:
                domain.append(("date_to_search", ">=", map_tax.date_from))
            if self.date_to:
                domain.append(("date_from_search", "<=", map_tax.date_to))
            if map_tax.search(domain):
                raise exceptions.Warning(
                    _(
                        "Error! The dates of the record overlap with an "
                        "existing record."
                    )
                )

    def name_get(self):
        vals = []
        for record in self:
            name = "%s" % record.model
            if record.date_from or record.date_to:
                name += " ({}-{})".format(
                    record.date_from and fields.Date.to_date(record.date_from) or "",
                    record.date_to and fields.Date.to_date(record.date_to) or "",
                )
            vals.append(tuple([record.id, name]))
        return vals
