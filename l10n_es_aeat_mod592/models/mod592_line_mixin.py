# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.tools import float_is_zero

from .misc import DOCUMENT_TYPES, PRODUCT_KEYS


class L10nEsAeatmod592LineMixin(models.AbstractModel):
    _name = "l10n.es.aeat.mod592.report.line.mixin"
    _description = "AEAT 592 report line Mixin"
    _rec_name = "entry_number"

    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod592.report", string="Mod592 Report"
    )
    sequence = fields.Integer(default=1)
    entry_number = fields.Char(string="Entrie number")
    product_key = fields.Selection(
        selection=PRODUCT_KEYS,
        compute="_compute_product_key",
        store=True,
    )
    date_done = fields.Date(string="Date", compute="_compute_date_done", store=True)
    proof = fields.Char(
        string="Supporting document", compute="_compute_proof", store=True
    )
    supplier_document_type = fields.Selection(
        selection=DOCUMENT_TYPES,
        string="Supplier document type",
        compute="_compute_supplier_document_type",
        store=True,
    )
    supplier_document_number = fields.Char(
        string="Supplier document number",
        compute="_compute_supplier_document_number",
        store=True,
    )
    supplier_social_reason = fields.Char(
        string="Supplier name", compute="_compute_supplier_social_reason", store=True
    )
    kgs = fields.Float(
        string="Weight",
        digits="Stock Weight",
        compute="_compute_kgs",
        store=True,
    )
    no_recycling_kgs = fields.Float(
        string="Weight non reclycable",
        digits="Stock Weight",
        compute="_compute_no_recycling_kgs",
        store=True,
    )
    entry_note = fields.Text(string="Entries observation")
    stock_move_id = fields.Many2one(
        comodel_name="stock.move", string="Stock Move", required=True
    )
    product_id = fields.Many2one(
        comodel_name="product.product", related="stock_move_id.product_id"
    )
    product_description = fields.Char(
        string="Product description", compute="_compute_product_description"
    )
    product_uom_qty = fields.Float(
        compute="_compute_product_uom_qty",
        store=True,
        digits="Product Unit of Measure",
    )
    picking_id = fields.Many2one(
        comodel_name="stock.picking", related="stock_move_id.picking_id"
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_partner_id",
        store=True,
    )
    entries_ok = fields.Boolean(
        compute="_compute_entries_ok",
        string="Entries OK",
        help="Checked if record is OK",
    )
    error_text = fields.Char(
        string="Error text",
        compute="_compute_error_text",
        store=True,
    )

    @api.depends("stock_move_id", "stock_move_id.date")
    def _compute_date_done(self):
        for item in self:
            item.date_done = item.stock_move_id.date

    @api.depends("picking_id", "picking_id.partner_id")
    def _compute_partner_id(self):
        for item in self:
            item.partner_id = item.picking_id.partner_id.commercial_partner_id

    @api.depends("product_id")
    def _compute_product_key(self):
        for item in self:
            item.product_key = item.product_id.plastic_type_key

    @api.depends("picking_id", "picking_id.name")
    def _compute_proof(self):
        for item in self:
            item.proof = item.picking_id.name

    @api.depends("partner_id")
    def _compute_supplier_document_type(self):
        for item in self:
            item.supplier_document_type = item.partner_id.plastic_document_type

    @api.depends("partner_id", "concept")
    def _compute_supplier_document_number(self):
        for item in self:
            item.supplier_document_number = (
                item.partner_id.vat if item.concept != "3" else ""
            )

    @api.depends("partner_id", "concept")
    def _compute_supplier_social_reason(self):
        for item in self:
            item.supplier_social_reason = (
                item.partner_id.name if item.concept != "3" else ""
            )

    @api.depends("stock_move_id", "stock_move_id.product_uom_qty")
    def _compute_product_uom_qty(self):
        for item in self:
            qty = item.stock_move_id.product_uom_qty
            if item.stock_move_id.product_uom != item.product_id.uom_id:
                qty = item.stock_move_id.product_uom._compute_quantity(
                    qty, item.product_id.uom_id
                )
            item.product_uom_qty = qty

    @api.depends("product_id", "product_uom_qty")
    def _compute_kgs(self):
        for item in self:
            item.kgs = item.product_id.plastic_tax_weight * item.product_uom_qty

    @api.depends("product_id", "product_uom_qty")
    def _compute_no_recycling_kgs(self):
        for item in self:
            item.no_recycling_kgs = (
                item.product_id.plastic_weight_non_recyclable * item.product_uom_qty
            )

    @api.depends("product_id")
    def _compute_product_description(self):
        for item in self:
            item.product_description = item.product_id.name

    @api.depends("error_text")
    def _compute_entries_ok(self):
        for item in self:
            item.entries_ok = True if not item.error_text else False

    @api.depends("entry_number", "product_key", "kgs", "no_recycling_kgs")
    def _compute_error_text(self):
        """Checks if all line fields are filled."""
        precision = self.env["decimal.precision"].precision_get("Stock Weight")
        for record in self:
            errors = []
            if not record.entry_number:
                errors.append(_("Without entrie number"))
            if not record.product_key:
                errors.append(_("Without product key"))
            if float_is_zero(record.kgs, precision_digits=precision):
                errors.append(_("Without Weiht"))
            if float_is_zero(record.no_recycling_kgs, precision_digits=precision):
                errors.append(_("Without Weiht non recyclable"))
            record.error_text = ", ".join(errors)

    def _get_csv_report_info(self):
        self.ensure_one()
        return {
            "entry_number": self.entry_number,
            "date_done": self.date_done.strftime("%d-%m-%Y"),
            "concept": self.concept,
            "product_key": self.product_key,
            "product_description": self.product_description,
            "proof": self.proof,
            "supplier_document_type": self.supplier_document_type,
            "supplier_document_number": self.supplier_document_number,
            "supplier_social_reason": self.supplier_social_reason,
            "kgs": str(self.kgs).replace(".", ","),
            "no_recycling_kgs": str(self.no_recycling_kgs).replace(".", ","),
            "entry_note": self.entry_note or "",
        }

    def _get_csv_report_info_values(self):
        info = self._get_csv_report_info()
        return list(info.values())

    def _get_csv_report_header(self):
        data = self._get_csv_report_info_mapped({})
        return list(data.keys())
