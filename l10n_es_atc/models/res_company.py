import logging

from odoo import api, fields, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    atc_public_way = fields.Char("Public Way")

    @api.model_create_multi
    def create(self, vals_list):
        """Create the ATC sequences of the new companies, as l10n_es_aeat does
        for the AEAT models (whose names it looks for as l10n.es.aeat.*)."""
        companies = super().create(vals_list)
        models = (
            self.env["ir.model"]
            .sudo()
            .search([Domain("model", "=like", "l10n.es.atc.%.report")])
        )
        for model in models:
            try:
                self.env[model.model]._register_hook(companies=companies)
            except Exception as e:  # noqa: BLE001
                _logger.debug(e)
        return companies
