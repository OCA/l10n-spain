# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    # No foreign key: native picking unlink removes the parent BEFORE attachments.
    deca_source_id = fields.Many2oneReference(
        model_field="res_model",
        string="DeCA source",
        copy=False,
        readonly=True,
        index=True,
    )
    deca_version = fields.Integer(copy=False, readonly=True)
    deca_content_hash = fields.Char(copy=False, readonly=True)

    _sql_constraints = [
        (
            "deca_source_version_unique",
            "unique(deca_source_id, deca_version)",
            "A DeCA version already exists for this transfer.",
        ),
    ]
    _deca_provenance_fields = frozenset(
        {"deca_source_id", "deca_version", "deca_content_hash"}
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and (
            any(self._deca_provenance_fields.intersection(vals) for vals in vals_list)
            or any(
                "default_" + name in self.env.context
                for name in self._deca_provenance_fields
            )
        ):
            raise AccessError(
                self.env._("Only DeCA generation can set file provenance.")
            )
        return super().create(vals_list)

    @api.constrains(
        "deca_source_id",
        "deca_version",
        "deca_content_hash",
        "res_model",
        "res_id",
        "company_id",
        "public",
        "access_token",
        "type",
        "mimetype",
    )
    def _check_deca_provenance(self):
        for attachment in self.filtered("deca_source_id"):
            picking = (
                self.env["stock.picking"].browse(attachment.deca_source_id).exists()
            )
            if (
                not picking
                or attachment.res_model != "stock.picking"
                or attachment.res_id != picking.id
                or attachment.company_id != picking.company_id
                or attachment.deca_version <= 0
                or not attachment.deca_content_hash
                or attachment.public
                or attachment.access_token
                or attachment.type != "binary"
                or attachment.mimetype != "application/pdf"
            ):
                raise ValidationError(
                    self.env._("Invalid generated DeCA file provenance.")
                )

    def write(self, vals):
        if self.sudo().filtered("deca_source_id"):
            raise AccessError(self.env._("Issued DeCA files cannot be changed."))
        if self._deca_provenance_fields.intersection(vals):
            raise AccessError(
                self.env._("DeCA file provenance can only be set on generation.")
            )
        return super().write(vals)

    def unlink(self):
        sources = self.sudo().mapped("deca_source_id")
        if sources and self.env["stock.picking"].sudo().browse(sources).exists():
            raise AccessError(
                self.env._(
                    "Issued DeCA files cannot be deleted while their transfer exists."
                )
            )
        return super().unlink()
