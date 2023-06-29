# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class L10nEsAeatmod592LineAcquirer(models.Model):

    _description = "AEAT 592 Acquirer report"
    _name = "l10n.es.aeat.mod592.report.line.acquirer"
    _rec_name = "entry_number"

    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod592.report", string="Mod592 Report")
    sequence = fields.Integer(default=1)

    entry_number = fields.Char('Entrie number')
    concept = fields.Selection(
        [
            ("1", _("(1) Intra-community acquisition")),
            ("2", _("(2) Shipping outside Spanish territory")),
            ("3", _("(3) Inadequacy or destruction")),
            ("4", _("(4) Return for destruction or reincorporation into the manufacturing process")),
        ],
        string='Concept')
    product_key = fields.Selection(
        [
            ("A", _("(A) Non-reusable")),
            ("B", _("(B) Semi-finished")),
            ("C", _("(C) Plastic product intended to allow the closure")),
        ],
        string='Product Key')
    date_done = fields.Date('Date')

    fiscal_acquirer = fields.Selection(
        [
            ("A", _("(A) Subjection and non-exemption Law 7/2022, of April 8")),
            ("B", _("(B) Non-subjection article 73 c) Law 7/2022, of April 8")),
            ("C", _("(C) Not subject to article 73 d) Law 7/2022, of April 8")),
            ("D", _("(D) Exemption article 75 a) 1º Law 7/2022, of April 8")),
            ("E", _("(E) Exemption article 75 a) 2º Law 7/2022, of April 8")),
            ("F", _("(F) Exemption article 75 a) 3º Law 7/2022, of April 8")),
            ("G", _("(G) Exemption article 75 b) Law 7/2022, of April 8")),
            ("H", _("(H) Exemption article 75 c) Law 7/2022, of April 8")),
            ("I", _("(I) Exemption article 75 d) Law 7/2022, of April 8")),
            ("J", _("(J) Exemption article 75 e) Law 7/2022, of April 8")),
            ("K", _("(K) Exemption article 75 f) Law 7/2022, of April 8")),
            ("L", _("(L) Exemption article 75 g) 1º Law 7/2022, of April 8")),
            ("M", _("(M) Exemption article 75 g) 2º Law 7/2022, of April 8")),
        ],
        string='Fiscal reginme acquirer')
    proof = fields.Char('Supporting document')
    supplier_document_type = fields.Selection(
        [
            ("1", _("(1) NIF or Spanish NIE")),
            ("2", _("(2) Intra-Community VAT NIF")),
            ("3", _("(3) Others")),
        ],
        string='Supplier document type')
    supplier_document_number = fields.Char(
        'Supplier document number')
    supplier_social_reason = fields.Char(
        'Supplier name')
    kgs = fields.Float('Weiht')
    no_recycling_kgs = fields.Float(
        'Weiht non reclycable')
    entry_note = fields.Text(
        'Entries observation')

    stock_move_id = fields.Many2one(
        comodel_name="stock.move", string="Stock Move", required=True
    )
    entries_ok = fields.Boolean(
        compute="_compute_entries_ok",
        string="Entries OK",
        help="Checked if record is OK",
    )
    error_text = fields.Char(
        string="Error text",
        compute="_compute_entries_ok",
        store=True,
    )

    @api.depends("supplier_document_number", "product_key", "supplier_social_reason", "entry_number", "fiscal_acquirer", "supplier_document_type", "supplier_document_number")
    def _compute_entries_ok(self):
        """Checks if all line fields are filled."""
        for record in self:
            errors = []
            if not record.entry_number:
                errors.append(_("Without entrie number"))
            if not record.concept:
                errors.append(_("Without concept"))
            if not record.product_key:
                errors.append(_("Without product key"))
            if record.concept != '3' and not record.supplier_social_reason:
                errors.append(_("Without supplier name"))
            if not record.fiscal_acquirer:
                errors.append(_("Without regime"))
            if record.concept != '3' and not record.supplier_document_number:
                errors.append(_("Without VAT"))
            if not record.kgs > 0.0:
                errors.append(_("Without Weiht"))
            if not record.no_recycling_kgs > 0.0:
                errors.append(_("Without Weiht non recyclable"))

            record.entries_ok = bool(not errors)
            record.error_text = ", ".join(errors)
