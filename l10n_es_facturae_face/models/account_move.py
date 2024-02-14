# (Copyright) 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_es_facturae_status = fields.Selection(
        selection=[
            ("face-1200", "Registered on REC"),
            ("face-1300", "Registered on RCF"),
            ("face-2400", "Accepted"),
            ("face-2500", "Paid"),
            ("face-2600", "Rejected"),
            ("face-3100", "Cancellation approved"),
        ],
        tracking=True,
        readonly=True,
        string="Facturae status",
        copy=False,
    )
    l10n_es_facturae_cancellation_status = fields.Selection(
        selection=[
            ("face-4100", "Not requested"),
            ("face-4200", "Cancellation requested"),
            ("face-4300", "Cancellation accepted"),
            ("face-4400", "Cancellation rejected"),
        ],
        tracking=True,
        readonly=True,
        string="Facturae cancellation status",
        copy=False,
    )

    def _get_edi_missing_records(self):
        result = super()._get_edi_missing_records()
        if result:
            return result
        if self.move_type not in ["out_invoice", "out_refund"]:
            return False
        partner = self.partner_id
        if not partner.facturae or not partner.l10n_es_facturae_sending_code:
            return False
        return not self._has_exchange_record(
            self.env.ref("l10n_es_facturae_face.facturae_exchange_type"),
            self.env.ref("l10n_es_facturae_face.backend_facturae"),
        )

    @api.model
    def _edi_missing_records_fields(self):
        result = super()._edi_missing_records_fields()
        return result + [
            "l10n_es_facturae_status",
            "partner_id.l10n_es_facturae_sending_code",
        ]

    def _has_exchange_record_domain(
        self, exchange_type, backend=False, extra_domain=False
    ):
        domain = super()._has_exchange_record_domain(
            exchange_type, backend=backend, extra_domain=extra_domain
        )
        if exchange_type == self.env.ref(
            "l10n_es_facturae_face.facturae_exchange_type"
        ):
            domain += [
                "|",
                ("l10n_es_facturae_status", "=", False),
                (
                    "l10n_es_facturae_status",
                    "not in",
                    self._get_l10n_es_facturae_excluded_status(),
                ),
            ]
        return domain

    @api.model
    def _get_l10n_es_facturae_excluded_status(self):
        return [
            "face-2600",
            "face-3100",
        ]

    def validate_facturae_fields(self):
        super().validate_facturae_fields()
        if not self.partner_id.organo_gestor:
            raise ValidationError(_("Organo Gestor not provided"))
        return
