# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging

import requests

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

from .logista_master_data import (
    LOGISTA_INCOTERM_TO_FREIGHT,
    LOGISTA_PROD_PLAZA_URL,
    LOGISTA_PROD_SHIPMENT_URL,
    LOGISTA_TEST_PLAZA_URL,
    LOGISTA_TEST_SHIPMENT_URL,
    format_logista_code128_subsets,
    format_logista_main_reference,
    format_logista_postal_code_api,
    format_logista_postal_code_plaza,
    get_logista_country_id,
    sanitize_logista_email,
    sanitize_logista_nif,
    sanitize_logista_phone,
)

_logger = logging.getLogger(__name__)


class LogistaRequest:
    """REST API v5 client and payload builder for Logista Parcel
    (`POST /EnlaceB2B/app/integrations/shipment/v1` and
    `GET /Visor/rest/unauthenticated/wsRepartoProductoPorPlazas`).
    """

    def __init__(self, carrier):
        self.carrier_id = carrier
        self.env = carrier.env
        self.timeout = 45
        if carrier.prod_environment:
            self.shipment_url = (
                carrier.logista_prod_url or LOGISTA_PROD_SHIPMENT_URL
            ).strip()
            self.plaza_url = (
                carrier.logista_prod_plaza_url or LOGISTA_PROD_PLAZA_URL
            ).strip()
        else:
            self.shipment_url = (
                carrier.logista_test_url or LOGISTA_TEST_SHIPMENT_URL
            ).strip()
            self.plaza_url = (
                carrier.logista_test_plaza_url or LOGISTA_TEST_PLAZA_URL
            ).strip()

    # -------------------------------------------------------------------------
    # HTTP & Authentication Helpers
    # -------------------------------------------------------------------------
    def _get_auth_header_value(self):
        token = (self.carrier_id.sudo().logista_api_token or "").strip()
        if not token:
            raise UserError(
                _("Missing Logista Parcel API Token on delivery method '%s'.")
                % self.carrier_id.name
            )
        if (
            self.carrier_id.logista_auth_scheme == "bearer"
            and not token.lower().startswith("bearer ")
        ):
            return f"Bearer {token}"
        return token

    def _get_headers(self, authenticated=True):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
        }
        if authenticated:
            headers["Authorization"] = self._get_auth_header_value()
        return headers

    @staticmethod
    def _mask_headers(headers):
        masked = dict(headers)
        auth = masked.get("Authorization")
        if auth:
            if len(auth) > 10:
                masked["Authorization"] = f"{auth[:5]}***{auth[-3:]}"
            else:
                masked["Authorization"] = "***"
        return masked

    @staticmethod
    def _format_error_entry(entry):
        if not isinstance(entry, dict):
            return str(entry)
        code = entry.get("Code")
        msg = entry.get("Message") or entry.get("message") or entry.get("error") or ""
        refs = entry.get("References") or []
        corr = entry.get("CorrelationId") or ""
        parts = []
        if code is not None:
            parts.append(f"[Code {code}]")
        if msg:
            parts.append(str(msg))
        extras = []
        if refs:
            extras.append(f"Refs: {', '.join(str(r) for r in refs)}")
        if corr:
            extras.append(f"CorrelationId: {corr}")
        if extras:
            parts.append(f"({'; '.join(extras)})")
        return " ".join(parts).strip()

    def _format_error_message(self, response):
        status = response.status_code
        try:
            data = response.json()
        except ValueError:
            data = None

        if isinstance(data, list) and data:
            lines = [self._format_error_entry(item) for item in data]
            return f"[HTTP {status}]\n- " + "\n- ".join(lines)
        if isinstance(data, dict):
            formatted = self._format_error_entry(data)
            if formatted:
                return f"[HTTP {status}] {formatted}"

        text = (response.text or "").strip()
        return f"[HTTP {status}] {text[:500] or getattr(response, 'reason', '')}"

    def _request(
        self,
        method,
        url,
        params=None,
        json_payload=None,
        authenticated=True,
        log_name="logista",
        raise_on_error=True,
    ):
        headers = self._get_headers(authenticated=authenticated)
        req_dump = {
            "method": method.upper(),
            "url": url,
            "params": params or {},
            "headers": self._mask_headers(headers),
            "body": json_payload,
        }
        self.carrier_id.log_xml(
            json.dumps(req_dump, indent=2, ensure_ascii=False),
            f"{log_name}_request",
        )

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as tmo:
            err_msg = (
                _("Timeout: Logista Parcel server did not reply within %ss.")
                % self.timeout
            )
            self.carrier_id.log_xml(str(tmo), f"{log_name}_error")
            if raise_on_error:
                raise UserError(err_msg) from tmo
            return {"_error": True, "status_code": 0, "error_message": err_msg}
        except requests.exceptions.RequestException as exc:
            err_msg = _(
                "Connection error with Logista Parcel API (%(url)s): %(error)s"
            ) % {"url": url, "error": exc}
            self.carrier_id.log_xml(str(exc), f"{log_name}_error")
            if raise_on_error:
                raise UserError(err_msg) from exc
            return {"_error": True, "status_code": 0, "error_message": err_msg}

        resp_text = response.text or ""
        try:
            parsed = (
                response.json()
                if (resp_text or getattr(response, "content", None))
                else {}
            )
        except ValueError:
            parsed = None

        self.carrier_id.log_xml(
            f"Status: {response.status_code}\n{resp_text}",
            f"{log_name}_response",
        )

        if response.status_code in (200, 201, 202):
            if parsed is not None:
                return parsed
            return {"raw": resp_text}

        error_message = self._format_error_message(response)
        if raise_on_error:
            raise UserError(_("Logista Parcel API Error:\n%s") % error_message)
        return {
            "_error": True,
            "status_code": response.status_code,
            "error_message": error_message,
            "data": parsed,
        }

    # -------------------------------------------------------------------------
    # UoM, Partner & Package Metric Helpers
    # -------------------------------------------------------------------------
    def _convert_weight_to_kg(self, weight):
        if not weight:
            return 0.0
        weight_uom = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        kg_uom = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False)
        if weight_uom and kg_uom and weight_uom != kg_uom:
            return weight_uom._compute_quantity(weight, kg_uom, round=False)
        return float(weight)

    def _convert_volume_to_m3(self, volume):
        if not volume:
            return 0.0
        vol_uom = self.env[
            "product.template"
        ]._get_volume_uom_id_from_ir_config_parameter()
        m3_uom = self.env.ref("uom.product_uom_cubic_meter", raise_if_not_found=False)
        if vol_uom and m3_uom and vol_uom != m3_uom:
            return vol_uom._compute_quantity(volume, m3_uom, round=False)
        return float(volume)

    @staticmethod
    def _clean_text(value, max_len=40):
        cleaned = " ".join(str(value or "").strip().split())
        return cleaned[:max_len] if max_len else cleaned

    def _get_shipper_partner(self, picking):
        return (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
            or self.env.company.partner_id
        )

    def _validate_partner(self, partner, picking=None):
        if not partner:
            raise UserError(
                _("Picking %s does not have a delivery address assigned.")
                % (picking.name if picking else "")
            )
        street = " ".join(filter(None, [partner.street, partner.street2])).strip()
        city = (partner.city or partner.state_id.name or "").strip()
        if not street or not city or not partner.zip or not partner.country_id:
            raise UserError(
                _(
                    "Consignee '%s' must have Street, City, Postal Code, and Country "
                    "configured for Logista Parcel."
                )
                % partner.display_name
            )
        country_id = get_logista_country_id(partner.country_id.code)
        if not country_id:
            raise UserError(
                _(
                    "Country '%(country)s' on '%(partner)s' is not supported by "
                    "Logista Parcel API v5 (supported: Spain ES, Portugal PT, "
                    "Andorra AD)."
                )
                % {
                    "country": partner.country_id.display_name,
                    "partner": partner.display_name,
                }
            )
        return partner

    def _resolve_freight_type(self, partner=None, picking=None):
        if picking and picking.logista_freight_type in ("P", "D"):
            return picking.logista_freight_type
        if self.carrier_id.logista_use_order_incoterm:
            incoterm = False
            if picking and getattr(picking, "incoterm", False):
                incoterm = picking.incoterm
            elif (
                picking
                and picking.sale_id
                and getattr(picking.sale_id, "incoterm", False)
            ):
                incoterm = picking.sale_id.incoterm
            if incoterm and incoterm.code in LOGISTA_INCOTERM_TO_FREIGHT:
                return LOGISTA_INCOTERM_TO_FREIGHT[incoterm.code]
        if partner and partner.logista_freight_type in ("P", "D"):
            return partner.logista_freight_type
        return self.carrier_id.logista_freight_type or "P"

    def _resolve_service_id(self, picking=None):
        if picking and picking.logista_service_id:
            return picking.logista_service_id
        return self.carrier_id.logista_service_id or "1"

    def _resolve_insured_value(self, picking):
        if picking.logista_insured_value > 0.0:
            return round(min(99999.99, picking.logista_insured_value), 2)
        if (
            self.carrier_id.shipping_insurance
            and self.carrier_id.shipping_insurance > 0
            and picking.sale_id
            and picking.sale_id.amount_untaxed > 0.0
        ):
            val = picking.sale_id.amount_untaxed * (
                self.carrier_id.shipping_insurance / 100.0
            )
            return round(min(99999.99, val), 2)
        return 0.0

    def _resolve_cod_amount(self, picking):
        if picking.logista_cod_amount > 0.0:
            return round(min(99999.99, picking.logista_cod_amount), 2)
        if (
            self.carrier_id.logista_cash_on_delivery
            and picking.sale_id
            and picking.sale_id.amount_total > 0.0
        ):
            return round(min(99999.99, picking.sale_id.amount_total), 2)
        return 0.0

    def _prepare_package_metrics(self, picking):
        """Compute package, pallet, mixed-shipment, weight, and volume metrics for
        Logista Parcel API v5 (`Packages`, `ControlPackages`, `MixShipment`,
        `MixPackages`, `MixPalets`, `Weight`, `Volume`) and label unit types.
        """
        phys_packages = picking.move_line_ids.mapped("result_package_id")
        default_pkg_type = self.carrier_id.logista_default_packaging_id
        default_kind = (
            default_pkg_type.logista_package_kind
            if default_pkg_type and default_pkg_type.logista_package_kind
            else "parcel"
        )

        # Weight calculation (kg)
        raw_weight = picking.shipping_weight or picking.weight or 0.0
        total_weight_kg = self._convert_weight_to_kg(raw_weight)
        if total_weight_kg <= 0.0 and phys_packages:
            for pkg in phys_packages:
                pw = getattr(pkg, "shipping_weight", 0.0) or getattr(pkg, "weight", 0.0)
                total_weight_kg += self._convert_weight_to_kg(pw)
        if total_weight_kg <= 0.0:
            for move in picking.move_ids.filtered(lambda m: m.state != "cancel"):
                qty = move.quantity or move.product_uom_qty or 0.0
                total_weight_kg += self._convert_weight_to_kg(
                    (move.product_id.weight or 0.0) * qty
                )
        total_weight_kg = round(min(99999.99, max(0.1, total_weight_kg)), 2)

        # Volume calculation (m³ from stock_picking_volume)
        raw_vol = getattr(picking, "volume", 0.0) or 0.0
        total_vol_m3 = round(min(99.999, self._convert_volume_to_m3(raw_vol)), 3)

        # Count pallets vs loose parcels
        unit_kinds = []
        if phys_packages:
            pallet_count = 0
            parcel_count = 0
            for pkg in phys_packages:
                p_type = pkg.package_type_id or default_pkg_type
                kind = (
                    p_type.logista_package_kind
                    if p_type and p_type.logista_package_kind
                    else default_kind
                )
                unit_kinds.append(kind)
                if kind == "pallet":
                    pallet_count += 1
                else:
                    parcel_count += 1
            defined_bultos = picking.number_of_packages or len(phys_packages)
        else:
            pallet_count = max(0, picking.logista_pallets_qty or 0)
            parcel_count = max(0, picking.logista_loose_packages_qty or 0)
            defined_bultos = max(1, picking.number_of_packages or 1)
            if pallet_count == 0 and parcel_count == 0 and default_kind == "pallet":
                pallet_count = defined_bultos

        if pallet_count > 0 and parcel_count > 0:
            mix_shipment = 1
            mix_palets = min(9999, pallet_count)
            mix_packages = min(9999, parcel_count)
            control_packages = min(9999, mix_palets + mix_packages)
            packages = min(9999, max(defined_bultos, control_packages))
            if not unit_kinds:
                unit_kinds = ["pallet"] * mix_palets + ["parcel"] * mix_packages
        elif pallet_count > 0:
            mix_shipment = 0
            mix_palets = 0
            mix_packages = 0
            control_packages = min(9999, pallet_count)
            packages = min(9999, max(defined_bultos, control_packages))
            if not unit_kinds:
                unit_kinds = ["pallet"] * control_packages
        else:
            mix_shipment = 0
            mix_palets = 0
            mix_packages = 0
            packages = min(9999, max(1, parcel_count or defined_bultos))
            control_packages = packages
            if not unit_kinds:
                unit_kinds = ["parcel"] * control_packages

        return {
            "packages": packages,
            "control_packages": control_packages,
            "mix_shipment": mix_shipment,
            "mix_packages": mix_packages,
            "mix_palets": mix_palets,
            "weight_kg": total_weight_kg,
            "volume_m3": total_vol_m3,
            "unit_kinds": unit_kinds,
        }

    def _prepare_consignee_data(self, partner):
        """Build `Consignee` object adhering strictly to API v5 field lengths."""
        commercial = partner.commercial_partner_id or partner
        name = self._clean_text(commercial.name or partner.name or "Customer", 40)

        street1 = self._clean_text(partner.street or "", 120)
        street2 = self._clean_text(partner.street2 or "", 80)
        if street1 and len(street1) <= 40:
            address = street1
            dept_parts = [street2] if street2 else []
        else:
            address = street1[:40]
            overflow = street1[40:].strip()
            dept_parts = [p for p in (overflow, street2) if p]

        if partner != commercial and partner.name and partner.name != commercial.name:
            dept_parts.append(partner.name.strip())
        department = self._clean_text(" - ".join(dept_parts), 40)

        country_iso = (partner.country_id.code or "ES").upper()
        country_id = get_logista_country_id(country_iso)
        postal_code = format_logista_postal_code_api(partner.zip, country_iso)
        city = self._clean_text(partner.city or partner.state_id.name or "", 40)

        consignee = {
            "Name": name,
            "Address": address,
            "City": city,
            "CountryId": country_id,
            "PostalCode": postal_code,
        }
        cust_code = (
            partner.logista_customer_code
            or commercial.logista_customer_code
            or partner.ref
            or commercial.ref
            or ""
        )
        if cust_code:
            consignee["CustomerCode"] = self._clean_text(cust_code, 15)
        if department:
            consignee["Department"] = department

        nif = sanitize_logista_nif(commercial.vat or partner.vat)
        if nif:
            consignee["NIF"] = nif

        phone = sanitize_logista_phone(partner.phone or partner.mobile)
        if phone:
            consignee["Phone"] = phone

        mail = sanitize_logista_email(partner.email)
        if mail:
            consignee["Mail"] = mail

        return consignee

    def _prepare_notifications_data(self, partner):
        notif_type = (
            partner.logista_notification_type
            if partner.logista_notification_type
            and partner.logista_notification_type != "none"
            else self.carrier_id.logista_notification_type
        )
        if not notif_type or notif_type == "none":
            return None

        sms_phone = sanitize_logista_phone(partner.mobile or partner.phone)
        mail = sanitize_logista_email(partner.email)
        if not sms_phone and not mail:
            return None

        notif = {
            "Type": int(notif_type),
            "Name": self._clean_text(
                partner.name or partner.commercial_partner_id.name or "Contact", 40
            ),
        }
        if sms_phone:
            notif["Phone"] = sms_phone
        if mail:
            notif["Mail"] = mail
        return notif

    def _prepare_references(self, picking, is_return=False):
        if picking.logista_customer_reference and not is_return:
            main_ref = format_logista_main_reference(picking.logista_customer_reference)
        elif is_return:
            doc_num = format_logista_main_reference(picking.name or "0")
            main_ref = f"R{doc_num[:8]}"
        else:
            main_ref = format_logista_main_reference(picking.name or "0")

        refs = [{"CustomerReference": main_ref, "IsMain": True}]

        sec_raw = ""
        if picking.sale_id and picking.sale_id.client_order_ref:
            sec_raw = picking.sale_id.client_order_ref
        elif picking.origin and picking.origin != picking.name:
            sec_raw = picking.origin
        sec_clean = self._clean_text(sec_raw, 15)
        if sec_clean and sec_clean != main_ref:
            refs.append({"CustomerReference": sec_clean, "IsMain": False})
        return main_ref, refs

    def _apply_optional_shipment_fields(
        self, shipment, picking, dest_partner, metrics, is_return=False
    ):
        """Populate optional package, value, service, and ePackingList fields."""
        carrier = self.carrier_id
        if (
            metrics["control_packages"] != metrics["packages"]
            or metrics["mix_shipment"] == 1
        ):
            shipment["ControlPackages"] = metrics["control_packages"]
        if metrics["mix_shipment"] == 1:
            shipment["MixShipment"] = 1
            shipment["MixPackages"] = metrics["mix_packages"]
            shipment["MixPalets"] = metrics["mix_palets"]

        if carrier.logista_send_volume and metrics["volume_m3"] > 0.0:
            shipment["Volume"] = metrics["volume_m3"]

        if not is_return:
            self._apply_commercial_values(shipment, picking)

        comments = self._resolve_comments(picking, is_return=is_return)
        if comments:
            shipment["Comments"] = comments

        dna = (
            picking.logista_delivery_note_action
            or carrier.logista_delivery_note_action
            or "0"
        )
        if dna in ("1", "2"):
            shipment["DeliveryNoteAction"] = int(dna)
        if picking.logista_tight_flow or carrier.logista_tight_flow:
            shipment["TightFlowService"] = 1

        notif = self._prepare_notifications_data(dest_partner)
        if notif:
            shipment["Notifications"] = notif
        if carrier.logista_epacking_enabled and not is_return:
            shipment["ePackingList"] = self._prepare_epacking_data(dest_partner)

    def _apply_commercial_values(self, shipment, picking):
        insured = self._resolve_insured_value(picking)
        if insured > 0.0:
            shipment["InsuranceValue"] = insured
        cod = self._resolve_cod_amount(picking)
        if cod > 0.0:
            shipment["CashOnDelivery"] = cod
        if picking.logista_arranged_delivery_date:
            shipment["ArrangedDeliveryDate"] = fields.Date.to_string(
                picking.logista_arranged_delivery_date
            )

    def _resolve_comments(self, picking, is_return=False):
        raw_comments = picking.logista_comments or ""
        if not raw_comments and picking.note:
            raw_comments = html2plaintext(picking.note)
        if is_return and not raw_comments:
            raw_comments = _("Return %s") % (picking.name or "")
        return self._clean_text(raw_comments, 100)

    def _prepare_epacking_data(self, dest_partner):
        carrier = self.carrier_id
        epacking = {
            "IsServiceEnabled": True,
            "IsMailingEnabled": bool(carrier.logista_epacking_mailing),
            "IsPrintingEnabled": bool(carrier.logista_epacking_printing),
        }
        mail_to = sanitize_logista_email(dest_partner.email)
        if carrier.logista_epacking_mailing and mail_to:
            epacking["MailTo"] = mail_to
        return epacking

    def _prepare_shipment_payload(self, picking, is_return=False):
        """Build JSON body `[ { "Shipment": { ... } } ]` for `POST /shipment/v1`."""
        carrier = self.carrier_id
        sender_code = (carrier.logista_sender_code or "").strip()
        if not sender_code:
            raise UserError(
                _(
                    "Missing Sender Code (`Sender.Code`) on Logista Parcel "
                    "delivery method '%s'."
                )
                % carrier.name
            )

        shipper_partner = self._get_shipper_partner(picking)
        target = shipper_partner if is_return else picking.partner_id
        dest_partner = self._validate_partner(target, picking=picking)

        pickup_dt = picking.scheduled_date or fields.Datetime.now()
        service_id = self._resolve_service_id(picking=picking)
        metrics = self._prepare_package_metrics(picking)
        main_ref, refs = self._prepare_references(picking, is_return=is_return)

        sender_block = {"Code": sender_code[:9]}
        sender_origin = picking.partner_id if is_return else shipper_partner
        if carrier.logista_send_sender_name and sender_origin and sender_origin.name:
            sender_block["Name"] = self._clean_text(sender_origin.name, 40)

        shipment = {
            "PickupTime": pickup_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ServiceId": int(service_id),
            "Sender": sender_block,
            "Consignee": self._prepare_consignee_data(dest_partner),
            "Packages": metrics["packages"],
            "Weight": metrics["weight_kg"],
            "FreightType": self._resolve_freight_type(
                partner=dest_partner, picking=picking
            ),
            "CustomerReferences": refs,
        }
        self._apply_optional_shipment_fields(
            shipment, picking, dest_partner, metrics, is_return=is_return
        )
        return [{"Shipment": shipment}], main_ref, metrics

    # -------------------------------------------------------------------------
    # High-Level Web Service Operations
    # -------------------------------------------------------------------------
    def send_shipping(self, picking, is_return=False):
        """Submit shipment to `POST /EnlaceB2B/app/integrations/shipment/v1`."""
        payload, main_ref, metrics = self._prepare_shipment_payload(
            picking, is_return=is_return
        )
        res = self._request(
            "POST",
            self.shipment_url,
            json_payload=payload,
            authenticated=True,
            log_name="logista_shipment",
            raise_on_error=True,
        )
        shipments = res.get("Shipments") if isinstance(res, dict) else None
        if not shipments or not isinstance(shipments, list):
            raise UserError(
                _("Unexpected response from Logista Parcel shipment API: %s") % res
            )
        first = shipments[0]
        shipment_id = str(first.get("ShipmentId") or "").strip()
        session_id = str(first.get("SessionId") or "").strip()
        if not shipment_id:
            raise UserError(
                _("Logista Parcel API did not return a valid ShipmentId: %s") % first
            )
        return {
            "shipment_id": shipment_id,
            "session_id": session_id,
            "references": first.get("References") or [main_ref],
            "main_reference": main_ref,
            "metrics": metrics,
        }

    def get_plaza_routing(
        self, country_code, zip_code, service_id=None, sector_code=None
    ):
        """Query `GET /Visor/rest/unauthenticated/wsRepartoProductoPorPlazas`
        (Características de etiquetaje_v4 p.1) to obtain destination delegation and
        delivery zone (`delegacion`, `zonaReparto`, `delegacionCB`, `delegacioncode`).
        Non-blocking on network error so shipping never fails if Visor is offline.
        """
        keypai = get_logista_country_id(country_code) or "ES"
        codpos = format_logista_postal_code_plaza(zip_code, country_code)
        if not codpos:
            return {}
        params = {
            "keypai": keypai,
            "codpos": codpos,
            "keytsv": str(service_id or self.carrier_id.logista_service_id or "1"),
            "keyact": str(sector_code or self.carrier_id.logista_sector_code or "0"),
        }
        res = self._request(
            "GET",
            self.plaza_url,
            params=params,
            authenticated=False,
            log_name="logista_plaza",
            raise_on_error=False,
        )
        if not isinstance(res, dict) or res.get("_error"):
            _logger.warning(
                "Logista plaza lookup failed for %s %s: %s",
                keypai,
                codpos,
                res.get("error_message") if isinstance(res, dict) else res,
            )
            return {}
        return {
            "zona_reparto": res.get("zonaReparto") or "",
            "delegacion": res.get("delegacion") or "",
            "delegacion_cb": res.get("delegacionCB") or "",
            "delegacion_code": res.get("delegacioncode") or "",
        }

    @staticmethod
    def _zpl_escape(text):
        return (
            str(text or "")
            .replace("^", " ")
            .replace("~", " ")
            .replace("\n", " ")
            .replace("\r", " ")
            .strip()
        )

    def render_zpl_labels(self, label_items):
        """Render 100x150mm (203 dpi) Zebra ZPL thermal labels matching the official
        Logista Parcel label structure and 34-digit Code 128C/B barcode.
        """
        blocks = []
        for lbl in label_items:
            zpl_bc = format_logista_code128_subsets(lbl["barcode"], mode="zpl")
            unit_tag = "Pal." if lbl.get("is_pallet") else "Bto."
            blocks.append(
                "\n".join(
                    [
                        "^XA",
                        "^CI28",
                        "^PW800",
                        "^LL1200",
                        "^FO30,25^A0N,36,36^FDLogista PARCEL^FS",
                        f"^FO330,20^A0N,54,54^FD{self._zpl_escape(lbl['delegacion_destino'])}^FS",
                        f"^FO30,68^A0N,22,22^FD{self._zpl_escape(lbl['origin_header'])}^FS",
                        "^FO25,96^GB750,4,4^FS",
                        f"^FO30,112^A0N,26,26^FD{self._zpl_escape(lbl['remitente_name'])}^FS",
                        f"^FO30,142^A0N,22,22^FD{self._zpl_escape(lbl['remitente_street'])}^FS",
                        f"^FO30,168^A0N,22,22^FD{self._zpl_escape(lbl['remitente_cp_city'])}^FS",
                        "^FO25,200^GB750,240,4^FS",
                        f"^FO40,215^A0N,30,30^FD{self._zpl_escape(lbl['consignatario_name'])}^FS",
                        f"^FO40,252^A0N,24,24^FD{self._zpl_escape(lbl['consignatario_street'])}^FS",
                        f"^FO40,282^A0N,24,24^FD{self._zpl_escape(lbl['consignatario_dept'])}^FS",
                        "^FO40,316^GB510,46,46^FS",
                        f"^FO48,324^FR^A0N,34,34^FD{self._zpl_escape(lbl['consignatario_cp_city'])}^FS",
                        f"^FO40,372^A0N,22,22^FD{self._zpl_escape(lbl['consignatario_country_tel'])}^FS",
                        f"^FO575,235^A0N,88,88^FD{self._zpl_escape(lbl['zona_reparto'])}^FS",
                        f"^FO565,335^A0N,24,24^FD{self._zpl_escape(lbl['sector_label'])}^FS",
                        f"^FO40,460^A0N,56,56^FD{self._zpl_escape(lbl['service_name'])}^FS",
                        "^FO40,525^GB210,34,34^FS",
                        f"^FO50,530^FR^A0N,24,24^FD{self._zpl_escape(lbl['freight_label'])}^FS",
                        f"^FO40,570^A0N,22,22^FD{self._zpl_escape(lbl['obs_1'])}^FS",
                        f"^FO40,598^A0N,22,22^FD{self._zpl_escape(lbl['obs_2'])}^FS",
                        (
                            "^FO450,458^A0N,34,34^FDRef. "
                            f"{self._zpl_escape(lbl['main_reference'])}^FS"
                        ),
                        (
                            f"^FO450,500^A0N,30,30^FD{unit_tag} "
                            f"{lbl['unit_index']}/{lbl['control_packages']} "
                            f"Tot: {lbl['packages']} Btos.^FS"
                        ),
                        f"^FO450,538^A0N,26,26^FDPeso: {lbl['weight_kg']} Kgs.^FS",
                        "^FO25,640^GB750,4,4^FS",
                        f"^FO140,680^BY2,3,230^BCN,230,Y,N,N,N^FD{zpl_bc}^FS",
                        "^XZ",
                    ]
                )
            )
        return "\n".join(blocks).encode("utf-8")
