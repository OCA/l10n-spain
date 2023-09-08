# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    l10n_es_facturae_sending_code = fields.Selection(
        selection_add=[("faceb2b", "FACe B2B")]
    )
    facturae_faceb2b_dire = fields.Char()

    def _get_facturae_backend(self):
        if self.l10n_es_facturae_sending_code == "faceb2b":
            return self.env.ref("l10n_es_facturae_faceb2b.faceb2b_backend")
        return super()._get_facturae_backend()

    def _get_check_facturae_sending_codes(self):
        return super()._get_check_facturae_sending_codes() + ["faceb2b"]

    def _get_facturae_exchange_type(self):
        if self.l10n_es_facturae_sending_code == "faceb2b":
            return self.env.ref(
                "l10n_es_facturae_faceb2b.facturae_faceb2b_exchange_type"
            )
        return super()._get_facturae_exchange_type()
