# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
import logging
import traceback

from odoo import api, fields, models

_logger = logging.getLogger()


class AeatTax(models.Model):
    _name = "aeat.tax"
    _description = "AEAT Tax"
    _order = "name"

    name = fields.Char()
    xmlid = fields.Char()

    @api.model
    def update_taxes(self):
        try:
            chart_template = self.env["account.chart.template"].sudo()
            taxes = {}
            data = chart_template._parse_csv("es_common", "account.tax", "l10n_es")
            for key in data:
                taxes[key] = data[key].get("description@es") or data[key]["description"]
            self._update_taxes(taxes)
        except Exception:
            _logger.error(traceback.format_exc())
            raise

    def _update_taxes(self, tax_data):
        taxes = self.env["aeat.tax"].search([])
        taxes.filtered(lambda x: x.xmlid not in tax_data).unlink()
        taxes._load_records(
            [
                {
                    "xml_id": f"l10n_es_aeat.{key}",
                    "noupdate": True,
                    "values": {"xmlid": key, "name": name},
                }
                for key, name in tax_data.items()
            ],
            update=True,
        )
