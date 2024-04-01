# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models

from .misc import FISCAL_MANUFACTURERS


class L10nEsAeatmod592LineManufacturer(models.Model):
    _description = "AEAT 592 Manufacturer report"
    _name = "l10n.es.aeat.mod592.report.line.manufacturer"
    _inherit = "l10n.es.aeat.mod592.report.line.mixin"

    concept = fields.Selection(
        selection=[
            ("1", _("(1) Initial existence")),
            ("2", _("(2) Manufacturing")),
            (
                "3",
                _(
                    """(3) Return of products for destruction or reincorporation into the
                manufacturing process"""
                ),
            ),
            ("4", _("(4) Delivery or making available of the products accounted for")),
            (
                "5",
                _(
                    """(5) Other cancellations of the products accounted for other than
                their delivery or availability"""
                ),
            ),
        ],
        compute="_compute_concept",
        store=True,
    )
    product_description = fields.Char(
        string="Product description", compute="_compute_product_description"
    )
    fiscal_manufacturer = fields.Selection(
        selection=FISCAL_MANUFACTURERS,
        string="Fiscal regime manufacturer",
        compute="_compute_fiscal_manufacturer",
        store=True,
    )
    entry_number = fields.Char(
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "l10n.es.aeat.mod592.report.line.manufacturer"
        )
    )

    @api.depends("partner_id", "stock_move_id")
    def _compute_concept(self):
        for item in self:
            concept = ""
            doc_type = item.partner_id.plastic_document_type
            dest_loc_usage = item.stock_move_id.location_dest_id.usage
            dest_loc_scrap = item.stock_move_id.location_dest_id.scrap_location
            # Initial Existence
            if dest_loc_usage == "internal":
                concept = "1"
            # Manufacturer
            elif dest_loc_usage == "production":
                concept = "2"
            # Initial Existence
            elif dest_loc_usage == "production" and dest_loc_scrap:
                concept = "3"
            # Sales to spanish customers
            elif dest_loc_usage == "customer" and doc_type == "1":
                concept = "4"
            # Scrap
            elif dest_loc_scrap:
                concept = "5"
            item.concept = concept

    @api.depends("product_id")
    def _compute_product_description(self):
        for item in self:
            item.product_description = item.product_id.name

    @api.depends("product_id")
    def _compute_fiscal_manufacturer(self):
        for item in self:
            item.fiscal_manufacturer = item.product_id.plastic_tax_regime_manufacturer

    @api.depends(
        "supplier_document_number",
        "supplier_social_reason",
        "fiscal_manufacturer",
        "supplier_document_type",
        "supplier_document_number",
    )
    def _compute_error_text(self):
        res = super()._compute_error_text()
        for record in self:
            errors = []
            if not record.supplier_social_reason:
                errors.append(_("Without supplier name"))
            if not record.fiscal_manufacturer:
                errors.append(_("Without regime"))
            if not record.supplier_document_type:
                errors.append(_("Without supplier document"))
            if not record.supplier_document_number:
                errors.append(_("Without document number"))
            record.error_text += ", ".join(errors)
        return res

    def _get_csv_report_info_mapped(self, data):
        info_mapped = {
            "Número de asiento": "entry_number",
            "Fecha Hecho Contabilizado": "date_done",
            "Concepto": "concept",
            "Clave Producto": "product_key",
            "Descripción Producto": "product_description",
            "Régimen Fiscal": "fiscal_manufacturer",
            "Justificante": "proof",
            "Prov./Dest.: Tipo Documento": "supplier_document_type",
            "Prov./Dest.: Nº Documento": "supplier_document_number",
            "Prov./Dest.: Razón Social": "supplier_social_reason",
            "Kilogramos": "kgs",
            "Kilogramos No Reciclados": "no_recycling_kgs",
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
        data["product_description"] = self.product_description
        data["fiscal_manufacturer"] = self.fiscal_manufacturer
        return self._get_csv_report_info_mapped(data)
