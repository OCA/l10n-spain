# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools import ormcache

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_agency_id = fields.Many2one("aeat.tax.agency", string="Tax Agency")
    representative_vat = fields.Char(
        string="L.R. VAT number",
        size=9,
        help="Legal Representative VAT number for all the AEAT reports of this "
        "company.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create immediately all the AEAT sequences when creating company."""
        companies = super().create(vals_list)
        models = (
            self.env["ir.model"]
            .sudo()
            .search([Domain("model", "=like", "l10n.es.aeat.%.report")])
        )
        for model in models:
            try:
                self.env[model.model]._register_hook(companies=companies)
            except Exception as e:
                _logger.debug(e)
        return companies

    @ormcache("self", "xmlid")
    def _get_tax_id_from_xmlid(self, xmlid):
        """Low level cached search for a tax given its template XML-ID and company."""
        self.ensure_one()
        return (
            xmlid
            and self.sudo()
            .env["ir.model.data"]
            .search(
                Domain.AND(
                    [
                        Domain("model", "=", "account.tax"),
                        Domain(
                            "module", "=", "account"
                        ),  # All is registered under this module
                        Domain("name", "=", f"{self.id}_{xmlid}"),
                    ]
                ),
            )
            .res_id
            or False
        )

    @ormcache("self", "xmlid")
    def _get_account_id_from_xmlid(self, xmlid):
        """Low level cached search for a tax given its account template and
        company.
        """
        self.ensure_one()
        return (
            xmlid
            and self.sudo()
            .env["ir.model.data"]
            .search(
                Domain.AND(
                    [
                        Domain("model", "=", "account.account"),
                        Domain(
                            "module", "=", "account"
                        ),  # All is registered under this module
                        Domain("name", "=", f"{self.id}_{xmlid}"),
                    ]
                ),
            )
            .res_id
            or False
        )
