# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TransaherManifestWizard(models.TransientModel):
    _name = "transaher.manifest.wizard"
    _description = "Transaher Daily Manifest (awsmnfprtsoap) Wizard"

    @api.model
    def _default_date_from(self):
        today = fields.Date.context_today(self)
        return datetime.combine(today, time(0, 0, 0))

    @api.model
    def _default_date_to(self):
        today = fields.Date.context_today(self)
        return datetime.combine(today, time(23, 59, 0))

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Transaher Delivery Method",
        required=True,
        domain="[('delivery_type', '=', 'transaher')]",
    )
    date_from = fields.Datetime(
        required=True,
        default=_default_date_from,
        help="Start date/time sent to awsmnfprtsoap in aaaammddhhmm format.",
    )
    date_to = fields.Datetime(
        required=True,
        default=_default_date_to,
        help="End date/time sent to awsmnfprtsoap in aaaammddhhmm format.",
    )
    source_mode = fields.Selection(
        selection=[
            (
                "ws_with_fallback",
                "Transaher Web Service (awsmnfprtsoap) + Local Fallback",
            ),
            ("ws_only", "Transaher Web Service Only (awsmnfprtsoap)"),
            ("local_pickings", "Local Odoo Pickings Only"),
        ],
        string="Manifest Data Source",
        default="ws_with_fallback",
        required=True,
    )
    pdf_file = fields.Binary(
        string="Manifest PDF",
        readonly=True,
    )
    pdf_filename = fields.Char(
        string="File Name",
        readonly=True,
    )

    def _format_fch_aaaammddhhmm(self, dt_val):
        local_dt = fields.Datetime.context_timestamp(self, dt_val)
        return local_dt.strftime("%Y%m%d%H%M")

    def _get_local_pickings_manifest_rows(self):
        pickings = self.env["stock.picking"].search(
            [
                ("carrier_id", "=", self.carrier_id.id),
                ("carrier_tracking_ref", "!=", False),
                ("state", "=", "done"),
                ("date_done", ">=", self.date_from),
                ("date_done", "<=", self.date_to),
            ],
            order="date_done asc, id asc",
        )
        rows = []
        for picking in pickings:
            gross_w, _vol, pkgs = self.carrier_id._transaher_prepare_picking_metrics(
                picking
            )
            partner = picking.partner_id
            rows.append(
                {
                    "cod_expedicion": picking.transaher_cod_expedicion
                    or picking.carrier_tracking_ref,
                    "centro": picking.transaher_centro
                    or self.carrier_id.transaher_centro_cod
                    or "",
                    "albaran_ordenante": picking.name,
                    "nombre_destinatario": partner.name or "",
                    "domicilio_destinatario": " ".join(
                        filter(None, [partner.street, partner.street2])
                    ),
                    "postal_destinatario": partner.zip or "",
                    "poblacion_destinatario": partner.city or "",
                    "servicio": picking.transaher_servicio or "",
                    "bultos": pkgs,
                    "peso": round(gross_w, 2),
                }
            )
        return rows

    def _collect_manifest_rows(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("'Date From' cannot be later than 'Date To'."))

        fch_desde = self._format_fch_aaaammddhhmm(self.date_from)
        fch_hasta = self._format_fch_aaaammddhhmm(self.date_to)

        rows = []
        if self.source_mode in ("ws_with_fallback", "ws_only"):
            client = self.carrier_id._transaher_get_client()
            try:
                rows = client.get_manifest_data(
                    fch_desde=fch_desde, fch_hasta=fch_hasta
                )
            except UserError:
                if self.source_mode == "ws_only":
                    raise
                rows = self._get_local_pickings_manifest_rows()
            if not rows and self.source_mode == "ws_with_fallback":
                rows = self._get_local_pickings_manifest_rows()
        else:
            rows = self._get_local_pickings_manifest_rows()

        if not rows:
            raise UserError(
                _("No Transaher expeditions were found between %(d1)s and %(d2)s.")
                % {
                    "d1": fields.Datetime.to_string(self.date_from),
                    "d2": fields.Datetime.to_string(self.date_to),
                }
            )
        return rows, fch_desde, fch_hasta

    def _prepare_report_data(self):
        rows, fch_desde, fch_hasta = self._collect_manifest_rows()
        company = self.carrier_id.company_id or self.env.company
        return {
            "wizard_id": self.id,
            "carrier_name": self.carrier_id.name,
            "company_name": company.name,
            "company_vat": company.vat or "",
            "fch_desde": fch_desde,
            "fch_hasta": fch_hasta,
            "date_from_display": fields.Datetime.context_timestamp(
                self, self.date_from
            ).strftime("%d/%m/%Y %H:%M"),
            "date_to_display": fields.Datetime.context_timestamp(
                self, self.date_to
            ).strftime("%d/%m/%Y %H:%M"),
            "printed_at": fields.Datetime.context_timestamp(
                self, fields.Datetime.now()
            ).strftime("%d/%m/%Y %H:%M"),
            "expeditions": rows,
            "total_expeditions": len(rows),
            "total_bultos": sum(int(r.get("bultos") or 0) for r in rows),
            "total_peso": round(sum(float(r.get("peso") or 0.0) for r in rows), 2),
        }

    def action_generate_manifest_pdf(self):
        """Query `awsmnfprtsoap`, render the PDF manifest, and store on wizard."""
        self.ensure_one()
        report_data = self._prepare_report_data()
        report = self.env.ref("delivery_transaher.action_report_transaher_manifest")
        pdf_bytes, _ext = report._render_qweb_pdf(
            report.report_name, res_ids=self.ids, data=report_data
        )
        date_tag = report_data["fch_desde"][:8]
        filename = f"Transaher_Manifest_{date_tag}.pdf"
        self.write(
            {
                "pdf_file": base64.b64encode(pdf_bytes),
                "pdf_filename": filename,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "transaher.manifest.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_print_manifest(self):
        """Directly print/download the PDF Manifest via Odoo's report action."""
        self.ensure_one()
        report_data = self._prepare_report_data()
        return self.env.ref(
            "delivery_transaher.action_report_transaher_manifest"
        ).report_action(self, data=report_data, config=False)
