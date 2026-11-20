# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_is_zero, format_datetime


class StockPicking(models.Model):
    _inherit = "stock.picking"

    _deca_owned_fields = frozenset(
        {
            "deca_access_token",
            "deca_version",
            "deca_first_version_date",
            "deca_content_hash",
            "deca_attachment_id",
            "tractor_license_plate_history",
            "trailer_license_plate_history",
            "special_authorization_history",
        }
    )

    tractor_license_plate = fields.Char(
        string="Main vehicle or tractor licence plate",
        size=8,
        help=(
            "Current licence plate printed on the DeCA. Changes after completion "
            "retain the previous value in the printed history."
        ),
    )
    trailer_license_plate = fields.Char(
        string="Trailer or semi-trailer licence plate",
        size=8,
        help=(
            "Current licence plate printed on the DeCA. Changes after completion "
            "retain the previous value in the printed history."
        ),
    )
    special_authorization = fields.Text(
        string="Special traffic authorisations",
        help=(
            "Traffic authorisations printed on the DeCA. Changes after completion "
            "retain previous values in the printed history."
        ),
    )
    deca_access_token = fields.Text(
        string="Security access token to share url",
        copy=False,
        readonly=True,
        groups="stock.group_stock_user",
        help=(
            "Bearer credential for the current DeCA PDF. Anyone with its URL can "
            "download the document."
        ),
    )
    carrier_contact_id = fields.Many2one(
        comodel_name="res.partner",
        string="Carrier contact",
        help=(
            "Carrier contact whose name, VAT and address are printed on the DeCA. "
            "Use a shared contact or one belonging to the transfer company."
        ),
        check_company=True,
    )
    special_authorization_history = fields.Text(
        string="Special authorisation history",
        help=(
            "Previous nonempty authorisations changed after completion, printed "
            "struck through on subsequent versions."
        ),
        copy=False,
        readonly=True,
    )
    tractor_license_plate_history = fields.Text(
        string="Tractor licence plate history",
        help=(
            "Previous nonempty tractor plates changed after completion, printed "
            "struck through on subsequent versions."
        ),
        copy=False,
        readonly=True,
    )
    trailer_license_plate_history = fields.Text(
        string="Trailer licence plate history",
        help=(
            "Previous nonempty trailer plates changed after completion, printed "
            "struck through on subsequent versions."
        ),
        copy=False,
        readonly=True,
    )
    deca_attachment_id = fields.Many2one(
        "ir.attachment",
        copy=False,
        readonly=True,
        ondelete="set null",
        string="Current DeCA file",
        help=(
            "Latest generated version. Earlier versions remain attached to the "
            "transfer."
        ),
    )
    deca_version = fields.Integer(
        string="DeCA Version",
        help=(
            "Increases when a printed value changes and a new PDF is generated; "
            "unchanged valid documents reuse the current file."
        ),
        default=0,
        copy=False,
        readonly=True,
    )
    deca_first_version_date = fields.Datetime(
        string="DeCA First Version Date",
        help=(
            "First PDF generation timestamp used in file metadata, not the printed "
            "issue date."
        ),
        copy=False,
        readonly=True,
    )
    deca_content_hash = fields.Char(
        string="DeCA Content Hash",
        copy=False,
        readonly=True,
    )
    l10n_es_show_deca = fields.Boolean(
        compute="_compute_l10n_es_show_deca",
    )
    deca_weight = fields.Float(
        compute="_compute_deca_weight",
        digits=False,
        min_display_digits="Stock Weight",
        store=True,
        help=(
            "Total cargo weight in kg, excluding cancelled moves. Uses actual "
            "quantity when nonzero, otherwise planned quantity. Product weights "
            "are converted from the effective weight unit to kg. Up to six decimal "
            "places are shown; positive weights too small to display block issuance."
        ),
        compute_sudo=True,
    )

    @api.depends("move_ids.deca_weight", "move_ids.state")
    def _compute_deca_weight(self):
        for picking in self:
            picking.deca_weight = sum(
                move.deca_weight for move in picking.move_ids if move.state != "cancel"
            )

    @api.depends("picking_type_id.code", "picking_type_id.l10n_es_deca_enabled")
    def _compute_l10n_es_show_deca(self):
        for picking in self:
            picking.l10n_es_show_deca = picking.picking_type_code == "outgoing" or (
                picking.picking_type_code == "incoming"
                and picking.picking_type_id.l10n_es_deca_enabled
            )

    @api.constrains("carrier_contact_id", "company_id")
    def _check_deca_carrier_company(self):
        self._check_company(["carrier_contact_id"])

    def _check_deca_required_fields(self):
        self._check_deca_carrier_company()
        kg = self.env.ref("uom.product_uom_kgm")
        if any(
            move.product_id.uom_id.category_id != kg.category_id
            for move in self.move_ids
        ):
            self.env["stock.move"]._get_deca_weight_uom(required=True)
        for picking in self:
            if any(
                weight > 0 and float_is_zero(weight, precision_digits=6)
                for weight in [
                    picking.deca_weight,
                    *picking.move_ids.mapped("deca_weight"),
                ]
            ):
                raise UserError(
                    self.env._(
                        "A positive DeCA weight is too small to display in kg with six "
                        "decimal places. Review the cargo before generating "
                        "the document."
                    )
                )
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

    def _get_deca_report_data(self):
        """Normalize the mutable business values used by both QWeb and its cache."""
        self.ensure_one()
        picking = self.with_company(self.company_id).with_context(
            lang=self.partner_id.lang or self.company_id.partner_id.lang or "en_US",
            tz=self.company_id.partner_id.tz or "UTC",
            display_default_code=True,
        )

        def partner_values(partner):
            return {
                name: partner[name] or ""
                for name in ("name", "vat", "street", "zip", "city")
            } | {
                "state": partner.state_id.name or "",
                "country": partner.country_id.name or "",
            }

        warehouse_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        sender, consignee = warehouse_partner, picking.partner_id
        if picking.picking_type_code == "incoming":
            sender, consignee = consignee, sender
        company = picking.company_id
        values = {
            "name": picking.name,
            "direction": picking.picking_type_code,
            "sender": partner_values(sender),
            "consignee": partner_values(consignee),
            "carrier": partner_values(picking.carrier_contact_id),
            "issue_city": company.city or "",
            "issue_date": format_datetime(
                picking.env,
                picking.create_date,
                tz=picking.env.context.get("tz"),
                dt_format="dd/MM/yyyy",
            ),
            "loading_date": format_datetime(
                picking.env,
                picking.date_done or picking.scheduled_date,
                tz=picking.env.context.get("tz"),
                dt_format="dd/MM/yyyy",
            ),
            "goods": [
                {
                    "product": move.product_id.display_name,
                    "quantity": picking.env["ir.qweb.field.float"].record_to_html(
                        move, "quantity", {}
                    ),
                    "unit": move.product_uom.name,
                    "weight": picking.env["ir.qweb.field.float"].record_to_html(
                        move, "deca_weight", {}
                    ),
                }
                for move in picking.move_ids
            ],
            "share_url": picking._get_share_url(),
            "lang": picking.env.lang,
            "company": {
                "id": company.id,
                "partner": partner_values(company.partner_id),
                **{
                    name: company[name] or ""
                    for name in (
                        "name",
                        "report_header",
                        "report_footer",
                        "company_details",
                        "email",
                        "phone",
                        "website",
                        "primary_color",
                        "secondary_color",
                        "font",
                        "layout_background",
                    )
                },
                "logo": hashlib.sha256(company.logo or b"").hexdigest(),
                "background": hashlib.sha256(
                    company.layout_background_image or b""
                ).hexdigest(),
                "layout": company.external_report_layout_id.id,
            },
        }
        for name in (
            "tractor_license_plate",
            "trailer_license_plate",
            "special_authorization",
        ):
            values[name] = picking[name] or ""
            values[name + "_history"] = (picking[name + "_history"] or "").splitlines()
        return values

    def _get_deca_hash(self):
        self.ensure_one()
        content = json.dumps(
            self._get_deca_report_data(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su and (
            any(self._deca_owned_fields.intersection(vals) for vals in vals_list)
            or any(
                "default_" + name in self.env.context
                for name in self._deca_owned_fields
            )
        ):
            raise AccessError(
                self.env._("DeCA generation data cannot be set manually.")
            )
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and self._deca_owned_fields.intersection(vals):
            raise AccessError(
                self.env._("DeCA generation data cannot be changed manually.")
            )
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

    def _check_deca_access(self):
        self.check_access("read")
        if not self.env.su and not self.env.user.has_group("stock.group_stock_user"):
            raise AccessError(
                self.env._("Only inventory users can generate or share a DeCA.")
            )
        if (
            not self
            or len(self.exists()) != len(self)
            or any(not p.l10n_es_show_deca for p in self)
        ):
            raise UserError(
                self.env._(
                    "DeCA is only available for outgoing or enabled incoming transfers."
                )
            )

    def _get_share_url(self):
        self.ensure_one()
        self._check_deca_access()
        if not self.deca_access_token:
            self.sudo().deca_access_token = self.env[
                "ir.attachment"
            ]._generate_access_token()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/my/picking/{self.id}?access_token={self.deca_access_token}"

    def action_get_share_url(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self._get_share_url(),
            "target": "new",
        }
