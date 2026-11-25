# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import io

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfFileReader as PdfReader
    from PyPDF2 import PdfFileWriter as PdfWriter

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    tractor_license_plate = fields.Char(
        string="Main vehicle or tractor licence plate",
        size=8,
    )
    trailer_license_plate = fields.Char(
        string="Trailer or semi-trailer licence plate",
        size=8,
    )
    special_authorization = fields.Text(
        string="Special traffic authorisations",
    )
    deca_access_token = fields.Text(
        string="Security access token to share url",
        copy=False,
    )
    carrier_contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="Carrier contact",
        help="Carrier contact whose details are printed on the DeCA",
    )
    special_authorization_history = fields.Text(
        string="Special authorisation history",
        copy=False,
        readonly=True,
    )
    tractor_license_plate_history = fields.Text(
        string="Tractor licence plate history",
        copy=False,
        readonly=True,
    )
    trailer_license_plate_history = fields.Text(
        string="Trailer licence plate history",
        copy=False,
        readonly=True,
    )
    deca_version = fields.Integer(
        string="DeCA Version",
        default=0,
        copy=False,
        readonly=True,
    )
    deca_first_version_date = fields.Datetime(
        string="DeCA First Version Date",
        copy=False,
        readonly=True,
    )
    deca_content_hash = fields.Char(
        string="DeCA Content Hash",
        copy=False,
        readonly=True,
    )
    deca_is_visible = fields.Boolean(
        compute="_compute_deca_is_visible",
    )
    deca_weight = fields.Float(
        compute="_compute_deca_weight",
        digits="Stock Weight",
        store=True,
        help="Total weight of the products in the picking.",
        compute_sudo=True,
    )

    @api.depends("move_ids.deca_weight")
    def _compute_deca_weight(self):
        for picking in self:
            picking.deca_weight = sum(
                move.deca_weight for move in picking.move_ids if move.state != "cancel"
            )

    @api.depends("picking_type_id.code", "picking_type_id.l10n_es_deca_enabled")
    def _compute_deca_is_visible(self):
        for picking in self:
            picking.deca_is_visible = picking.picking_type_code == "outgoing" or (
                picking.picking_type_code == "incoming"
                and picking.picking_type_id.l10n_es_deca_enabled
            )

    def _check_deca_required_fields(self):
        for picking in self:
            missing = []
            if not picking.tractor_license_plate:
                missing.append(self.env._("Main vehicle or tractor licence plate"))
            if not picking.carrier_contact_id:
                missing.append(self.env._("Carrier contact"))
            else:
                if not picking.carrier_contact_id.vat:
                    missing.append(self.env._("Carrier NIF (VAT)"))
            sender = (
                picking.picking_type_id.warehouse_id.partner_id
                or picking.company_id.partner_id
            )
            consignee = picking.partner_id
            if picking.picking_type_code == "incoming":
                sender = picking.partner_id
                consignee = (
                    picking.picking_type_id.warehouse_id.partner_id
                    or picking.company_id.partner_id
                )
            if not consignee.vat:
                missing.append(self.env._("Consignee NIF (VAT)"))
            if not sender.vat:
                missing.append(self.env._("Sender NIF (VAT)"))
            if not picking.deca_weight:
                missing.append(self.env._("Weight"))
            if missing:
                raise UserError(
                    self.env._(
                        "The following data is missing for the DeCA report for "
                        "picking %(picking)s:\n%(missing)s",
                        picking=picking.name,
                        missing="\n".join([f"- {m}" for m in missing]),
                    )
                )

    def _get_deca_hash(self):
        self.ensure_one()
        data = (
            f"{self.name}{self.tractor_license_plate}{self.trailer_license_plate}"
            f"{self.special_authorization}"
            f"{self.carrier_contact_id.id}"
        )
        data += (
            f"{self.partner_id.id}{self.picking_type_id.warehouse_id.partner_id.id}"
            f"{self.company_id.id}"
        )
        loading_date = self.date_done or self.scheduled_date
        data += f"{loading_date.date() if loading_date else ''}"
        data += (
            f"{self.tractor_license_plate_history}{self.trailer_license_plate_history}"
            f"{self.special_authorization_history}"
        )
        for move in self.move_ids:
            data += f"{move.product_id.id}{move.quantity}"
            data += f"{move.product_uom.id}{move.deca_weight}"
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    def write(self, vals):
        tracked_fields = [
            ("tractor_license_plate", "tractor_license_plate_history"),
            ("trailer_license_plate", "trailer_license_plate_history"),
            ("special_authorization", "special_authorization_history"),
        ]
        history_updates = {}
        for rec in self:
            if rec.state == "done":
                for field_name, history_field in tracked_fields:
                    if field_name in vals:
                        old_val = rec[field_name]
                        new_val = vals[field_name]
                        if old_val and old_val != new_val:
                            current_history = rec[history_field] or ""
                            history_updates.setdefault(rec.id, {})[history_field] = (
                                f"{current_history}{old_val}\n"
                            )
        res = super().write(vals)
        for rec in self:
            if rec.id in history_updates:
                super(StockPicking, rec).write(history_updates[rec.id])
        return res

    def _get_share_url(self):
        self.ensure_one()
        self.check_access("read")
        if not self.deca_access_token:
            self.sudo().deca_access_token = self.env[
                "ir.attachment"
            ]._generate_access_token()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/my/picking/{self.id}?access_token={self.deca_access_token}"

    def _render_deca_pdf(self):
        self.ensure_one()
        self._check_deca_required_fields()
        current_hash = self._get_deca_hash()
        if self.deca_version > 0 and self.deca_content_hash == current_hash:
            attachment_name = f"DeCA - {self.name} - v{self.deca_version}.pdf"
            attachment = (
                self.env["ir.attachment"]
                .sudo()
                .search(
                    [
                        ("res_model", "=", "stock.picking"),
                        ("res_id", "=", self.id),
                        ("name", "=", attachment_name),
                    ],
                    limit=1,
                )
            )
            if attachment:
                return attachment, attachment.raw, "pdf"
        content, ext = self.env["ir.actions.report"]._render_qweb_pdf(
            "l10n_es_deca_oca.report_deca", [self.id]
        )
        if ext != "pdf" or content.startswith(b"<!DOC"):
            return self.env["ir.attachment"], content, ext
        if not self.deca_first_version_date:
            self.sudo().deca_first_version_date = fields.Datetime.now()
        self.sudo().write(
            {
                "deca_version": self.deca_version + 1,
                "deca_content_hash": current_hash,
            }
        )
        reader = PdfReader(io.BytesIO(content))
        writer = PdfWriter()
        if hasattr(reader, "pages"):
            for page in reader.pages:
                if hasattr(writer, "add_page"):
                    writer.add_page(page)
                else:
                    writer.addPage(page)
        else:
            for i in range(reader.getNumPages()):
                writer.addPage(reader.getPage(i))
        try:
            metadata = reader.metadata or {}
        except AttributeError:
            metadata = reader.getDocumentInfo() or {}
        custom_metadata = dict(metadata)
        creation_date = self.deca_first_version_date.strftime("D:%Y%m%d%H%M%SZ")
        mod_date = fields.Datetime.now().strftime("D:%Y%m%d%H%M%SZ")
        custom_metadata.update(
            {
                "/CreationDate": creation_date,
                "/ModDate": mod_date,
            }
        )
        try:
            writer.add_metadata(custom_metadata)
        except AttributeError:
            writer.addMetadata(custom_metadata)
        output = io.BytesIO()
        writer.write(output)
        final_content = output.getvalue()
        attachment_name = f"DeCA - {self.name} - v{self.deca_version}.pdf"
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": attachment_name,
                    "type": "binary",
                    "raw": final_content,
                    "res_model": "stock.picking",
                    "res_id": self.id,
                    "mimetype": "application/pdf",
                }
            )
        )
        return attachment, final_content, ext

    def action_print_deca(self):
        self.ensure_one()
        attachment, _content, _ext = self._render_deca_pdf()
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }
