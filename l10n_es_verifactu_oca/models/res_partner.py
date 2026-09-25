# Copyright 2024 Aures TIC - Jose Zambudio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    verifactu_enabled = fields.Boolean(
        compute="_compute_aeat_sending_enabled", string="VERI*FACTU enabled"
    )

    @api.depends("company_id")
    def _compute_aeat_sending_enabled(self):
        res = super()._compute_aeat_sending_enabled()
        verifactu_enabled = any(self.env.companies.mapped("verifactu_enabled"))
        for partner in self:
            partner.verifactu_enabled = (
                partner.company_id.verifactu_enabled
                if partner.company_id
                else verifactu_enabled
            )
            if partner.verifactu_enabled:
                partner.aeat_sending_enabled = True
        return res

    def _is_valid_verifactu_receiver(self):
        """Whether this partner can be the destinatario of a registro de alta.

        Document types that must identify the customer (F1, F3, R1-R4) need
        either a Spanish NIF or a foreign identifier stating its country: an
        ``IDOtro`` without ``CodigoPais`` declares a document of nowhere.
        """
        self.ensure_one()
        if not self.vat:
            return False
        country_code, _identifier_type, identifier = self._parse_aeat_vat_info()
        return bool(identifier and (country_code == "ES" or self.country_id.code))
