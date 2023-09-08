# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

fb2b_schema = "http://www.facturae.es/Facturae/Extensions/FaceB2BExtensionv1_1"


class AccountMove(models.Model):

    _inherit = "account.move"

    def _get_facturae_headers(self):
        result = super()._get_facturae_headers()
        if self.partner_id.l10n_es_facturae_sending_code == "faceb2b":
            result += ' xmlns:fb2b="%s"' % fb2b_schema
        return result

    def _facturae_has_extensions(self):
        return (
            self.partner_id.l10n_es_facturae_sending_code == "faceb2b"
            or super()._facturae_has_extensions()
        )
