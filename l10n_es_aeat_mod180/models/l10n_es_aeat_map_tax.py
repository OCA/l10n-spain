from odoo import _, api, exceptions, models


class L10nEsAeatMapTax(models.Model):
    _inherit = "l10n.es.aeat.map.tax"

    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if self.env.context.get("from_init_hook_180", False):
            default["model"] = 180
        return super().copy(default)

    @api.constrains("date_from", "date_to", "model")
    def _unique_date_range(self):
        for tax_map in self:
            domain = [("id", "!=", tax_map.id), ("model", "=", tax_map.model)]
            if tax_map.date_from and tax_map.date_to:
                domain += [
                    "|",
                    "&",
                    ("date_from", "<=", tax_map.date_to),
                    ("date_from", ">=", tax_map.date_from),
                    "|",
                    "&",
                    ("date_to", "<=", tax_map.date_to),
                    ("date_to", ">=", tax_map.date_from),
                    "|",
                    "&",
                    ("date_from", "=", False),
                    ("date_to", ">=", tax_map.date_from),
                    "|",
                    "&",
                    ("date_to", "=", False),
                    ("date_from", "<=", tax_map.date_to),
                ]
            elif tax_map.date_from:
                domain += [("date_to", ">=", tax_map.date_from)]
            elif tax_map.date_to:
                domain += [("date_from", "<=", tax_map.date_to)]
            date_lst = tax_map.search(domain)
            if date_lst:
                raise exceptions.Warning(
                    _(
                        """Error! Las fechas de los registros
                         se solapan con un registro existente."""
                    )
                )
