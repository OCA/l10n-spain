# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

fb2b_schema = "http://www.facturae.es/Facturae/Extensions/FaceB2BExtensionv1_1"


class AccountMove(models.Model):

    _inherit = "account.move"
    l10n_es_facturae_status = fields.Selection(
        selection_add=[
            ("faceb2b-1200", "Registered on broker FACeB2B"),
            ("faceb2b-1300", "Registered on customer platform"),
            ("faceb2b-2500", "Paid"),
            ("faceb2b-2600", "Rejected"),
            ("faceb2b-3100", "Cancellation approved"),
        ],
    )

    l10n_es_facturae_cancellation_status = fields.Selection(
        selection_add=[
            ("faceb2b-4200", "Cancellation requested"),
            ("faceb2b-4300", "Cancellation accepted"),
            ("faceb2b-4400", "Cancellation rejected"),
        ],
    )

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
