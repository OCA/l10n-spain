# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models

from .misc import FISCAL_ACQUIRERS


class L10nEsAeatmod592LineAcquirer(models.Model):
    _description = "AEAT 592 Acquirer report"
    _name = "l10n.es.aeat.mod592.report.line.acquirer"
    _inherit = "l10n.es.aeat.mod592.report.line.mixin"

    concept = fields.Selection(
        selection=[
            ("1", _("(1) Intra-community acquisition")),
            ("2", _("(2) Shipping outside Spanish territory")),
            ("3", _("(3) Inadequacy or destruction")),
            (
                "4",
                _(
                    """(4) Return for destruction or reincorporation into the
                manufacturing process"""
                ),
            ),
        ],
        compute="_compute_concept",
        store=True,
    )
    fiscal_acquirer = fields.Selection(
        selection=FISCAL_ACQUIRERS,
        string="Fiscal reginme acquirer",
        compute="_compute_fiscal_acquirer",
        store=True,
    )
    entry_number = fields.Char(
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "l10n.es.aeat.mod592.report.line.acquirer"
        )
    )

    @api.depends("partner_id", "stock_move_id")
    def _compute_concept(self):
        for item in self:
            concept = ""
            doc_type = item.partner_id.plastic_document_type
            orig_loc_usage = item.stock_move_id.location_id.usage
            dest_loc_usage = item.stock_move_id.location_dest_id.usage
            dest_loc_scrap = item.stock_move_id.location_dest_id.scrap_location
            # Intracomunitary Acquisitions
            if orig_loc_usage == "supplier" and doc_type == "2":
                concept = "1"
            # Deduction by: Non Spanish Shipping
            elif dest_loc_usage == "customer" and doc_type != "1":
                concept = "2"
            # Deduction by: Scrap
            elif dest_loc_scrap:
                concept = "3"
            # Deduction by: Adquisition returns
            elif (
                dest_loc_usage == "supplier"
                and item.stock_move_id.origin_returned_move_id
            ):
                concept = "4"
            item.concept = concept

    @api.depends("product_id")
    def _compute_fiscal_acquirer(self):
        for item in self:
            item.fiscal_acquirer = item.product_id.plastic_tax_regime_acquirer

    @api.depends(
        "supplier_document_number",
        "supplier_social_reason",
        "fiscal_acquirer",
    )
    def _compute_error_text(self):
        res = super()._compute_error_text()
        for record in self:
            errors = []
            if record.concept != "3" and not record.supplier_social_reason:
                errors.append(_("Without supplier name"))
            if not record.fiscal_acquirer:
                errors.append(_("Without regime"))
            if record.concept != "3" and not record.supplier_document_number:
                errors.append(_("Without VAT"))
            record.error_text += ", ".join(errors)
        return res

    def _get_csv_report_info_mapped(self, data):
        info_mapped = {
            "Número de asiento": "entry_number",
            "Fecha Hecho Contabilizado": "date_done",
            "Concepto": "concept",
            "Clave Producto": "product_key",
            "Descripción Producto": "fiscal_acquirer",
            "Justificante": "proof",
            "Kilogramos": "kgs",
            "Kilogramos No Reciclados": "no_recycling_kgs",
            "Prov./Dest.: Tipo Documento": "supplier_document_type",
            "Prov./Dest.: Nº Documento": "supplier_document_number",
            "Prov./Dest.: Razón Social": "supplier_social_reason",
            "Observaciones": "entry_note",
        }
        res = {}
        for info_key in list(info_mapped.keys()):
            info_key_value = info_mapped[info_key]
            res[info_key] = (
                data[info_key_value] if data and info_key_value in data else ""
            )
        return res

    def _get_csv_report_info(self):
        self.ensure_one()
        data = super()._get_csv_report_info()
        data["concept"] = self.concept
        data["fiscal_acquirer"] = self.fiscal_acquirer
        return self._get_csv_report_info_mapped(data)
