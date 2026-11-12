# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    sii_enabled = fields.Boolean(
        related="company_id.sii_enabled",
        readonly=True,
    )
    sii_available_regime_codes_sale = fields.Char(
        compute="_compute_sii_available_regime_codes",
        help="Technical field for the dynamic selection of the sale key",
    )
    sii_available_regime_codes_purchase = fields.Char(
        compute="_compute_sii_available_regime_codes",
        help="Technical field for the dynamic selection of the purchase key",
    )
    sii_regime_code_sale = fields.Selection(
        selection="_selection_sii_regime_code",
        string="Forced SII Registration Key for Sales",
        help="Only for operations whose key does not come from their taxes (e.g. "
        "group of entities or business premises leases). It becomes the main "
        "key of the invoices with this fiscal position, and the keys of their "
        "taxes the additional ones. Leave it empty to take the keys from the "
        "taxes (e.g. exports or OSS) or the general regime.",
    )
    sii_regime_code_purchase = fields.Selection(
        selection="_selection_sii_regime_code",
        string="Forced SII Registration Key for Purchases",
        help="Only for operations whose key does not come from their taxes (e.g. "
        "group of entities, business premises leases or imports without DUA). "
        "It becomes the main key of the invoices with this fiscal position, and "
        "the keys of their taxes the additional ones. Leave it empty to take "
        "the keys from the taxes (e.g. intra-community acquisitions) or the "
        "general regime.",
    )
    sii_partner_identification_type = fields.Selection(
        selection=[("1", "National"), ("2", "Intracom"), ("3", "Export")],
        string="SII partner Identification Type",
    )

    @api.model
    def _selection_sii_regime_code(self):
        return self.env["account.tax"]._l10n_es_regime_code_selection()

    @api.depends("company_id")
    def _compute_sii_available_regime_codes(self):
        for position in self:
            company = position.company_id or self.env.company
            position.sii_available_regime_codes_sale = ",".join(
                company._l10n_es_regime_available_codes("sale")
            )
            position.sii_available_regime_codes_purchase = ",".join(
                company._l10n_es_regime_available_codes("purchase")
            )

    def _get_sii_forced_regime_code(self, use):
        """Return the registration key forced for sales or purchases, if any."""
        if not self:
            return False
        self.ensure_one()
        if use == "purchase":
            return self.sii_regime_code_purchase
        return self.sii_regime_code_sale
