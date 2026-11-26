# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.tools import html2plaintext

from .logista_master_data import (
    LOGISTA_DELIVERY_NOTE_ACTIONS,
    LOGISTA_FREIGHT_TYPES,
    LOGISTA_SECTOR_LABELS,
    LOGISTA_SERVICE_NAMES,
    LOGISTA_SERVICES,
    build_logista_barcode_34,
    format_logista_main_reference,
    sanitize_logista_phone,
)
from .logista_request import LogistaRequest


class StockPicking(models.Model):
    _inherit = "stock.picking"

    logista_service_id = fields.Selection(
        selection=LOGISTA_SERVICES,
        string="Logista Service Override",
        copy=False,
        help="Optional per-picking override of the Logista Parcel service.",
    )
    logista_freight_type = fields.Selection(
        selection=LOGISTA_FREIGHT_TYPES,
        copy=False,
        help="Optional per-picking override of FreightType (P = Pagados, D = Debidos).",
    )
    logista_arranged_delivery_date = fields.Date(
        string="Arranged Delivery Date",
        copy=False,
        help="Optional arranged delivery date (`ArrangedDeliveryDate`, yyyy-mm-dd).",
    )
    logista_delivery_note_action = fields.Selection(
        selection=LOGISTA_DELIVERY_NOTE_ACTIONS,
        string="Delivery Note Action",
        copy=False,
        help="Action on signed customer delivery note (`DeliveryNoteAction`).",
    )
    logista_tight_flow = fields.Boolean(
        string="Tight Flow Service (Flujo Tenso)",
        default=False,
        copy=False,
    )
    logista_cod_amount = fields.Float(
        string="Cash on Delivery (€)",
        copy=False,
        help="Cash on Delivery amount in EUR (`CashOnDelivery`).",
    )
    logista_insured_value = fields.Float(
        string="Declared Insurance Value (€)",
        copy=False,
        help="Declared insurance amount in EUR (`InsuranceValue`).",
    )
    logista_pallets_qty = fields.Integer(
        string="Pallets Count (Logista)",
        default=0,
        copy=False,
        help=(
            "Number of pallets when shipping pallets or mixed shipments without "
            "individual Odoo packages."
        ),
    )
    logista_loose_packages_qty = fields.Integer(
        string="Loose Parcels in Mixed Shipment",
        default=0,
        copy=False,
        help=(
            "Number of loose parcels (`MixPackages`) in a mixed pallet+parcel shipment."
        ),
    )
    logista_customer_reference = fields.Char(
        string="Logista Main Reference",
        size=9,
        copy=False,
        help="Optional explicit main customer reference (max 9 alphanumeric chars).",
    )
    logista_comments = fields.Char(
        string="Logista Delivery Comments",
        size=100,
        copy=False,
        help="Delivery comments printed on label and sent to API (max 100 chars).",
    )

    def logista_get_label(self):
        self.ensure_one()
        if self.delivery_type != "logista" or not self.carrier_tracking_ref:
            return False
        return self.carrier_id.logista_get_label(self)

    def _get_logista_label_items(self, is_return=False):
        """Build per-unit label dictionaries for QWeb PDF and ZPL label rendering,
        strictly complying with `Características de etiquetaje_v4_Logista Parcel.pdf`
        and the official `BULTOS` / `PALETS` label layouts.
        """
        self.ensure_one()
        carrier = self.carrier_id
        req = LogistaRequest(carrier)
        shipper = req._get_shipper_partner(self)
        if is_return:
            remitente = self.partner_id or shipper
            destinatario = shipper
        else:
            remitente = shipper
            destinatario = self.partner_id

        meta = (
            dict(self.tracking_json)
            if isinstance(self.tracking_json, dict) and not is_return
            else {}
        )
        metrics = req._prepare_package_metrics(self)
        service_id = req._resolve_service_id(picking=self)
        sector_code = carrier.logista_sector_code or "0"

        dest_country_iso = (destinatario.country_id.code or "ES").upper()
        orig_country_iso = (remitente.country_id.code or "ES").upper()

        delegacion_dest = meta.get("delegacion") or ""
        zona_reparto = meta.get("zona_reparto") or ""
        if not delegacion_dest and destinatario.zip:
            plaza = req.get_plaza_routing(
                dest_country_iso,
                destinatario.zip,
                service_id=service_id,
                sector_code=sector_code,
            )
            delegacion_dest = plaza.get("delegacion") or ""
            zona_reparto = plaza.get("zona_reparto") or ""
        if not delegacion_dest:
            delegacion_dest = (
                destinatario.state_id.name or destinatario.city or ""
            ).upper()

        main_ref = meta.get("main_reference")
        if not main_ref:
            if self.logista_customer_reference and not is_return:
                main_ref = format_logista_main_reference(
                    self.logista_customer_reference
                )
            elif is_return:
                doc_num = format_logista_main_reference(self.name)
                main_ref = f"R{doc_num[:8]}"
            else:
                main_ref = format_logista_main_reference(self.name)

        origin_deleg_code = carrier._logista_get_origin_delegation_code()
        cust_bc_code = carrier._logista_get_customer_barcode_code()
        stored_barcodes = meta.get("barcodes") or []

        rem_state = remitente.state_id.name.upper() if remitente.state_id else ""
        rem_country = remitente.country_id.name.upper() if remitente.country_id else ""
        rem_loc_extra = " - ".join(filter(None, [rem_state, rem_country]))
        rem_cp_city = f"{remitente.zip or ''} - {(remitente.city or '').upper()}"
        if rem_loc_extra:
            rem_cp_city = f"{rem_cp_city} ({rem_loc_extra})"

        dest_commercial = destinatario.commercial_partner_id or destinatario
        dest_name = (dest_commercial.name or destinatario.name or "").upper()[:45]
        dest_street = (destinatario.street or "").upper()[:50]
        dest_dept_parts = []
        if destinatario.street2:
            dest_dept_parts.append(destinatario.street2.upper())
        if (
            destinatario != dest_commercial
            and destinatario.name
            and destinatario.name != dest_commercial.name
        ):
            dest_dept_parts.append(destinatario.name.upper())
        dest_dept = " - ".join(dest_dept_parts)[:50]
        dest_cp_city = (
            f"{destinatario.zip or ''} - {(destinatario.city or '').upper()}"
        )[:34]
        dest_tel = sanitize_logista_phone(destinatario.phone or destinatario.mobile)
        dest_state_country = " - ".join(
            filter(
                None,
                [
                    destinatario.state_id.name.upper() if destinatario.state_id else "",
                    destinatario.country_id.name.upper()
                    if destinatario.country_id
                    else "",
                ],
            )
        )
        dest_country_tel = (
            f"{dest_state_country}   Tel.{dest_tel}" if dest_tel else dest_state_country
        )

        freight_code = req._resolve_freight_type(partner=destinatario, picking=self)
        freight_label = "P.PAGADOS" if freight_code == "P" else "P.DEBIDOS"

        raw_obs = self.logista_comments or (
            html2plaintext(self.note).strip() if self.note else ""
        )
        raw_obs_clean = " ".join(raw_obs.split()).upper()
        obs_1 = raw_obs_clean[:50]
        obs_2 = raw_obs_clean[50:100].strip()

        now_dt = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        printed_at = now_dt.strftime("%d/%m/%Y %H:%M")
        rem_city = (remitente.city or "").upper()
        origin_header = (
            carrier.logista_origin_delegation_name
            or f"{orig_country_iso} {origin_deleg_code} {rem_city}"
        ).strip()

        shipment_id = str(
            meta.get("shipment_id") or self.carrier_tracking_ref or ""
        ).strip()
        control_total = metrics["control_packages"]
        unit_kinds = metrics["unit_kinds"]

        items = []
        for idx in range(1, control_total + 1):
            barcode = (
                stored_barcodes[idx - 1]
                if idx - 1 < len(stored_barcodes)
                else build_logista_barcode_34(
                    sector_code=sector_code,
                    service_id=service_id,
                    postal_code=destinatario.zip or "00000",
                    origin_delegation_code=origin_deleg_code,
                    customer_code=cust_bc_code,
                    reference=main_ref,
                    package_index=idx,
                    dest_country_code=dest_country_iso,
                    origin_country_code=orig_country_iso,
                )
            )
            kind = unit_kinds[idx - 1] if idx - 1 < len(unit_kinds) else "parcel"
            items.append(
                {
                    "unit_index": idx,
                    "control_packages": control_total,
                    "packages": metrics["packages"],
                    "is_pallet": kind == "pallet",
                    "weight_kg": metrics["weight_kg"],
                    "barcode": barcode,
                    "shipment_id": shipment_id,
                    "main_reference": main_ref,
                    "service_name": LOGISTA_SERVICE_NAMES.get(service_id, "AMBIPAQ"),
                    "sector_label": LOGISTA_SECTOR_LABELS.get(sector_code, "GENÉRICO"),
                    "freight_label": freight_label,
                    "delegacion_destino": delegacion_dest,
                    "zona_reparto": zona_reparto,
                    "origin_header": origin_header,
                    "printed_at": printed_at,
                    "remitente_name": (remitente.name or "").upper()[:45],
                    "remitente_street": " ".join(
                        filter(None, [remitente.street, remitente.street2])
                    ).upper()[:55],
                    "remitente_cp_city": rem_cp_city[:65],
                    "consignatario_name": dest_name,
                    "consignatario_street": dest_street,
                    "consignatario_dept": dest_dept,
                    "consignatario_cp_city": dest_cp_city,
                    "consignatario_country_tel": dest_country_tel[:55],
                    "obs_1": obs_1,
                    "obs_2": obs_2,
                }
            )
        return items
