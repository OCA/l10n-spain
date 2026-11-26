# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
import math
import re

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

from .transaher_master_data import (
    TRANSAHER_BULTOS_TAG_MODES,
    TRANSAHER_CANCELLABLE_DELIVERY_STATES,
    TRANSAHER_DEFAULT_CENTRO,
    TRANSAHER_DEFAULT_HOLDING,
    TRANSAHER_DEFAULT_PROTOCOLO,
    TRANSAHER_DEFAULT_SECCION,
    TRANSAHER_INCOTERM_TO_PORTES,
    TRANSAHER_LABEL_MODES,
    TRANSAHER_PACKAGING_CODES,
    TRANSAHER_PALLET_CODES,
    TRANSAHER_PORTES_TYPES,
    TRANSAHER_PROD_MBRIDGE_URL,
    TRANSAHER_PROD_MCLIENT_URL,
    TRANSAHER_TEST_MBRIDGE_URL,
    TRANSAHER_TEST_MCLIENT_URL,
    TRANSAHER_TRACKING_URL_TEMPLATE,
    build_transaher_barcode_24,
    format_transaher_decimal,
    format_transaher_postal_code,
    get_transaher_country_code,
    map_transaher_status_to_delivery_state,
    parse_transaher_datetime,
    sanitize_transaher_field,
)
from .transaher_request import TransaherRequest

_logger = logging.getLogger(__name__)

_TRANSAHER_TOKEN_INVALIDATION_FIELDS = {
    "prod_environment",
    "transaher_client_code_test",
    "transaher_password_test",
    "transaher_client_code_prod",
    "transaher_password_prod",
    "transaher_test_mbridge_url",
    "transaher_prod_mbridge_url",
    "transaher_holding",
}


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("transaher", "Transaher")],
        ondelete={
            "transaher": lambda recs: recs.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            )
        },
    )

    # =========================================================================
    # TRANSAHER SOAP CREDENTIALS & ENDPOINTS
    # =========================================================================
    transaher_client_code_test = fields.Char(
        string="Test Client Code (CodigoCliente)",
        copy=False,
        groups="base.group_system",
        help="Numeric client code provided by Transaher for the test environment.",
    )
    transaher_password_test = fields.Char(
        string="Test Password (PasswordCliente)",
        copy=False,
        groups="base.group_system",
        help="Password provided by Transaher for the test environment.",
    )
    transaher_client_code_prod = fields.Char(
        string="Production Client Code (CodigoCliente)",
        copy=False,
        groups="base.group_system",
        help="Numeric client code provided by Transaher for production.",
    )
    transaher_password_prod = fields.Char(
        string="Production Password (PasswordCliente)",
        copy=False,
        groups="base.group_system",
        help="Password provided by Transaher for production.",
    )
    transaher_test_mclient_url = fields.Char(
        string="Test MClient Base URL",
        default=TRANSAHER_TEST_MCLIENT_URL,
        help=(
            "Base URL for GeneXus SOAP services in test mode "
            "(awsprcsatsoap, awsexpbaja, awsmnfprtsoap)."
        ),
    )
    transaher_test_mbridge_url = fields.Char(
        string="Test MBridge Base URL",
        default=TRANSAHER_TEST_MBRIDGE_URL,
        help=(
            "Base URL for WCF SOAP services in test mode "
            "(wsgetToken, wsetiexpsoap, wsInformacionTransporte)."
        ),
    )
    transaher_prod_mclient_url = fields.Char(
        string="Production MClient Base URL",
        default=TRANSAHER_PROD_MCLIENT_URL,
        help=(
            "Definitive production URL for MClient SOAP services "
            "provided by Transaher."
        ),
    )
    transaher_prod_mbridge_url = fields.Char(
        string="Production MBridge Base URL",
        default=TRANSAHER_PROD_MBRIDGE_URL,
        help=(
            "Definitive production URL for MBridge SOAP services "
            "provided by Transaher."
        ),
    )
    transaher_tracking_url = fields.Char(
        string="Tracking Portal URL",
        default=TRANSAHER_TRACKING_URL_TEMPLATE,
        help="Transaher web portal URL for shipment tracking links.",
    )

    # Cached 20-minute security token (Section 2.2)
    transaher_cached_token = fields.Char(
        string="Cached Security Token",
        copy=False,
        groups="base.group_system",
    )
    transaher_token_valid_until = fields.Datetime(
        string="Token Valid Until",
        copy=False,
        groups="base.group_system",
    )

    # =========================================================================
    # PROTOCOL & EXPEDITION PARAMETERS
    # =========================================================================
    transaher_holding = fields.Integer(
        string="Holding Code (CodigoHolding)",
        default=TRANSAHER_DEFAULT_HOLDING,
        help=(
            "Fixed holding code (0 per Transaher Technical Manual "
            "Sections 2.1 & 4.2)."
        ),
    )
    transaher_seccion = fields.Integer(
        string="Section Code (Seccod)",
        default=TRANSAHER_DEFAULT_SECCION,
        help="Default section code (10 per Transaher Technical Manual Section 4.2).",
    )
    transaher_centro_cod = fields.Integer(
        string="Origin Center Code (Centro)",
        default=TRANSAHER_DEFAULT_CENTRO,
        help=(
            "Origin Transaher center code (e.g. 461 for Valencia, 81 for Barcelona). "
            "Used as fallback in barcodes and cancellations."
        ),
    )
    transaher_centro_label = fields.Char(
        string="Origin Center Label",
        default="461 VALENCIA",
        help=(
            "Origin center label printed in Zone 1 of local Transaher labels "
            "(e.g. '81 BARCELONA' or '461 VALENCIA')."
        ),
    )
    transaher_protocolo = fields.Integer(
        string="Protocol Code (Protocolo)",
        default=TRANSAHER_DEFAULT_PROTOCOLO,
        help=(
            "Fixed EDI/SOAP protocol code (20 per Transaher Technical Manual "
            "Sections 3.1 & 8)."
        ),
    )
    transaher_portes = fields.Selection(
        selection=TRANSAHER_PORTES_TYPES,
        string="Default Freight Terms (Tipo de Portes)",
        default="1",
        required=True,
        help=(
            "Field 8 of Datosentrada: 1 = Freight Prepaid (Pagados), "
            "2 = Freight Collect (Debidos)."
        ),
    )
    transaher_use_order_incoterm = fields.Boolean(
        string="Map Freight Terms from Incoterm",
        default=True,
        help=(
            "Automatically map Sale Order / Picking Incoterms "
            "(EXW/FCA -> 2 Debidos; DAP/CPT/DDP -> 1 Pagados)."
        ),
    )
    transaher_send_volume = fields.Boolean(
        string="Declare Volume (m³) in Shipments",
        default=True,
        help="Send package volume in Field 13 of Datosentrada (format 123,123).",
    )

    # =========================================================================
    # PACKAGING & LABEL PRINTING OPTIONS (SECTIONS 5 & 6)
    # =========================================================================
    transaher_default_package_type_id = fields.Many2one(
        comodel_name="stock.package.type",
        string="Default Package / Pallet Type",
        domain="[('package_carrier_type', '=', 'transaher')]",
        help=(
            "Default package or pallet type when the picking or sale order "
            "has no detailed packages."
        ),
    )
    transaher_default_packaging_code = fields.Selection(
        selection=TRANSAHER_PACKAGING_CODES,
        string="Default Packaging Classification",
        default="BUL",
    )
    transaher_label_mode = fields.Selection(
        selection=TRANSAHER_LABEL_MODES,
        string="Label Generation Mode",
        default="ws_with_fallback",
        required=True,
        help=(
            "- Transaher Web Service PDF (with Local Fallback): Downloads the "
            "official PDF/ZPL from wsEtiExpSOAP and falls back to the local "
            "24-digit barcode QWeb label if unavailable.\n"
            "- Transaher Web Service Only: Exclusively uses wsEtiExpSOAP.\n"
            "- Local Standard Transaher Label PDF: Generates the label locally "
            "following Section 5 of the manual."
        ),
    )
    transaher_bultos_tag_mode = fields.Selection(
        selection=TRANSAHER_BULTOS_TAG_MODES,
        string="wsEtiExpSOAP Package Tag (<Bultos>)",
        default="reprint_all",
        required=True,
        help=(
            "Controls the <Bultos> tag in wsEtiExpSOAP (Section 6.1): '-1' prints "
            "all packages of the expedition; empty prints only unprinted packages."
        ),
    )
    transaher_posicion_inicial = fields.Integer(
        string="Initial Print Position (Multi-Label Sheet)",
        default=0,
        help=(
            "Optional PosicionInicialImpresion parameter for multi-label A4 sheets "
            "(0 = omit / start from 1)."
        ),
    )

    # =========================================================================
    # TARIFF ENGINE & COST CONTROL
    # =========================================================================
    transaher_volumetric_factor = fields.Float(
        string="Volumetric Factor (kg / m³)",
        default=250.0,
        help=(
            "Volume-to-chargeable-weight conversion factor for road freight "
            "(e.g. 250 or 333 kg/m³). Set 0 to use gross weight only."
        ),
    )
    transaher_fuel_surcharge_pct = fields.Float(
        string="Default Fuel Surcharge (%)",
        default=0.0,
        help=(
            "Default fuel surcharge percentage applied in the local tariff table "
            "when a rule does not specify its own."
        ),
    )
    transaher_cod_surcharge_pct = fields.Float(
        string="Default COD Surcharge (%)",
        default=0.0,
        help="Default Cash-on-Delivery (Contra reembolso) surcharge percentage.",
    )
    transaher_insurance_surcharge_pct = fields.Float(
        string="Default Insurance Surcharge (%)",
        default=0.0,
        help=(
            "Default cargo insurance percentage applied when insured value "
            "is declared."
        ),
    )
    transaher_free_for_customer = fields.Boolean(
        string="Free Shipping for Customer (Keep Internal Cost)",
        default=False,
        help=(
            "If enabled, the customer is charged 0.00 € on the sale order line "
            "while Odoo preserves the internal Transaher cost on the sale order "
            "and picking."
        ),
    )
    transaher_tariff_rule_ids = fields.One2many(
        comodel_name="transaher.tariff.rule",
        inverse_name="carrier_id",
        string="Tariff Table by Zones / Weights / Packages",
        copy=True,
    )

    # =========================================================================
    # STANDARD ODOO CAPABILITY HOOKS & TOKEN CACHE INVALIDATION
    # =========================================================================
    @api.depends("delivery_type")
    def _compute_can_generate_return(self):
        res = super()._compute_can_generate_return()
        for carrier in self:
            if carrier.delivery_type == "transaher":
                carrier.can_generate_return = True
        return res

    @api.depends("delivery_type")
    def _compute_supports_shipping_insurance(self):
        res = super()._compute_supports_shipping_insurance()
        for carrier in self:
            if carrier.delivery_type == "transaher":
                carrier.supports_shipping_insurance = True
        return res

    def _get_delivery_label_prefix(self):
        if self.delivery_type == "transaher":
            return "Transaher_Label"
        return super()._get_delivery_label_prefix()

    def get_return_label_prefix(self):
        if self.delivery_type == "transaher":
            return "Transaher_Return"
        return super().get_return_label_prefix()

    def _transaher_get_default_custom_package_code(self):
        return self.transaher_default_packaging_code or "BUL"

    def write(self, vals):
        if (
            _TRANSAHER_TOKEN_INVALIDATION_FIELDS.intersection(vals)
            and "transaher_cached_token" not in vals
        ):
            vals = dict(
                vals,
                transaher_cached_token=False,
                transaher_token_valid_until=False,
            )
        return super().write(vals)

    # =========================================================================
    # CLIENT, UI ACTIONS & WEIGHT/PACKAGE HELPERS
    # =========================================================================
    def _transaher_get_client(self):
        self.ensure_one()
        return TransaherRequest(self)

    def action_test_transaher_connection(self):
        """Test authentication against `wsgetToken.svc` and show notification."""
        self.ensure_one()
        client = self._transaher_get_client()
        token = client.get_token(force_refresh=True)
        masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
        env_label = _("Production") if self.prod_environment else _("Test")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Transaher Connection Successful (%s)") % env_label,
                "message": _(
                    "Security token successfully obtained from wsgetToken (%s). "
                    "Valid for 20 minutes."
                )
                % masked,
                "type": "success",
                "sticky": False,
            },
        }

    def action_open_manifest_wizard(self):
        """Open the Daily Transaher Manifest (`awsmnfprtsoap`) wizard."""
        self.ensure_one()
        return {
            "name": _("Transaher Daily Manifest"),
            "type": "ir.actions.act_window",
            "res_model": "transaher.manifest.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_carrier_id": self.id,
            },
        }

    def _transaher_convert_weight_to_kg(self, weight):
        if not weight:
            return 0.0
        weight_uom = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        kg_uom = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False)
        if weight_uom and kg_uom and weight_uom != kg_uom:
            return weight_uom._compute_quantity(weight, kg_uom, round=False)
        return float(weight)

    def _transaher_convert_volume_to_m3(self, volume):
        if not volume:
            return 0.0
        vol_uom = self.env[
            "product.template"
        ]._get_volume_uom_id_from_ir_config_parameter()
        m3_uom = self.env.ref("uom.product_uom_cubic_meter", raise_if_not_found=False)
        if vol_uom and m3_uom and vol_uom != m3_uom:
            return vol_uom._compute_quantity(volume, m3_uom, round=False)
        return float(volume)

    def _transaher_convert_dimension_to_cm(self, dimension_value):
        if not dimension_value:
            return 0
        length_uom = self.env[
            "product.template"
        ]._get_length_uom_id_from_ir_config_parameter()
        cm_uom = self.env.ref("uom.product_uom_cm", raise_if_not_found=False)
        if length_uom and cm_uom and length_uom != cm_uom:
            cm_val = length_uom._compute_quantity(dimension_value, cm_uom, round=False)
        else:
            cm_val = float(dimension_value)
        return max(1, int(round(cm_val)))

    def _transaher_get_package_dimensions_cm(self, package_type=None):
        self.ensure_one()
        pkg_type = package_type or self.transaher_default_package_type_id
        pkg_code = (
            (
                pkg_type.transaher_packaging_code
                if pkg_type and pkg_type.transaher_packaging_code
                else None
            )
            or (
                pkg_type.shipper_package_code
                if pkg_type and pkg_type.shipper_package_code
                else None
            )
            or self.transaher_default_packaging_code
            or "BUL"
        )
        if (
            pkg_type
            and pkg_type.packaging_length
            and pkg_type.width
            and pkg_type.height
        ):
            l_cm = self._transaher_convert_dimension_to_cm(pkg_type.packaging_length)
            w_cm = self._transaher_convert_dimension_to_cm(pkg_type.width)
            h_cm = self._transaher_convert_dimension_to_cm(pkg_type.height)
        elif pkg_code in ("EUR", "PAL"):
            l_cm, w_cm, h_cm = 120, 80, 120
        elif pkg_code == "MED":
            l_cm, w_cm, h_cm = 80, 60, 100
        elif pkg_code == "SOB":
            l_cm, w_cm, h_cm = 35, 25, 5
        else:
            l_cm, w_cm, h_cm = 40, 30, 30
        return l_cm, w_cm, h_cm, pkg_code

    def _transaher_compute_chargeable_weight(self, gross_weight_kg, volume_m3=0.0):
        self.ensure_one()
        vol_weight = (volume_m3 or 0.0) * (self.transaher_volumetric_factor or 0.0)
        return max(float(gross_weight_kg or 0.0), vol_weight)

    def _transaher_resolve_portes_code(self, partner=None, order=None, picking=None):
        """Resolve Field 8 (`Tipo de portes`: '1' = Pagados, '2' = Debidos)."""
        self.ensure_one()
        if picking and picking.transaher_portes in ("1", "2"):
            return picking.transaher_portes
        if self.transaher_use_order_incoterm:
            incoterm = False
            if picking and getattr(picking, "incoterm", False):
                incoterm = picking.incoterm
            elif (
                picking
                and picking.sale_id
                and getattr(picking.sale_id, "incoterm", False)
            ):
                incoterm = picking.sale_id.incoterm
            elif order and getattr(order, "incoterm", False):
                incoterm = order.incoterm
            if incoterm and incoterm.code in TRANSAHER_INCOTERM_TO_PORTES:
                return TRANSAHER_INCOTERM_TO_PORTES[incoterm.code]
        if partner and partner.transaher_portes_default in ("1", "2"):
            return partner.transaher_portes_default
        return self.transaher_portes or "1"

    def _transaher_resolve_insured_value(self, order=None, picking=None):
        """Resolve declared cargo insured value (Field 14): explicit picking override or
        carrier `shipping_insurance` percentage of untaxed order value.
        """
        self.ensure_one()
        if picking and picking.transaher_insured_value > 0.0:
            return picking.transaher_insured_value
        if self.shipping_insurance and self.shipping_insurance > 0:
            so = order or (picking.sale_id if picking else False)
            if so and so.amount_untaxed > 0.0:
                return round(so.amount_untaxed * (self.shipping_insurance / 100.0), 2)
        return 0.0

    @staticmethod
    def _transaher_split_observations(obs_1="", obs_2="", fallback_text=""):
        """Prepare Field 9 (`Observaciones 1`) and Field 10 (`Observaciones 2`)."""
        line_1 = sanitize_transaher_field(obs_1, max_len=70)
        line_2 = sanitize_transaher_field(obs_2, max_len=70)
        if line_1 or line_2:
            return line_1, line_2

        plain = sanitize_transaher_field(fallback_text, max_len=145)
        if not plain:
            return "", ""
        if len(plain) <= 70:
            return plain, ""
        cut = plain.rfind(" ", 0, 71)
        if cut <= 0:
            cut = 70
        return plain[:cut].strip(), plain[cut:].strip()[:70]

    def _transaher_estimate_order_metrics(self, order):
        """Compute `(gross_weight_kg, total_vol_m3, packages_qty)` from `sale.order`,
        using OCA `stock_picking_volume` and `delivery_package_number` when available.
        """
        self.ensure_one()
        total_weight_kg = 0.0
        order_vol_raw = 0.0
        for line in order.order_line.filtered(
            lambda ln: not ln.is_delivery
            and not ln.display_type
            and ln.product_id.type in ("consu", "product")
        ):
            line_weight = 0.0
            if line.product_id.weight:
                line_weight = line.product_id.weight * line.product_uom_qty
            elif hasattr(line.product_id, "_get_packaging_unit_weight"):
                pkg_unit_weight = line.product_id._get_packaging_unit_weight(
                    packaging=line.product_packaging_id,
                    weight_type="gross",
                )
                line_weight = (pkg_unit_weight or 0.0) * line.product_uom_qty
            total_weight_kg += self._transaher_convert_weight_to_kg(line_weight)
            order_vol_raw += line.product_id._get_volume_for_qty(
                line.product_uom_qty, line.product_uom
            )

        if total_weight_kg <= 0.0:
            fallback_weight = (
                order._get_estimated_weight()
                if hasattr(order, "_get_estimated_weight")
                else 0.0
            )
            total_weight_kg = max(
                1.0, self._transaher_convert_weight_to_kg(fallback_weight) or 1.0
            )

        l_cm, w_cm, h_cm, pkg_code = self._transaher_get_package_dimensions_cm()
        active_pickings = order.picking_ids.filtered(lambda p: p.state != "cancel")
        defined_packages = sum(active_pickings.mapped("number_of_packages"))
        if defined_packages > 0:
            packages_qty = defined_packages
        else:
            max_pkg_weight = (
                self._transaher_convert_weight_to_kg(
                    self.transaher_default_package_type_id.max_weight
                )
                if self.transaher_default_package_type_id
                and self.transaher_default_package_type_id.max_weight > 0
                else (700.0 if pkg_code in TRANSAHER_PALLET_CODES else 25.0)
            )
            packages_qty = (
                max(1, int(math.ceil(total_weight_kg / max_pkg_weight)))
                if max_pkg_weight > 0
                else 1
            )

        order_vol_m3 = self._transaher_convert_volume_to_m3(order_vol_raw)
        if order_vol_m3 > 0.0:
            total_vol_m3 = round(order_vol_m3, 3)
        else:
            unit_vol_m3 = (l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0)
            total_vol_m3 = max(0.001, round(unit_vol_m3 * packages_qty, 3))
        return total_weight_kg, total_vol_m3, packages_qty

    def _transaher_prepare_picking_metrics(self, picking):
        """Compute `(gross_weight_kg, total_vol_m3, packages_qty)` via OCA fields:
        - `picking.number_of_packages` (`delivery_package_number`)
        - `picking.volume` (`stock_picking_volume`)
        with fallback to physical `stock.quant.package` and default dimensions.
        """
        self.ensure_one()
        packages = picking.move_line_ids.mapped("result_package_id")
        picking_vol_m3 = self._transaher_convert_volume_to_m3(picking.volume)
        total_weight_kg = 0.0
        pkg_dims_vol_m3 = 0.0

        if packages:
            for pkg in packages:
                pkg_type = (
                    pkg.package_type_id
                    or picking.transaher_package_type_id
                    or self.transaher_default_package_type_id
                )
                l_cm, w_cm, h_cm, _code = self._transaher_get_package_dimensions_cm(
                    pkg_type
                )
                pkg_shipping_w = getattr(pkg, "shipping_weight", 0.0)
                if pkg_shipping_w and pkg_shipping_w > 0.0:
                    pkg_weight_kg = self._transaher_convert_weight_to_kg(pkg_shipping_w)
                elif pkg.quant_ids and getattr(pkg, "weight", 0.0) > 0.0:
                    pkg_weight_kg = self._transaher_convert_weight_to_kg(pkg.weight)
                else:
                    pkg_moves_weight = sum(
                        ml.product_id.weight * ml.quantity
                        for ml in picking.move_line_ids.filtered(
                            lambda m, p=pkg: m.result_package_id == p
                        )
                    ) + (
                        pkg_type.base_weight
                        if pkg_type and pkg_type.base_weight
                        else 0.0
                    )
                    pkg_weight_kg = max(
                        0.1, self._transaher_convert_weight_to_kg(pkg_moves_weight)
                    )
                total_weight_kg += pkg_weight_kg
                pkg_dims_vol_m3 += (l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0)
            packages_qty = max(len(packages), picking.number_of_packages or 0)
            total_vol_m3 = (
                round(picking_vol_m3, 3)
                if picking_vol_m3 > 0.0
                else round(pkg_dims_vol_m3, 3)
            )
            return round(max(0.1, total_weight_kg), 3), total_vol_m3, packages_qty

        raw_weight = picking.shipping_weight or picking.weight or 0.0
        total_weight_kg = self._transaher_convert_weight_to_kg(raw_weight)
        if total_weight_kg <= 0.0:
            for move in picking.move_ids.filtered(lambda m: m.state != "cancel"):
                if move.product_id.weight:
                    total_weight_kg += self._transaher_convert_weight_to_kg(
                        move.product_id.weight * (move.quantity or move.product_uom_qty)
                    )
                elif hasattr(move.product_id, "_get_packaging_unit_weight"):
                    w_unit = move.product_id._get_packaging_unit_weight(
                        packaging=move.product_packaging_id,
                        weight_type="gross",
                    )
                    total_weight_kg += self._transaher_convert_weight_to_kg(
                        (w_unit or 0.0) * (move.quantity or move.product_uom_qty)
                    )
        total_weight_kg = max(1.0, total_weight_kg)

        packages_qty = max(1, picking.number_of_packages or 1)
        if picking_vol_m3 > 0.0:
            total_vol_m3 = round(picking_vol_m3, 3)
        else:
            l_cm, w_cm, h_cm, _code = self._transaher_get_package_dimensions_cm(
                picking.transaher_package_type_id
                or self.transaher_default_package_type_id
            )
            unit_vol_m3 = (l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0)
            total_vol_m3 = max(0.001, round(unit_vol_m3 * packages_qty, 3))
        return round(total_weight_kg, 3), total_vol_m3, packages_qty

    def _transaher_build_datos_entrada(
        self,
        picking,
        gross_weight_kg,
        total_vol_m3,
        packages_qty,
        consignee=None,
        is_return=False,
    ):
        """Construct the 18-field pipe-separated `Datosentrada` string (Section 3.2):
        1: Nombre destinatario (40, Oblig)
        2: Dirección destinatario (50, Oblig)
        3: Código país (3, Oblig: 011=ES, 010=PT)
        4: Código postal (5, Oblig)
        5: Código repetición postal (Opt)
        6: Nombre población destinatario (45, Oblig)
        7: Referencia interna / nº albarán empresa (20, Opt)
        8: Tipo de portes (1, Oblig: 1=Pagados, 2=Debidos)
        9: Observaciones línea 1 (70, Opt)
        10: Observaciones línea 2 (70, Opt)
        11: Número de bultos (4, Oblig)
        12: Peso en kilos (8, Oblig, formato 12345,123)
        13: Volumen (6, Opt, formato 123,123)
        14: Valor asegurado (9, Opt, formato 123456,123)
        15: Valor contra reembolso (9, Opt, formato 123456,123)
        16: Email del destinatario (50, Opt)
        17: Teléfono del destinatario (15, Opt)
        18: Referencia interna / nº albarán del remitente (20, Opt)
        """
        self.ensure_one()
        partner = consignee or picking.partner_id
        if not partner:
            raise UserError(
                _("Picking %s does not have a delivery address assigned.")
                % picking.name
            )

        street_full = " ".join(filter(None, [partner.street, partner.street2])).strip()
        city_name = (partner.city or partner.state_id.name or "").strip()
        if (
            not street_full
            or not partner.zip
            or not city_name
            or not partner.country_id
        ):
            raise UserError(
                _(
                    "Consignee '%s' must have Street, Postal Code, City, and "
                    "Country configured to register an expedition in Transaher."
                )
                % partner.display_name
            )

        country_iso = (partner.country_id.code or "ES").upper()
        f1_name = sanitize_transaher_field(
            partner.name or partner.commercial_partner_id.name, max_len=40
        )
        f2_street = sanitize_transaher_field(street_full, max_len=50)
        f3_country = get_transaher_country_code(partner.country_id, fallback="011")
        f4_zip = format_transaher_postal_code(
            partner.zip, country_code=country_iso, for_barcode=False
        )
        if not f4_zip:
            raise UserError(
                _("Invalid postal code ('%s') for Transaher shipment.") % partner.zip
            )

        f5_rep_postal = sanitize_transaher_field(
            (
                not is_return
                and (
                    picking.transaher_postal_rep_code
                    or partner.transaher_postal_rep_code
                )
            )
            or "",
            max_len=5,
        )
        f6_city = sanitize_transaher_field(city_name, max_len=45)

        order_ref = ""
        if picking.sale_id and picking.sale_id.client_order_ref:
            order_ref = picking.sale_id.client_order_ref
        elif picking.origin:
            order_ref = picking.origin
        elif picking.name:
            order_ref = picking.name
        if is_return:
            order_ref = f"RET-{order_ref or picking.name}"
        f7_company_ref = sanitize_transaher_field(order_ref, max_len=20)

        f8_portes = self._transaher_resolve_portes_code(
            partner=partner, picking=picking
        )

        fallback_notes = partner.transaher_delivery_notes or ""
        if not fallback_notes and picking.note:
            fallback_notes = html2plaintext(picking.note or "")
        f9_obs1, f10_obs2 = self._transaher_split_observations(
            obs_1=picking.transaher_obs_1
            if not is_return
            else _("Return pickup %s") % picking.name,
            obs_2=picking.transaher_obs_2 if not is_return else "",
            fallback_text=fallback_notes,
        )

        f11_bultos = str(min(9999, max(1, int(packages_qty or 1))))
        f12_peso = format_transaher_decimal(
            gross_weight_kg, max_len=8, max_decimals=3, empty_if_zero=False
        )
        f13_volumen = (
            format_transaher_decimal(
                total_vol_m3, max_len=6, max_decimals=3, empty_if_zero=True
            )
            if self.transaher_send_volume
            else ""
        )
        insured_val = (
            self._transaher_resolve_insured_value(picking=picking)
            if not is_return
            else 0.0
        )
        f14_insured = format_transaher_decimal(
            insured_val, max_len=9, max_decimals=3, empty_if_zero=True
        )
        f15_cod = (
            format_transaher_decimal(
                picking.transaher_cod_amount,
                max_len=9,
                max_decimals=3,
                empty_if_zero=True,
            )
            if not is_return
            else ""
        )
        f16_email = sanitize_transaher_field(partner.email or "", max_len=50)

        raw_phone = partner.mobile or partner.phone or ""
        clean_phone = re.sub(r"[^\d+]", "", raw_phone)
        f17_phone = sanitize_transaher_field(clean_phone, max_len=15)

        sender_ref = f"RET-{picking.name}" if is_return else (picking.name or "")
        f18_sender_ref = sanitize_transaher_field(sender_ref, max_len=20)

        fields_18 = [
            f1_name,
            f2_street,
            f3_country,
            f4_zip,
            f5_rep_postal,
            f6_city,
            f7_company_ref,
            f8_portes,
            f9_obs1,
            f10_obs2,
            f11_bultos,
            f12_peso,
            f13_volumen,
            f14_insured,
            f15_cod,
            f16_email,
            f17_phone,
            f18_sender_ref,
        ]
        return "|".join(fields_18)

    # =========================================================================
    # TARIFF CALCULATION (SALE.ORDER & STOCK.PICKING)
    # =========================================================================
    def _transaher_rate_from_tariff_table(
        self,
        partner,
        chargeable_weight_kg,
        packages_qty=1,
        cod_amount=0.0,
        insured_value=0.0,
    ):
        self.ensure_one()
        active_rules = self.transaher_tariff_rule_ids.filtered("active").sorted(
            "sequence"
        )
        for rule in active_rules:
            if rule._match_destination_and_shipment(
                partner, chargeable_weight_kg, packages_qty
            ):
                cost, breakdown = rule._compute_rule_cost(
                    chargeable_weight_kg=chargeable_weight_kg,
                    packages_qty=packages_qty,
                    cod_amount=cod_amount,
                    insured_value=insured_value,
                )
                return cost, breakdown, rule
        return None, None, None

    def transaher_rate_shipment(self, order):
        """Calculate shipping rate for `sale.order` via Transaher Tariff Rules
        and volumetric weight conversion, preserving internal cost when free.
        """
        self.ensure_one()
        partner = order.partner_shipping_id or order.partner_id
        if not partner.country_id or not partner.zip:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "The consignee (%s) must have a Postal Code and Country "
                    "to calculate the Transaher rate."
                )
                % partner.display_name,
                "warning_message": False,
            }

        gross_weight_kg, total_vol_m3, packages_qty = (
            self._transaher_estimate_order_metrics(order)
        )
        chargeable_weight_kg = self._transaher_compute_chargeable_weight(
            gross_weight_kg=gross_weight_kg,
            volume_m3=total_vol_m3,
        )
        insured_value = self._transaher_resolve_insured_value(order=order)

        table_cost, table_breakdown, matched_rule = (
            self._transaher_rate_from_tariff_table(
                partner=partner,
                chargeable_weight_kg=chargeable_weight_kg,
                packages_qty=packages_qty,
                insured_value=insured_value,
            )
        )
        if table_cost is None:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "No matching rule found in Transaher Tariff Table for %(partner)s "
                    "(ZIP %(zip)s, %(country)s, %(weight).2f chargeable kg, "
                    "%(pkgs)d packages)."
                )
                % {
                    "partner": partner.display_name,
                    "zip": partner.zip,
                    "country": partner.country_id.name,
                    "weight": chargeable_weight_kg,
                    "pkgs": packages_qty,
                },
                "warning_message": False,
            }

        summary_line = _(
            "Gross weight: %(gross).2f kg | Vol: %(vol).3f m³ | "
            "Chargeable weight: %(chg).2f kg | Packages: %(pkgs)d"
        ) % {
            "gross": gross_weight_kg,
            "vol": total_vol_m3,
            "chg": chargeable_weight_kg,
            "pkgs": packages_qty,
        }
        full_breakdown = f"{table_breakdown}\n{summary_line}"

        currency_code = (
            matched_rule.currency_id.name if matched_rule.currency_id else "EUR"
        )
        order_currency = (
            order.currency_id
            or order.company_id.currency_id
            or self.env.company.currency_id
        )
        source_currency = (
            self.env["res.currency"].search([("name", "=", currency_code)], limit=1)
            or order_currency
        )
        if source_currency != order_currency:
            cost_in_order_curr = source_currency._convert(
                table_cost,
                order_currency,
                order.company_id or self.env.company,
                order.date_order or fields.Date.context_today(self),
            )
        else:
            cost_in_order_curr = table_cost

        order.sudo().write(
            {
                "transaher_estimated_cost": cost_in_order_curr,
                "transaher_chargeable_weight": chargeable_weight_kg,
                "transaher_rate_breakdown": full_breakdown,
            }
        )

        customer_price = (
            0.0 if self.transaher_free_for_customer else float(cost_in_order_curr)
        )
        return {
            "success": True,
            "price": customer_price,
            "error_message": False,
            "warning_message": False,
        }

    # =========================================================================
    # LABELS, SHIPPING SUBMISSION, CANCELLATION & TRACKING
    # =========================================================================
    def _transaher_attach_label_to_picking(
        self,
        picking,
        raw_bytes,
        tracking_ref,
        extension="pdf",
        mimetype="application/pdf",
        is_return=False,
    ):
        self.ensure_one()
        if not raw_bytes:
            return False
        ext = (extension or "pdf").lower().lstrip(".")
        if ext == "zpl":
            mimetype = "text/plain"
        prefix = (
            self.get_return_label_prefix()
            if is_return
            else self._get_delivery_label_prefix()
        )
        safe_ref = (tracking_ref or picking.name or "shipment").replace("/", "_")
        filename = f"{prefix}_{safe_ref}.{ext}"
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": base64.b64encode(raw_bytes),
                "res_model": "stock.picking",
                "res_id": picking.id,
                "mimetype": mimetype or "application/pdf",
            }
        )

    def _transaher_render_local_qweb_label(self, picking):
        """Render the local standard Transaher QWeb shipping label PDF."""
        report = self.env.ref("delivery_transaher.action_report_transaher_label")
        pdf_bytes, _ext = report._render_qweb_pdf(
            report.report_name, res_ids=picking.ids
        )
        return pdf_bytes

    def _transaher_download_or_render_label(
        self, picking, bultos_override=None, is_return=False
    ):
        """Obtain `(raw_bytes, ext, mimetype, warnings)` from WS or QWeb."""
        self.ensure_one()
        warnings = []

        if self.transaher_label_mode == "local_qweb":
            pdf_bytes = self._transaher_render_local_qweb_label(picking)
            return pdf_bytes, "pdf", "application/pdf", warnings

        client = self._transaher_get_client()
        bultos_tag = (
            bultos_override
            if bultos_override is not None
            else ("-1" if self.transaher_bultos_tag_mode == "reprint_all" else "")
        )
        pos_ini = (
            str(self.transaher_posicion_inicial)
            if self.transaher_posicion_inicial > 0
            else ""
        )

        exp_req = [
            {
                "holding": picking.transaher_holding
                or self.transaher_holding
                or TRANSAHER_DEFAULT_HOLDING,
                "seccion": picking.transaher_seccion
                or self.transaher_seccion
                or TRANSAHER_DEFAULT_SECCION,
                "centro": picking.transaher_centro
                or self.transaher_centro_cod
                or TRANSAHER_DEFAULT_CENTRO,
                "codigo": picking.transaher_cod_expedicion
                or picking.carrier_tracking_ref,
                "bultos": bultos_tag,
            }
        ]

        try:
            lbl_res = client.get_labels(exp_req, posicion_inicial=pos_ini)
            raw_bytes = base64.b64decode(lbl_res["data"])
            for msg in lbl_res.get("messages") or []:
                if msg.get("description"):
                    warnings.append(
                        f"[{msg.get('type') or 'INFO'}] {msg['description']}"
                    )
            return (
                raw_bytes,
                lbl_res.get("extension") or "pdf",
                lbl_res.get("content_type") or "application/pdf",
                warnings,
            )
        except UserError as exc:
            if self.transaher_label_mode == "ws_with_fallback":
                _logger.warning(
                    "Transaher wsEtiExpSOAP failed for picking %s (%s); "
                    "generating local 24-digit barcode QWeb label.",
                    picking.name,
                    exc,
                )
                warnings.append(
                    _(
                        "wsEtiExpSOAP unavailable (%s); "
                        "local Transaher barcode label generated."
                    )
                    % str(exc)
                )
                pdf_bytes = self._transaher_render_local_qweb_label(picking)
                return pdf_bytes, "pdf", "application/pdf", warnings
            raise

    def transaher_send_shipping(self, pickings):
        """Execute the full Transaher integration flow (Section 9):
        1. `awsprcsatsoap` (Alta): register expedition and store composite key.
        2. Generate 24-character barcodes per package (`Section 5.2`).
        3. `wsgetToken` + `wsEtiExpSOAP`: download PDF/ZPL label and attach.
        """
        res = []
        client = self._transaher_get_client()

        for picking in pickings:
            partner = picking.partner_id
            gross_weight_kg, total_vol_m3, packages_qty = (
                self._transaher_prepare_picking_metrics(picking)
            )
            chargeable_weight_kg = self._transaher_compute_chargeable_weight(
                gross_weight_kg=gross_weight_kg,
                volume_m3=total_vol_m3,
            )
            datos_entrada = self._transaher_build_datos_entrada(
                picking=picking,
                gross_weight_kg=gross_weight_kg,
                total_vol_m3=total_vol_m3,
                packages_qty=packages_qty,
            )

            alta_data = client.create_expedition(datos_entrada)
            holding = alta_data.get(
                "holding", self.transaher_holding or TRANSAHER_DEFAULT_HOLDING
            )
            seccion = alta_data.get(
                "seccion", self.transaher_seccion or TRANSAHER_DEFAULT_SECCION
            )
            centro = (
                alta_data.get("centro")
                or self.transaher_centro_cod
                or TRANSAHER_DEFAULT_CENTRO
            )
            cod_exp = str(alta_data["cod_expedicion"]).strip()
            exp_key = f"{holding}.{seccion}.{centro}.{cod_exp}"

            # Generate 24-digit barcodes (Section 5.2) for each package
            country_iso = (partner.country_id.code or "ES").upper()
            barcodes = [
                build_transaher_barcode_24(
                    centro_origen=centro,
                    cod_expedicion=cod_exp,
                    bulto_num=idx,
                    postal_code=partner.zip or "00000",
                    country_code=country_iso,
                )
                for idx in range(1, packages_qty + 1)
            ]
            packages = picking.move_line_ids.mapped("result_package_id")
            for idx, pkg in enumerate(packages):
                if idx < len(barcodes):
                    pkg.transaher_barcode = barcodes[idx]

            # Calculate or inherit internal estimated shipping cost
            estimated_cost = 0.0
            cost_breakdown = ""
            if picking.sale_id and picking.sale_id.transaher_estimated_cost:
                estimated_cost = picking.sale_id.transaher_estimated_cost
                cost_breakdown = picking.sale_id.transaher_rate_breakdown or ""
            else:
                table_cost, table_breakdown, _rule = (
                    self._transaher_rate_from_tariff_table(
                        partner=partner,
                        chargeable_weight_kg=chargeable_weight_kg,
                        packages_qty=packages_qty,
                        cod_amount=picking.transaher_cod_amount,
                        insured_value=self._transaher_resolve_insured_value(
                            picking=picking
                        ),
                    )
                )
                if table_cost is not None:
                    estimated_cost = table_cost
                    cost_breakdown = table_breakdown

            picking_vals = {
                "transaher_holding": holding,
                "transaher_seccion": seccion,
                "transaher_centro": centro,
                "transaher_cod_expedicion": cod_exp,
                "transaher_fecha_expedicion": alta_data.get("fecha_expedicion")
                or False,
                "transaher_servicio": alta_data.get("servicio") or False,
                "transaher_area_dis_cod": alta_data.get("area_dis_cod") or False,
                "transaher_area_dis_dsc": alta_data.get("area_dis_dsc") or False,
                "transaher_centro_destino": alta_data.get("centro_destino") or False,
                "transaher_expedicion_ch": alta_data.get("expedicion_ch") or False,
                "transaher_barcodes": ", ".join(barcodes),
                "transaher_chargeable_weight": chargeable_weight_kg,
                "transaher_estimated_cost": estimated_cost,
                "transaher_cost_breakdown": cost_breakdown,
                "delivery_state": "shipping_recorded_in_carrier",
                "date_shipped": fields.Date.today(),
            }
            if not picking.number_of_packages:
                picking_vals["number_of_packages"] = packages_qty
            picking.write(picking_vals)

            raw_label, ext, mimetype, warnings = (
                self._transaher_download_or_render_label(
                    picking=picking,
                    is_return=False,
                )
            )
            attachment = self._transaher_attach_label_to_picking(
                picking=picking,
                raw_bytes=raw_label,
                tracking_ref=cod_exp,
                extension=ext,
                mimetype=mimetype,
                is_return=False,
            )

            if self.return_label_on_delivery:
                self.get_return_label(picking, tracking_number=cod_exp)

            tracking_url = self.transaher_get_tracking_link(
                picking, tracking_override=cod_exp
            )
            msg_items = [
                Markup(
                    "<li><b>%s:</b> <a href='%s' target='_blank'>%s</a> "
                    "(Key: <code>%s</code>)</li>"
                )
                % (_("Transaher Expedition"), tracking_url, cod_exp, exp_key),
                Markup("<li><b>%s:</b> %.2f kg / %.2f kg (%d)</li>")
                % (
                    _("Gross / Chargeable Weight"),
                    gross_weight_kg,
                    chargeable_weight_kg,
                    packages_qty,
                ),
                Markup("<li><b>%s:</b> <code>%s</code></li>")
                % (_("24-Digit Barcodes"), ", ".join(barcodes)),
            ]
            if alta_data.get("centro_destino") or alta_data.get("area_dis_dsc"):
                route_txt = " — ".join(
                    filter(
                        None,
                        [
                            alta_data.get("centro_destino"),
                            alta_data.get("area_dis_cod"),
                            alta_data.get("area_dis_dsc"),
                        ],
                    )
                )
                msg_items.append(
                    Markup("<li><b>%s:</b> %s</li>")
                    % (_("Destination Center / Zone"), route_txt)
                )
            if estimated_cost:
                msg_items.append(
                    Markup("<li><b>%s:</b> %.2f €</li>")
                    % (_("Estimated Freight Cost"), estimated_cost)
                )
            if warnings:
                msg_items.append(
                    Markup("<li><b>%s:</b> %s</li>")
                    % (_("Notices"), "; ".join(warnings))
                )

            body = (
                Markup("<p><b>%s</b></p><ul>")
                % _("Shipment successfully registered in Transaher:")
                + Markup("").join(msg_items)
                + Markup("</ul>")
            )
            picking.message_post(
                body=body,
                attachment_ids=[attachment.id] if attachment else [],
            )

            res.append(
                {
                    "exact_price": 0.0
                    if self.transaher_free_for_customer
                    else estimated_cost,
                    "tracking_number": cod_exp,
                }
            )
        return res

    def transaher_get_tracking_link(self, picking, tracking_override=None):
        self.ensure_one()
        base_url = (
            self.transaher_tracking_url or TRANSAHER_TRACKING_URL_TEMPLATE
        ).strip()
        ref = (
            tracking_override
            or picking.transaher_cod_expedicion
            or picking.carrier_tracking_ref
            or picking.name
        )
        if "{tracking_ref}" in base_url:
            return base_url.format(tracking_ref=ref)
        if "<shipmenttrackingnumber>" in base_url:
            return base_url.replace("<shipmenttrackingnumber>", ref)
        return base_url

    def transaher_cancel_shipment(self, pickings):
        """Cancel expedition via `awsExpBaja` (`Holcod`, `Seccod`, `Expctrcod`).
        Per Section 4.1, cancellation is only allowed when recorded in carrier
        (`shipping_recorded_in_carrier` — Received, Documented, or Labelled).
        """
        client = self._transaher_get_client()
        for picking in pickings:
            if (
                picking.delivery_state
                and picking.delivery_state not in TRANSAHER_CANCELLABLE_DELIVERY_STATES
            ):
                raise UserError(
                    _(
                        "Transaher expedition #%(exp)s is currently in carrier state "
                        "'%(state)s'. Per Transaher rules (Section 4.1), cancellation "
                        "via awsExpBaja is only allowed when the expedition is in "
                        "Received, Documented, or Labelled status."
                    )
                    % {
                        "exp": picking.transaher_cod_expedicion
                        or picking.carrier_tracking_ref,
                        "state": picking.tracking_state or picking.delivery_state,
                    }
                )

            exp_cod = picking.transaher_cod_expedicion or picking.carrier_tracking_ref
            if exp_cod:
                holcod = (
                    picking.transaher_holding
                    if picking.transaher_holding is not False
                    else (self.transaher_holding or TRANSAHER_DEFAULT_HOLDING)
                )
                seccod = (
                    picking.transaher_seccion
                    or self.transaher_seccion
                    or TRANSAHER_DEFAULT_SECCION
                )
                expctrcod = (
                    picking.transaher_centro
                    or self.transaher_centro_cod
                    or TRANSAHER_DEFAULT_CENTRO
                )
                client.cancel_expedition(
                    holcod=holcod,
                    seccod=seccod,
                    expctrcod=expctrcod,
                    expcod=exp_cod,
                )

            picking.write(
                {
                    "carrier_tracking_ref": False,
                    "transaher_cod_expedicion": False,
                    "transaher_barcodes": False,
                    "delivery_state": "canceled_shipment",
                    "date_delivered": False,
                    "date_shipped": False,
                }
            )
            picking.message_post(
                body=_(
                    "Transaher expedition cancelled via awsExpBaja "
                    "and unlinked from picking."
                )
            )

    def transaher_get_return_label(
        self, pickings, tracking_number=None, origin_date=None
    ):
        """Create a return expedition in Transaher and attach its PDF label."""
        client = self._transaher_get_client()
        for picking in pickings:
            shipper_partner = (
                picking.picking_type_id.warehouse_id.partner_id
                or picking.company_id.partner_id
                or self.env.company.partner_id
            )
            gross_weight_kg, total_vol_m3, packages_qty = (
                self._transaher_prepare_picking_metrics(picking)
            )
            datos_entrada = self._transaher_build_datos_entrada(
                picking=picking,
                gross_weight_kg=gross_weight_kg,
                total_vol_m3=total_vol_m3,
                packages_qty=packages_qty,
                consignee=shipper_partner,
                is_return=True,
            )
            ret_data = client.create_expedition(datos_entrada)
            ret_cod = str(ret_data["cod_expedicion"]).strip()

            raw_label = None
            ext = "pdf"
            mimetype = "application/pdf"
            if self.transaher_label_mode != "local_qweb":
                try:
                    lbl_res = client.get_labels(
                        [
                            {
                                "holding": ret_data.get(
                                    "holding", TRANSAHER_DEFAULT_HOLDING
                                ),
                                "seccion": ret_data.get(
                                    "seccion", TRANSAHER_DEFAULT_SECCION
                                ),
                                "centro": ret_data.get("centro")
                                or self.transaher_centro_cod,
                                "codigo": ret_cod,
                                "bultos": "-1",
                            }
                        ]
                    )
                    raw_label = base64.b64decode(lbl_res["data"])
                    ext = lbl_res.get("extension") or "pdf"
                    mimetype = lbl_res.get("content_type") or "application/pdf"
                except UserError:
                    if self.transaher_label_mode == "ws_only":
                        raise

            if not raw_label:
                raw_label = self._transaher_render_local_qweb_label(picking)

            attachment = self._transaher_attach_label_to_picking(
                picking=picking,
                raw_bytes=raw_label,
                tracking_ref=ret_cod,
                extension=ext,
                mimetype=mimetype,
                is_return=True,
            )
            picking.message_post(
                body=_("Transaher return expedition created (Expedition #%s).")
                % ret_cod,
                attachment_ids=[attachment.id] if attachment else [],
            )

    def transaher_fetch_labels(self, picking, bultos_filter="-1"):
        """Reprint or download PDF/ZPL labels for an existing expedition."""
        self.ensure_one()
        if not (picking.transaher_cod_expedicion or picking.carrier_tracking_ref):
            raise UserError(
                _("Picking %s does not have a Transaher expedition code yet.")
                % picking.name
            )
        raw_bytes, ext, mimetype, _warnings = self._transaher_download_or_render_label(
            picking=picking,
            bultos_override=bultos_filter,
            is_return=False,
        )
        attachment = self._transaher_attach_label_to_picking(
            picking=picking,
            raw_bytes=raw_bytes,
            tracking_ref=picking.transaher_cod_expedicion
            or picking.carrier_tracking_ref,
            extension=ext,
            mimetype=mimetype,
            is_return=False,
        )
        if attachment:
            picking.message_post(
                body=_("Transaher shipping label downloaded and attached to picking."),
                attachment_ids=[attachment.id],
            )
        return attachment

    def _transaher_format_tracking_history(self, exp, events, incidences):
        """Format event and incidence lists into `tracking_state_history`."""
        history_lines = []
        for ev in events:
            parts = [
                p
                for p in (
                    ev.get("situacion_dsc"),
                    ev.get("tipo_dsc"),
                    ev.get("causa_dsc"),
                    ev.get("desc_1"),
                )
                if p
            ]
            ev_dt = ev.get("date") or "N/A"
            ev_cod = ev.get("situacion_cod") or "-"
            history_lines.append(f"{ev_dt} - [{ev_cod}] {' - '.join(parts)}")

        inc_lines = []
        for inc in incidences:
            inc_parts = [
                p
                for p in (
                    inc.get("tipo_dsc"),
                    inc.get("causa_dsc"),
                    inc.get("desc_1"),
                    inc.get("desc_2"),
                )
                if p
            ]
            inc_lines.append(f"{inc.get('date') or 'N/A'} - {' - '.join(inc_parts)}")

        full_history = (
            "\n".join(history_lines) if history_lines else (exp.get("situacion") or "")
        )
        if inc_lines:
            inc_header = _("Incidences")
            full_history = (
                f"{full_history}\n--- {inc_header} ---\n" + "\n".join(inc_lines)
                if full_history
                else "\n".join(inc_lines)
            )
        return full_history, inc_lines

    @staticmethod
    def _transaher_audit_tracking_amounts(picking, amounts, vals):
        """Populate invoiced freight cost audit fields from `<Importes>`."""
        if not amounts:
            return
        total_invoiced = sum(a.get("importe_neto", 0.0) for a in amounts)
        if total_invoiced <= 0.0:
            return
        inv_numbers = [
            "-".join(
                filter(
                    None,
                    [
                        a.get("factura_centro"),
                        a.get("factura_serie"),
                        a.get("factura_numero"),
                    ],
                )
            )
            for a in amounts
            if a.get("factura_numero")
        ]
        vals["transaher_invoiced_cost"] = round(total_invoiced, 2)
        if inv_numbers:
            vals["transaher_invoice_number"] = inv_numbers[0]
        amt_lines = [
            (
                f"• [{a.get('concepto_cod') or '-'}] "
                f"{a.get('concepto_dsc') or a.get('baremo_dsc') or 'Concept'}: "
                f"{a.get('importe_neto', 0.0):.2f} {a.get('divisa') or 'EUR'} "
                f"({a.get('situacion') or ''})"
            )
            for a in amounts
        ]
        base_breakdown = (
            (picking.transaher_cost_breakdown or "")
            .split("\n--- Transaher wsInformacionTransporte Importes ---")[0]
            .strip()
        )
        vals["transaher_cost_breakdown"] = (
            (f"{base_breakdown}\n" if base_breakdown else "")
            + "--- Transaher wsInformacionTransporte Importes ---\n"
            + "\n".join(amt_lines)
        ).strip()

    def transaher_tracking_state_update(self, picking):
        """Standard OCA `delivery_state` hook called by `tracking_state_update()`
        and by `delivery_state`'s cron `StockPicking._update_delivery_state()`.
        Queries `wsInformacionTransporte` for live status, events, incidences,
        package SSCCs, and invoiced freight amounts (`sdtImportes`).
        """
        self.ensure_one()
        exp_num = (
            picking.transaher_cod_expedicion
            or (picking.carrier_tracking_ref or "").split(",")[0].strip()
        )
        if not exp_num:
            return

        client = self._transaher_get_client()
        info = client.get_tracking_info(
            holding=picking.transaher_holding,
            seccion=picking.transaher_seccion or self.transaher_seccion,
            centro=picking.transaher_centro or self.transaher_centro_cod,
            numero_expedicion=exp_num,
        )
        expediciones = info.get("expediciones") or []
        if not expediciones:
            return

        exp = expediciones[0]
        events = exp.get("events") or []
        incidences = exp.get("incidences") or []
        packages_info = exp.get("packages") or []
        amounts = exp.get("amounts") or []

        latest_event = events[-1] if events else {}
        latest_code = (
            latest_event.get("situacion_cod") or latest_event.get("tipo_cod") or ""
        )
        latest_desc = (
            latest_event.get("situacion_dsc")
            or latest_event.get("tipo_dsc")
            or latest_event.get("desc_1")
            or exp.get("situacion")
            or ""
        )
        latest_date = (
            latest_event.get("date")
            or exp.get("fh_tres")
            or exp.get("fh_dos")
            or exp.get("fh_uno")
            or ""
        )

        full_history, inc_lines = self._transaher_format_tracking_history(
            exp, events, incidences
        )
        is_return = bool(
            picking.picking_type_id and picking.picking_type_id.code == "incoming"
        )
        mapped_delivery_state = map_transaher_status_to_delivery_state(
            situacion=exp.get("situacion"),
            description=latest_desc,
            has_incidence=bool(incidences),
            is_return=is_return,
        )
        tracking_state_text = (
            f"[{latest_code}] {latest_desc}"
            if latest_code and latest_desc
            else (latest_desc or exp.get("situacion") or latest_code or False)
        )

        # Sync SSCC / EAN on physical Odoo packages if returned
        phys_packages = picking.move_line_ids.mapped("result_package_id")
        for idx, pkg in enumerate(phys_packages):
            if idx < len(packages_info):
                sscc_or_ean = packages_info[idx].get("sscc") or packages_info[idx].get(
                    "ean"
                )
                if sscc_or_ean:
                    pkg.transaher_sscc = sscc_or_ean

        vals = {
            "delivery_state": mapped_delivery_state,
            "tracking_state": tracking_state_text,
            "tracking_state_history": full_history or False,
            "tracking_json": info,
            "transaher_has_incidence": bool(incidences),
            "transaher_incidence_text": "\n".join(inc_lines) if inc_lines else False,
            "transaher_driver_info": exp.get("chofer_dsc") or False,
        }
        if (
            mapped_delivery_state in ("customer_delivered", "warehouse_delivered")
            and not picking.date_delivered
        ):
            vals["date_delivered"] = (
                parse_transaher_datetime(latest_date) or fields.Datetime.now()
            )
        for src_key, dst_field in (
            ("centro_destino", "transaher_centro_destino"),
            ("area_dis_cod", "transaher_area_dis_cod"),
            ("area_dis_dsc", "transaher_area_dis_dsc"),
        ):
            if exp.get(src_key):
                vals[dst_field] = exp[src_key]

        self._transaher_audit_tracking_amounts(picking, amounts, vals)
        picking.write(vals)
        return exp
