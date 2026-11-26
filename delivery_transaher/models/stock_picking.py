# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .transaher_master_data import (
    TRANSAHER_DEFAULT_HOLDING,
    TRANSAHER_DEFAULT_SECCION,
    TRANSAHER_PORTES_TYPES,
    build_transaher_barcode_24,
)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_transaher_carrier = fields.Boolean(
        compute="_compute_is_transaher_carrier",
        store=True,
    )

    # =========================================================================
    # TRANSAHER COMPOSITE EXPEDITION KEY & ROUTING METADATA (SECTION 3.3)
    # Note: Package count (`number_of_packages`), volume (`volume`), and shipment
    # tracking state (`delivery_state`, `tracking_state`, `tracking_state_history`,
    # `tracking_json`, `date_shipped`, `date_delivered`) are provided natively by
    # OCA `delivery_package_number`, `stock_picking_volume`, and `delivery_state`.
    # =========================================================================
    transaher_holding = fields.Integer(
        default=TRANSAHER_DEFAULT_HOLDING,
        copy=False,
    )
    transaher_seccion = fields.Integer(
        string="Transaher Section",
        default=TRANSAHER_DEFAULT_SECCION,
        copy=False,
    )
    transaher_centro = fields.Integer(
        string="Transaher Origin Center",
        copy=False,
        help="Center code returned by awsprcsatsoap (e.g. 461 Valencia, 81 Barcelona).",
    )
    transaher_cod_expedicion = fields.Char(
        string="Transaher Expedition Code",
        copy=False,
        index=True,
        help="Official CodExpedicion returned by Transaher Alta (awsprcsatsoap).",
    )
    transaher_expedition_key = fields.Char(
        string="Transaher Full Key (H.S.C.Exp)",
        compute="_compute_transaher_expedition_key",
        store=True,
        copy=False,
        help=(
            "Composite expedition key Holding.Seccion.Centro.CodExpedicion "
            "used by wsEtiExpSOAP and awsExpBaja."
        ),
    )
    transaher_fecha_expedicion = fields.Char(
        string="Expedition Date (Transaher)",
        copy=False,
    )
    transaher_servicio = fields.Char(
        string="Transaher Service",
        copy=False,
    )
    transaher_area_dis_cod = fields.Char(
        string="Distribution Area Code",
        copy=False,
    )
    transaher_area_dis_dsc = fields.Char(
        string="Distribution Area Description",
        copy=False,
    )
    transaher_centro_destino = fields.Char(
        string="Destination Center",
        copy=False,
    )
    transaher_expedicion_ch = fields.Char(
        string="Channel / External Expedition Ref",
        copy=False,
    )
    transaher_barcodes = fields.Char(
        string="24-Digit Package Barcodes",
        copy=False,
        help=(
            "24-character Code 128 / Interleaved 2 of 5 barcodes generated "
            "per package (Section 5.2)."
        ),
    )
    transaher_tracking_url = fields.Char(
        string="Transaher Tracking Link",
        compute="_compute_transaher_tracking_url",
    )

    # =========================================================================
    # PER-PICKING OPERATIONAL OVERRIDES FOR DATOSENTRADA (SECTION 3.2)
    # =========================================================================
    transaher_package_type_id = fields.Many2one(
        comodel_name="stock.package.type",
        string="Transaher Packaging Type",
        domain="[('package_carrier_type', '=', 'transaher')]",
        copy=False,
    )
    transaher_portes = fields.Selection(
        selection=TRANSAHER_PORTES_TYPES,
        string="Freight Terms (Tipo de Portes)",
        copy=False,
        help=(
            "Field 8 of Datosentrada: 1 = Freight Prepaid (Pagados), "
            "2 = Freight Collect (Debidos)."
        ),
    )
    transaher_postal_rep_code = fields.Char(
        string="Postal Repetition Code",
        size=5,
        copy=False,
        help="Field 5 of Datosentrada: Correos postal repetition code (optional).",
    )
    transaher_obs_1 = fields.Char(
        string="Observations Line 1",
        size=70,
        copy=False,
        help=(
            "Field 9 of Datosentrada: delivery observations line 1 "
            "(max. 70 characters)."
        ),
    )
    transaher_obs_2 = fields.Char(
        string="Observations Line 2",
        size=70,
        copy=False,
        help=(
            "Field 10 of Datosentrada: delivery observations line 2 "
            "(max. 70 characters)."
        ),
    )
    transaher_insured_value = fields.Float(
        string="Insured Value (€)",
        digits="Product Price",
        copy=False,
        help="Field 14 of Datosentrada: cargo insured value (format 123456,123).",
    )
    transaher_cod_amount = fields.Float(
        string="Cash on Delivery / COD (€)",
        digits="Product Price",
        copy=False,
        help=(
            "Field 15 of Datosentrada: Contra reembolso amount to collect "
            "on delivery (format 123456,123)."
        ),
    )

    # =========================================================================
    # TARIFF CONTROL & INVOICED FREIGHT COST AUDIT
    # =========================================================================
    transaher_chargeable_weight = fields.Float(
        string="Transaher Chargeable Weight (kg)",
        copy=False,
    )
    transaher_estimated_cost = fields.Float(
        string="Estimated Transaher Cost (€)",
        digits="Product Price",
        copy=False,
    )
    transaher_invoiced_cost = fields.Float(
        string="Invoiced Transaher Cost (€)",
        digits="Product Price",
        copy=False,
        help=(
            "Net freight amount reported by Transaher wsInformacionTransporte "
            "(<Importes>)."
        ),
    )
    transaher_cost_difference = fields.Float(
        string="Cost Deviation (€)",
        digits="Product Price",
        compute="_compute_transaher_cost_difference",
        store=True,
    )
    transaher_invoice_number = fields.Char(
        copy=False,
    )
    transaher_cost_breakdown = fields.Text(
        string="Transaher Tariff / Cost Breakdown",
        copy=False,
    )

    # =========================================================================
    # TRANSAHER DRIVER & INCIDENCE DETAILS (SECTION 7 - wsInformacionTransporte)
    # =========================================================================
    transaher_driver_info = fields.Char(
        string="Assigned Driver",
        copy=False,
    )
    transaher_has_incidence = fields.Boolean(
        string="Has Active Incidence",
        default=False,
        copy=False,
    )
    transaher_incidence_text = fields.Text(
        string="Transaher Incidences",
        copy=False,
    )

    # =========================================================================
    # COMPUTE & ONCHANGE METHODS
    # =========================================================================
    @api.depends("carrier_id", "carrier_id.delivery_type")
    def _compute_is_transaher_carrier(self):
        for picking in self:
            picking.is_transaher_carrier = bool(
                picking.carrier_id and picking.carrier_id.delivery_type == "transaher"
            )

    @api.depends(
        "transaher_holding",
        "transaher_seccion",
        "transaher_centro",
        "transaher_cod_expedicion",
    )
    def _compute_transaher_expedition_key(self):
        for picking in self:
            if picking.transaher_cod_expedicion:
                h = picking.transaher_holding or 0
                s = picking.transaher_seccion or 10
                c = picking.transaher_centro or 0
                picking.transaher_expedition_key = (
                    f"{h}.{s}.{c}.{picking.transaher_cod_expedicion}"
                )
            else:
                picking.transaher_expedition_key = False

    @api.depends("transaher_estimated_cost", "transaher_invoiced_cost")
    def _compute_transaher_cost_difference(self):
        for picking in self:
            if picking.transaher_invoiced_cost:
                picking.transaher_cost_difference = picking.transaher_invoiced_cost - (
                    picking.transaher_estimated_cost or 0.0
                )
            else:
                picking.transaher_cost_difference = 0.0

    @api.depends("carrier_id", "carrier_tracking_ref", "transaher_cod_expedicion")
    def _compute_transaher_tracking_url(self):
        for picking in self:
            if (
                picking.carrier_id
                and picking.carrier_id.delivery_type == "transaher"
                and (picking.carrier_tracking_ref or picking.transaher_cod_expedicion)
            ):
                picking.transaher_tracking_url = (
                    picking.carrier_id.transaher_get_tracking_link(picking)
                )
            else:
                picking.transaher_tracking_url = False

    @api.onchange("partner_id", "carrier_id")
    def _onchange_partner_transaher_defaults(self):
        for picking in self:
            if (
                picking.carrier_id
                and picking.carrier_id.delivery_type == "transaher"
                and picking.partner_id
            ):
                picking.transaher_portes = (
                    picking.carrier_id._transaher_resolve_portes_code(
                        partner=picking.partner_id, picking=picking
                    )
                )
                if picking.partner_id.transaher_postal_rep_code:
                    picking.transaher_postal_rep_code = (
                        picking.partner_id.transaher_postal_rep_code
                    )
                if (
                    picking.partner_id.transaher_delivery_notes
                    and not picking.transaher_obs_1
                ):
                    obs1, obs2 = picking.carrier_id._transaher_split_observations(
                        fallback_text=picking.partner_id.transaher_delivery_notes
                    )
                    picking.transaher_obs_1 = obs1
                    picking.transaher_obs_2 = obs2

    # =========================================================================
    # ACTION BUTTONS ON PICKING
    # =========================================================================
    def _ensure_transaher_carrier(self):
        self.ensure_one()
        if not self.carrier_id or self.carrier_id.delivery_type != "transaher":
            raise UserError(
                _("Picking %s does not have a Transaher delivery method assigned.")
                % self.name
            )
        return self.carrier_id

    def action_transaher_get_label(self):
        """Download or reprint all package labels (`<Bultos>-1</Bultos>`)."""
        for picking in self:
            carrier = picking._ensure_transaher_carrier()
            carrier.transaher_fetch_labels(picking, bultos_filter="-1")
        return True

    def action_transaher_print_local_label(self):
        """Print the standard Transaher QWeb PDF label with 24-digit barcodes."""
        self.ensure_one()
        self._ensure_transaher_carrier()
        return self.env.ref(
            "delivery_transaher.action_report_transaher_label"
        ).report_action(self, config=False)

    def action_transaher_calculate_rate(self):
        """Calculate or recalculate estimated shipping cost on the picking."""
        for picking in self:
            carrier = picking._ensure_transaher_carrier()
            partner = picking.partner_id
            if not partner or not partner.country_id or not partner.zip:
                raise UserError(
                    _(
                        "The picking consignee must have a Postal Code and Country "
                        "to calculate the Transaher rate."
                    )
                )
            gross_weight_kg, total_vol_m3, packages_qty = (
                carrier._transaher_prepare_picking_metrics(picking)
            )
            chargeable_weight_kg = carrier._transaher_compute_chargeable_weight(
                gross_weight_kg=gross_weight_kg,
                volume_m3=total_vol_m3,
            )
            table_cost, table_breakdown, _rule = (
                carrier._transaher_rate_from_tariff_table(
                    partner=partner,
                    chargeable_weight_kg=chargeable_weight_kg,
                    packages_qty=packages_qty,
                    cod_amount=picking.transaher_cod_amount,
                    insured_value=carrier._transaher_resolve_insured_value(
                        picking=picking
                    ),
                )
            )
            if table_cost is None:
                raise UserError(
                    _(
                        "No applicable Transaher tariff found for %(partner)s "
                        "(ZIP %(zip)s, %(weight).2f chargeable kg, %(pkgs)d packages)."
                    )
                    % {
                        "partner": partner.display_name,
                        "zip": partner.zip,
                        "weight": chargeable_weight_kg,
                        "pkgs": packages_qty,
                    }
                )
            summary_line = _(
                "Gross weight: %(gross).2f kg | Vol: %(vol).3f m³ | "
                "Chargeable weight: %(chg).2f kg | Packages: %(pkgs)d"
            ) % {
                "gross": gross_weight_kg,
                "vol": total_vol_m3,
                "chg": chargeable_weight_kg,
                "pkgs": packages_qty,
            }
            picking.write(
                {
                    "transaher_estimated_cost": table_cost,
                    "transaher_chargeable_weight": chargeable_weight_kg,
                    "transaher_cost_breakdown": f"{table_breakdown}\n{summary_line}",
                }
            )
        return True

    def action_open_transaher_tracking_url(self):
        self.ensure_one()
        if not self.transaher_tracking_url:
            raise UserError(
                _("This picking does not have a Transaher tracking link yet.")
            )
        return {
            "type": "ir.actions.act_url",
            "url": self.transaher_tracking_url,
            "target": "new",
        }

    def _get_transaher_label_items(self):
        """Return per-package dicts for the QWeb Transaher label report."""
        self.ensure_one()
        carrier = self.carrier_id
        partner = self.partner_id
        shipper = (
            self.picking_type_id.warehouse_id.partner_id
            or self.company_id.partner_id
            or self.env.company.partner_id
        )
        gross_weight_kg, _vol, packages_qty = (
            carrier._transaher_prepare_picking_metrics(self)
        )
        centro = self.transaher_centro or carrier.transaher_centro_cod or 0
        cod_exp = self.transaher_cod_expedicion or self.carrier_tracking_ref or "0"
        country_iso = (partner.country_id.code or "ES").upper()

        existing_barcodes = [
            b.strip() for b in (self.transaher_barcodes or "").split(",") if b.strip()
        ]
        portes_code = carrier._transaher_resolve_portes_code(
            partner=partner, picking=self
        )
        portes_label = _("PAGADOS") if portes_code == "1" else _("DEBIDOS")
        obs_text = " / ".join(
            filter(None, [self.transaher_obs_1, self.transaher_obs_2])
        )
        exp_date = self.transaher_fecha_expedicion or fields.Date.to_string(
            self.scheduled_date.date()
            if self.scheduled_date
            else fields.Date.context_today(self)
        )
        order_ref = (
            (
                self.sale_id.client_order_ref
                if self.sale_id and self.sale_id.client_order_ref
                else ""
            )
            or self.origin
            or self.name
        )

        items = []
        for idx in range(1, packages_qty + 1):
            barcode = (
                existing_barcodes[idx - 1]
                if idx - 1 < len(existing_barcodes)
                else build_transaher_barcode_24(
                    centro_origen=centro,
                    cod_expedicion=cod_exp,
                    bulto_num=idx,
                    postal_code=partner.zip or "00000",
                    country_code=country_iso,
                )
            )
            items.append(
                {
                    "origin_label": carrier.transaher_centro_label
                    or f"{centro} TRANSAHER",
                    "fecha": exp_date,
                    "bulto_index": idx,
                    "bultos_total": packages_qty,
                    "peso_total": f"{gross_weight_kg:.3f}",
                    "remitente_name": (shipper.name or "")[:45],
                    "observaciones": obs_text,
                    "pedido": (order_ref or "")[:20],
                    "referencia": (self.name or "")[:20],
                    "portes_label": portes_label,
                    "cod_expedicion": cod_exp,
                    "consignatario_name": (partner.name or "")[:40],
                    "consignatario_street": " ".join(
                        filter(None, [partner.street, partner.street2])
                    )[:50],
                    "consignatario_cp_city": (
                        f"{partner.zip or ''} - {partner.city or ''}"
                    ),
                    "consignatario_country": (partner.country_id.name or "").upper(),
                    "area_dis_cod": self.transaher_area_dis_cod or "0",
                    "area_dis_dsc": self.transaher_area_dis_dsc or "",
                    "centro_destino": self.transaher_centro_destino
                    or (partner.country_id.name or ""),
                    "barcode": barcode,
                }
            )
        return items
