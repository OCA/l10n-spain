# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import re

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .logista_master_data import (
    LOGISTA_AUTH_SCHEMES,
    LOGISTA_DELIVERY_NOTE_ACTIONS,
    LOGISTA_FREIGHT_TYPES,
    LOGISTA_LABEL_FORMATS,
    LOGISTA_NOTIFICATION_TYPES,
    LOGISTA_PROD_PLAZA_URL,
    LOGISTA_PROD_SHIPMENT_URL,
    LOGISTA_SECTORS,
    LOGISTA_SERVICES,
    LOGISTA_TEST_PLAZA_URL,
    LOGISTA_TEST_SHIPMENT_URL,
    LOGISTA_TRACKING_URL_TEMPLATE,
    build_logista_barcode_34,
)
from .logista_request import LogistaRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("logista", "Logista Parcel")],
        ondelete={"logista": "set default"},
    )

    # -------------------------------------------------------------------------
    # Connection & Shipper Identification
    # -------------------------------------------------------------------------
    logista_api_token = fields.Char(
        string="Logista API Token",
        copy=False,
        groups="base.group_system",
        help=(
            "Authorization token provided by Logista Parcel (valid for 3 months; "
            "renew before expiration)."
        ),
    )
    logista_auth_scheme = fields.Selection(
        selection=LOGISTA_AUTH_SCHEMES,
        string="Authorization Header Format",
        default="raw",
        required=True,
        help=(
            "Header format for `Authorization`: raw `<token>` (Section Autenticación) "
            "or `Bearer <token>`."
        ),
    )
    logista_test_url = fields.Char(
        string="Test Shipment Endpoint",
        default=LOGISTA_TEST_SHIPMENT_URL,
    )
    logista_prod_url = fields.Char(
        string="Production Shipment Endpoint",
        default=LOGISTA_PROD_SHIPMENT_URL,
    )
    logista_test_plaza_url = fields.Char(
        string="Test Plaza Routing Endpoint",
        default=LOGISTA_TEST_PLAZA_URL,
    )
    logista_prod_plaza_url = fields.Char(
        string="Production Plaza Routing Endpoint",
        default=LOGISTA_PROD_PLAZA_URL,
    )
    logista_sender_code = fields.Char(
        string="Sender Code (Sender.Code)",
        size=9,
        copy=False,
        help="9-character sender code provided by Logista Parcel.",
    )
    logista_send_sender_name = fields.Boolean(
        string="Include Sender Name in Payload",
        default=True,
    )

    # -------------------------------------------------------------------------
    # Service, Freight & Shipment Options
    # -------------------------------------------------------------------------
    logista_service_id = fields.Selection(
        selection=LOGISTA_SERVICES,
        string="Logista Parcel Service",
        default="1",
        required=True,
    )
    logista_sector_code = fields.Selection(
        selection=LOGISTA_SECTORS,
        string="Sector Code",
        default="0",
        required=True,
        help=(
            "Sector code assigned by Logista Parcel (Position 1 of the 34-digit "
            "barcode and `keyact` parameter in `wsRepartoProductoPorPlazas`)."
        ),
    )
    logista_freight_type = fields.Selection(
        selection=LOGISTA_FREIGHT_TYPES,
        string="Default Freight Type",
        default="P",
        required=True,
    )
    logista_use_order_incoterm = fields.Boolean(
        string="Map Freight Type from Incoterm",
        default=True,
        help=(
            "Automatically map Sale Order / Picking Incoterms (EXW/FCA -> D Collect; "
            "CPT/DAP/DDP -> P Prepaid)."
        ),
    )
    logista_delivery_note_action = fields.Selection(
        selection=LOGISTA_DELIVERY_NOTE_ACTIONS,
        string="Delivery Note Action",
        default="0",
    )
    logista_tight_flow = fields.Boolean(
        string="Tight Flow Service (Flujo Tenso)",
        default=False,
    )
    logista_notification_type = fields.Selection(
        selection=LOGISTA_NOTIFICATION_TYPES,
        string="Default Status Notification",
        default="none",
    )
    logista_cash_on_delivery = fields.Boolean(
        string="Cash on Delivery (Contra Reembolso)",
        default=False,
        help=(
            "Send the Sale Order total amount as `CashOnDelivery` unless overridden "
            "on the picking."
        ),
    )
    logista_send_volume = fields.Boolean(
        string="Send Volume (m³)",
        default=True,
        help=(
            "Include picking volume in cubic meters (`Volume`) when greater than zero."
        ),
    )
    logista_epacking_enabled = fields.Boolean(
        string="Enable ePackingList",
        default=False,
    )
    logista_epacking_mailing = fields.Boolean(
        string="ePackingList Email Delivery",
        default=False,
    )
    logista_epacking_printing = fields.Boolean(
        string="ePackingList Print Copy",
        default=False,
    )
    logista_allow_local_cancel = fields.Boolean(
        string="Allow Local Cancellation in Odoo",
        default=True,
        help=(
            "Logista Parcel API v5 does not expose a remote cancellation endpoint. "
            "When enabled, cancelling a shipment in Odoo unlinks the tracking "
            "reference and reminds the user to notify the origin delegation if needed."
        ),
    )

    # -------------------------------------------------------------------------
    # Label, Barcode & Packaging Configuration
    # -------------------------------------------------------------------------
    logista_label_format = fields.Selection(
        selection=LOGISTA_LABEL_FORMATS,
        string="Label Format",
        default="PDF",
        required=True,
    )
    logista_origin_delegation_code = fields.Char(
        string="Origin Delegation Code (2 Digits)",
        size=2,
        help=(
            "2-digit origin delegation code provided by Logista Parcel for "
            "positions 9-10 of the 34-digit Code 128 barcode."
        ),
    )
    logista_origin_delegation_name = fields.Char(
        string="Origin Delegation Label Header",
        help="Optional header text printed above the sender block on labels.",
    )
    logista_customer_barcode_code = fields.Char(
        string="Barcode Customer Code (6 Digits)",
        size=6,
        copy=False,
        help=(
            "6-digit customer code provided by Logista Parcel for positions 11-16 "
            "of the 34-digit barcode. If empty, the last 6 digits of Sender.Code "
            "are used."
        ),
    )
    logista_default_packaging_id = fields.Many2one(
        comodel_name="stock.package.type",
        string="Default Packaging Type",
        domain="[('package_carrier_type', '=', 'logista')]",
    )
    logista_tracking_url = fields.Char(
        string="Tracking URL",
        default=LOGISTA_TRACKING_URL_TEMPLATE,
    )

    # -------------------------------------------------------------------------
    # Capability Hooks & Internal Helpers
    # -------------------------------------------------------------------------
    @api.depends("delivery_type")
    def _compute_can_generate_return(self):
        res = super()._compute_can_generate_return()
        for carrier in self:
            if carrier.delivery_type == "logista":
                carrier.can_generate_return = True
        return res

    @api.depends("delivery_type")
    def _compute_supports_shipping_insurance(self):
        res = super()._compute_supports_shipping_insurance()
        for carrier in self:
            if carrier.delivery_type == "logista":
                carrier.supports_shipping_insurance = True
        return res

    def _logista_get_origin_delegation_code(self):
        self.ensure_one()
        if self.logista_origin_delegation_code:
            digits = re.sub(r"\D", "", self.logista_origin_delegation_code)
            if digits:
                return digits[-2:].zfill(2)
        sender_digits = re.sub(r"\D", "", self.logista_sender_code or "")
        if len(sender_digits) >= 8:
            return sender_digits[:2]
        return "00"

    def _logista_get_customer_barcode_code(self):
        self.ensure_one()
        if self.logista_customer_barcode_code:
            digits = re.sub(r"\D", "", self.logista_customer_barcode_code)
            if digits:
                return digits[-6:].zfill(6)
        sender_digits = re.sub(r"\D", "", self.logista_sender_code or "")
        if sender_digits:
            return sender_digits[-6:].zfill(6)
        return "000000"

    def _logista_render_label_bytes(self, picking, is_return=False):
        """Render shipping label in PDF (QWeb 100x150mm) or ZPL (Zebra thermal)."""
        self.ensure_one()
        if self.logista_label_format == "ZPL":
            items = picking._get_logista_label_items(is_return=is_return)
            zpl_bytes = LogistaRequest(self).render_zpl_labels(items)
            return zpl_bytes, "zpl", "text/plain"

        report = self.env.ref("delivery_logista.action_report_logista_label")
        pdf_bytes, _ext = report.with_context(
            logista_is_return=is_return
        )._render_qweb_pdf(report.report_name, res_ids=picking.ids)
        return pdf_bytes, "pdf", "application/pdf"

    def _logista_create_label_attachment(
        self,
        picking,
        raw_bytes,
        tracking_ref,
        ext="pdf",
        mimetype="application/pdf",
        is_return=False,
    ):
        self.ensure_one()
        if not raw_bytes:
            return False
        prefix = "logista_return" if is_return else "logista_label"
        safe_ref = str(tracking_ref or picking.name or "shipment").replace("/", "_")
        return (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": f"{prefix}_{safe_ref}.{ext}",
                    "datas": base64.b64encode(raw_bytes),
                    "type": "binary",
                    "res_model": picking._name,
                    "res_id": picking.id,
                    "mimetype": mimetype,
                }
            )
        )

    # -------------------------------------------------------------------------
    # UI Actions
    # -------------------------------------------------------------------------
    def action_test_logista_plaza_ws(self):
        """Test connectivity against Logista Parcel `wsRepartoProductoPorPlazas`."""
        self.ensure_one()
        partner = self.company_id.partner_id or self.env.company.partner_id
        country_iso = (partner.country_id.code or "ES").upper()
        zip_code = partner.zip or "28001"
        plaza = LogistaRequest(self).get_plaza_routing(
            country_code=country_iso,
            zip_code=zip_code,
            service_id=self.logista_service_id,
            sector_code=self.logista_sector_code,
        )
        if not plaza or not plaza.get("delegacion"):
            raise UserError(
                _(
                    "Could not resolve a Logista Parcel delegation for ZIP '%(zip)s' "
                    "(%(country)s). Check network connectivity and postal code."
                )
                % {"zip": zip_code, "country": country_iso}
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Logista Parcel Plaza Service OK"),
                "message": _(
                    "ZIP %(zip)s -> Delegation: %(del)s (Code %(code)s), Zone: %(zone)s"
                )
                % {
                    "zip": zip_code,
                    "del": plaza.get("delegacion"),
                    "code": plaza.get("delegacion_code") or "-",
                    "zone": plaza.get("zona_reparto") or "-",
                },
                "type": "success",
                "sticky": False,
            },
        }

    # -------------------------------------------------------------------------
    # Odoo / OCA Delivery Carrier Hooks
    # -------------------------------------------------------------------------
    def logista_rate_shipment(self, order):
        """Logista Parcel API v5 does not provide a rate quotation web service.
        Uses price rules (`price_rule_ids`) if configured on the carrier, or
        falls back to the carrier product's fixed/pricelist price.
        """
        self.ensure_one()
        partner = order.partner_shipping_id or order.partner_id
        if not self._match_address(partner):
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "Error: this delivery method is not available for this address."
                ),
                "warning_message": False,
            }
        if self.price_rule_ids:
            try:
                price_unit = self._get_price_available(order)
            except UserError as exc:
                return {
                    "success": False,
                    "price": 0.0,
                    "error_message": exc.args[0],
                    "warning_message": False,
                }
            price = self._compute_currency(order, price_unit, "company_to_pricelist")
        else:
            price = order.pricelist_id._get_product_price(self.product_id, 1.0)
        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }

    def logista_send_shipping(self, pickings):
        self.ensure_one()
        client = LogistaRequest(self)
        origin_deleg_code = self._logista_get_origin_delegation_code()
        cust_bc_code = self._logista_get_customer_barcode_code()
        results = []

        for picking in pickings:
            response = client.send_shipping(picking, is_return=False)
            shipment_id = response["shipment_id"]
            session_id = response["session_id"]
            main_ref = response["main_reference"]
            metrics = response["metrics"]

            partner = picking.partner_id
            shipper = client._get_shipper_partner(picking)
            dest_country_iso = (partner.country_id.code or "ES").upper()
            orig_country_iso = (shipper.country_id.code or "ES").upper()
            service_id = client._resolve_service_id(picking=picking)
            sector_code = self.logista_sector_code or "0"

            plaza = client.get_plaza_routing(
                dest_country_iso,
                partner.zip,
                service_id=service_id,
                sector_code=sector_code,
            )

            barcodes = [
                build_logista_barcode_34(
                    sector_code=sector_code,
                    service_id=service_id,
                    postal_code=partner.zip or "00000",
                    origin_delegation_code=origin_deleg_code,
                    customer_code=cust_bc_code,
                    reference=main_ref,
                    package_index=idx,
                    dest_country_code=dest_country_iso,
                    origin_country_code=orig_country_iso,
                )
                for idx in range(1, metrics["control_packages"] + 1)
            ]
            phys_packages = picking.move_line_ids.mapped("result_package_id")
            for idx, pkg in enumerate(phys_packages):
                if idx < len(barcodes):
                    pkg.logista_barcode = barcodes[idx]

            meta = (
                dict(picking.tracking_json)
                if isinstance(picking.tracking_json, dict)
                else {}
            )
            meta.update(
                {
                    "shipment_id": shipment_id,
                    "session_id": session_id,
                    "references": response["references"],
                    "main_reference": main_ref,
                    "barcodes": barcodes,
                    "delegacion": plaza.get("delegacion") or "",
                    "zona_reparto": plaza.get("zona_reparto") or "",
                    "delegacion_cb": plaza.get("delegacion_cb") or "",
                    "delegacion_code": plaza.get("delegacion_code") or "",
                    "packages": metrics["packages"],
                    "control_packages": metrics["control_packages"],
                    "mix_shipment": metrics["mix_shipment"],
                }
            )
            state_txt = (
                f"Session {session_id} - Shipment {shipment_id}"
                if session_id
                else f"Shipment {shipment_id}"
            )
            vals = {
                "delivery_state": "shipping_recorded_in_carrier",
                "date_shipped": fields.Date.context_today(self),
                "tracking_state": state_txt,
                "tracking_state_history": state_txt,
                "tracking_json": meta,
            }
            if not picking.number_of_packages:
                vals["number_of_packages"] = metrics["packages"]
            picking.write(vals)

            raw_bytes, ext, mimetype = self._logista_render_label_bytes(
                picking, is_return=False
            )
            attachment = self._logista_create_label_attachment(
                picking, raw_bytes, shipment_id, ext=ext, mimetype=mimetype
            )
            if attachment:
                msg = (
                    Markup("<p><b>%s</b></p><ul>")
                    % _("Logista Parcel label generated:")
                    + Markup(
                        "<li><b>%s:</b> <code>%s</code> (%s: <code>%s</code>)</li>"
                    )
                    % (_("ShipmentId"), shipment_id, _("SessionId"), session_id or "-")
                    + Markup("<li><b>%s:</b> <code>%s</code></li>")
                    % (_("Barcodes"), ", ".join(barcodes))
                    + Markup("</ul>")
                )
                picking.message_post(body=msg, attachment_ids=[attachment.id])

            if self.return_label_on_delivery:
                self.get_return_label(picking, tracking_number=shipment_id)

            exact_price = 0.0
            if picking.sale_id:
                rate_res = self.logista_rate_shipment(picking.sale_id)
                if rate_res.get("success"):
                    exact_price = rate_res.get("price", 0.0)

            results.append(
                {
                    "tracking_number": shipment_id,
                    "exact_price": exact_price,
                }
            )
        return results

    def logista_get_label(self, picking):
        self.ensure_one()
        raw_bytes, ext, mimetype = self._logista_render_label_bytes(
            picking, is_return=False
        )
        ref = picking.carrier_tracking_ref or picking.name
        attachment = self._logista_create_label_attachment(
            picking, raw_bytes, ref, ext=ext, mimetype=mimetype
        )
        if attachment:
            picking.message_post(
                body=_("Logista Parcel label reprinted."),
                attachment_ids=[attachment.id],
            )
        return attachment

    def logista_get_return_label(
        self, pickings, tracking_number=None, origin_date=None
    ):
        self.ensure_one()
        client = LogistaRequest(self)
        for picking in pickings:
            response = client.send_shipping(picking, is_return=True)
            ret_id = response["shipment_id"]
            raw_bytes, ext, mimetype = self._logista_render_label_bytes(
                picking, is_return=True
            )
            attachment = self._logista_create_label_attachment(
                picking,
                raw_bytes,
                ret_id,
                ext=ext,
                mimetype=mimetype,
                is_return=True,
            )
            if attachment:
                picking.message_post(
                    body=_(
                        "Logista Parcel return expedition registered (ShipmentId: %s)."
                    )
                    % ret_id,
                    attachment_ids=[attachment.id],
                )
        return True

    def logista_get_tracking_link(self, picking):
        self.ensure_one()
        template = (self.logista_tracking_url or LOGISTA_TRACKING_URL_TEMPLATE).strip()
        ref = (picking.carrier_tracking_ref or picking.name or "").split(",")[0].strip()
        zip_code = (picking.partner_id.zip or "").strip()
        if "{tracking_ref}" in template or "{zip}" in template:
            return template.format(tracking_ref=ref, zip=zip_code)
        return template

    def logista_cancel_shipment(self, pickings):
        self.ensure_one()
        if not self.logista_allow_local_cancel:
            raise UserError(
                _(
                    "Logista Parcel API v5 does not provide an automatic shipment "
                    "cancellation endpoint. Please contact your Logista Parcel "
                    "origin delegation or enable local cancellation on the carrier."
                )
            )
        for picking in pickings.filtered("carrier_tracking_ref"):
            old_ref = picking.carrier_tracking_ref
            meta = (
                dict(picking.tracking_json)
                if isinstance(picking.tracking_json, dict)
                else {}
            )
            meta["cancelled_locally"] = True
            picking.write(
                {
                    "carrier_tracking_ref": False,
                    "delivery_state": "canceled_shipment",
                    "tracking_state": _("Cancelled locally"),
                    "tracking_json": meta,
                }
            )
            picking.message_post(
                body=_(
                    "Logista Parcel shipment %s unlinked locally in Odoo. "
                    "Remember to notify your Logista Parcel origin delegation if "
                    "the expedition was already consolidated in I2MS."
                )
                % old_ref
            )
        return True
