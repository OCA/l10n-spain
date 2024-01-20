# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
import logging
import traceback

from odoo import api, fields, models

_logger = logging.getLogger()


class AeatAccount(models.Model):
    _name = "aeat.account"
    _description = "AEAT Account"
    _order = "name"

    name = fields.Char()
    xmlid = fields.Char()

    @api.model
    def update_accounts(self):
        try:
            chart_template = self.env["account.chart.template"].sudo()
            accounts = {}
            data = chart_template._parse_csv("es_common", "account.account", "l10n_es")
            for key in data:
                accounts[
                    key
                ] = f"{data[key]['code']} - {data[key].get('name@es') or data[key]['name']}"
            self._update_accounts(accounts)
        except Exception:
            _logger.error(traceback.format_exc())
            raise

    def _update_accounts(self, account_data):
        accounts = self.env["aeat.account"].search([])
        accounts.filtered(lambda x: x.xmlid not in account_data).unlink()
        accounts._load_records(
            [
                {
                    "xml_id": f"l10n_es_aeat.{key}",
                    "noupdate": True,
                    "values": {"xmlid": key, "name": name},
                }
                for key, name in account_data.items()
            ],
            update=True,
        )
