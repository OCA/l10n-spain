# (Copyright) 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_es_facturae_status = fields.Selection(
        selection_add=[
            ("efact-SENT", "Sended"),
            ("efact-VALIDATED", "Validated"),
            ("efact-REGISTERED", "Registered"),
            ("efact-DELIVERED", "Delivered"),
            ("efact-ANNOTATED", "Registered on RFC"),
            ("efact-RECEIVED", "Received"),
            ("efact-ACCEPTED", "Accepted"),
            ("efact-RECOGNISED", "Accounted obligation"),
            ("efact-REJECTED", "Rejected"),
            ("efact-PAID", "Paid"),
            ("efact-CANCELED", "Canceled"),
        ]
    )

    @api.model
    def _get_l10n_es_facturae_excluded_status(self):
        return super()._get_l10n_es_facturae_excluded_status() + [
            "efact-REJECTED",
        ]
