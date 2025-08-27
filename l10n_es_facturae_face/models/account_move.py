# (Copyright) 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


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

    def _edi_create_exchange_record_vals(self, exchange_type):
        result = super()._edi_create_exchange_record_vals(exchange_type)
        if exchange_type == self.env.ref(
            "l10n_es_facturae_face.facturae_face_update_exchange_type"
        ):
            related_record = self._get_exchange_record(
                self.env.ref("l10n_es_facturae_face.facturae_exchange_type"),
                self.env.ref("l10n_es_facturae_face.face_backend"),
            )
            if not related_record:
                raise UserError(_("Exchange record cannot be found for FACe"))
            result.update(
                {"edi_exchange_state": "input_pending", "parent_id": related_record.id}
            )
        return result

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
        if (
            self.partner_id.l10n_es_facturae_sending_code == "face"
            and not self.partner_id.organo_gestor
        ):
            raise ValidationError(_("Organo Gestor not provided"))
        if (
            self.partner_id.l10n_es_facturae_sending_code == "face"
            and not self.partner_id.unidad_tramitadora
        ):
            raise ValidationError(_("Unidad Tramitadora not provided"))
        if (
            self.partner_id.l10n_es_facturae_sending_code == "face"
            and not self.partner_id.oficina_contable
        ):
            raise ValidationError(_("Oficina Contable not provided"))
        return

    def _get_l10n_es_facturae_face_backend(self):
        return self.env.ref("l10n_es_facturae_face.face_backend")

    def _get_l10n_es_facturae_face_exchange_record_vals(self):
        return {
            "model": self._name,
            "res_id": self.id,
        }

    def _post(self, soft=True):
        result = super()._post(soft=soft)
        for record in self:
            if record.edi_disable_auto:
                continue
            partner = record.partner_id
            if record.move_type not in ["out_invoice", "out_refund"]:
                continue
            if not partner.facturae or not partner.l10n_es_facturae_sending_code:
                continue
            backend = record._get_l10n_es_facturae_face_backend()
            if not backend:
                continue
            exchange_type = self.env.ref("l10n_es_facturae_face.facturae_exchange_type")
            # We check fields now to raise an error to the user, otherwise the
            # error will be raising silently in the queue job.
            record.validate_facturae_fields()
            if record._has_exchange_record(exchange_type, backend):
                continue
            exchange_record = backend.create_record(
                exchange_type.code,
                record._get_l10n_es_facturae_face_exchange_record_vals(),
            )
            if exchange_record.edi_exchange_state == "new":
                exchange_record.action_exchange_generate()
        return result
