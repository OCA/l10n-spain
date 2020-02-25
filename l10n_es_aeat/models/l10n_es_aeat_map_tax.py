# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import _, api, exceptions, fields, models


class L10nEsAeatMapTax(models.Model):
    _name = "l10n.es.aeat.map.tax"
    _description = "AEAT tax mapping"

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")
    map_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.map.tax.line",
        inverse_name="map_parent_id",
        string="Map lines",
        required=True,
    )
    model = fields.Integer(string="AEAT Model", required=True)

    @api.constrains("date_from", "date_to")
    def _unique_date_range(self):
        for map_tax in self:
            domain = [("id", "!=", map_tax.id)]
            if map_tax.date_from and map_tax.date_to:
                domain += [
                    "|",
                    "&",
                    ("date_from", "<=", map_tax.date_to),
                    ("date_from", ">=", map_tax.date_from),
                    "|",
                    "&",
                    ("date_to", "<=", map_tax.date_to),
                    ("date_to", ">=", map_tax.date_from),
                    "|",
                    "&",
                    ("date_from", "=", False),
                    ("date_to", ">=", map_tax.date_from),
                    "|",
                    "&",
                    ("date_to", "=", False),
                    ("date_from", "<=", map_tax.date_to),
                ]
            elif map_tax.date_from:
                domain += [("date_to", ">=", map_tax.date_from)]
            elif map_tax.date_to:
                domain += [("date_from", "<=", map_tax.date_to)]
            date_lst = map_tax.search(domain)
            if date_lst:
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
