# (Copyright) 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_es_facturae_status = fields.Selection(
        selection_add=[
            ("face-1200", "Registered on REC"),
            ("face-1300", "Registered on RCF"),
            ("face-2400", "Accepted"),
            ("face-2500", "Payed"),
            ("face-2600", "Rejected"),
            ("face-3100", "Cancellation approved"),
        ]
    )
    l10n_es_facturae_cancellation_status = fields.Selection(
        selection_add=[
            ("face-4100", "Not requested"),
            ("face-4200", "Cancellation requested"),
            ("face-4300", "Cancellation accepted"),
            ("face-4400", "Cancellation rejected"),
        ]
    )

    def _get_l10n_es_facturae_backend(self):
        if self.partner_id.l10n_es_facturae_sending_code == "face":
            return self.env.ref("l10n_es_facturae_face.face_backend")
        return super()._get_l10n_es_facturae_backend()

    @api.model
    def _get_l10n_es_facturae_excluded_status(self):
        return super()._get_l10n_es_facturae_excluded_status() + [
            "face-2600",
            "face-3100",
        ]
