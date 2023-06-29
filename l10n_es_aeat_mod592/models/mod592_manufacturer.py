# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class L10nEsAeatmod592LineManufacturer(models.Model):

    _description = "AEAT 592 Manufacturer report"
    _name = "l10n.es.aeat.mod592.report.line.manufacturer"
    _rec_name = "entry_number"

    sequence = fields.Integer(default=1)
    entry_number = fields.Char(string='Entrie number', store=True, limit=20)

    date_done = fields.Date(string='Date', store=True, limit=10)
    concept = fields.Selection(
        [
            ("1", _("(1) Initial existence")),
            ("2", _("(2) Manufacturing")),
            ("3", _("(3) Return of products for destruction or reincorporation into the manufacturing process")),
            ("4", _("(4) Delivery or making available of the products accounted for")),
            ("5", _("(5) Other cancellations of the products accounted for other than their delivery or availability")),
        ],
        string=_('Concept'))
    product_key = fields.Selection(
        [
            ("A", _("(A) Non-reusable")),
            ("B", _("(B) Semi-finished")),
            ("C", _("(C) Plastic product intended to allow the closure")),
        ],
        string='Key product')
    product_description = fields.Char(
        string='Product description')
    fiscal_manufacturer = fields.Selection(
        [
            ("A", _("(A) Subjection and non-exemption ")),
            ("B", _("(B) Not subject to article 73 a) Law 7/2022, of April 8")),
            ("C", _("(C) Not subject to article 73 b) Law 7/2022, of April 8")),
            ("D", _("(D) Non-subjection article 73 c) Law 7/2022, of April 8")),
            ("E", _("(E) Not subject to article 73 d) Law 7/2022, of April 8")),
            ("F", _("(F) Exemption article 75 a) 1º Law 7/2022, of April 8")),
            ("G", _("(G) Exemption article 75 a) 2º Law 7/2022, of April 8")),
            ("H", _("(H) Exemption article 75 a) 3º Law 7/2022, of April 8")),
            ("I", _("(I) Exemption article 75 c) Law 7/2022, of April 8")),
            ("J", _("(J) Exemption article 75 g) 1º Law 7/2022, of April 8")),
            ("K", _("(K) Exemption article 75 g) 2º Law 7/2022, of April 8")),
        ],
        string="Fiscal regime manufacturer")

    proof = fields.Char('Proof document')
    supplier_document_type = fields.Selection(
        [
            ("1", _("(1) NIF or Spanish NIE")),
            ("2", _("(2) Intra-Community VAT NIF")),
            ("3", _("(3) Others")),
        ],
        string='Supplier document type')
    supplier_document_number = fields.Char(string='Supplier document number')
    supplier_social_reason = fields.Char('Supplier name')
    kgs = fields.Float('Weight')
    no_recycling_kgs = fields.Float('Weight non reclycable')
    entry_note = fields.Text('Entries observation')
    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod592.report", string="Mod592 Report")
    # move_line_id = fields.Many2one(
    #     comodel_name="account.move.line", string="Journal Item", required=True
    # )
    stock_move_id = fields.Many2one(
        comodel_name="stock.move", string="Stock Move", required=True
    )
    entries_ok = fields.Boolean(
        compute="_compute_entries_ok",
        string="Entries OK",
        help="Checked if record is OK",
        compute_sudo=True
    )
    error_text = fields.Char(
        string="Error text",
        compute="_compute_entries_ok",
        store=True,
        compute_sudo=True,
    )

    @api.depends("supplier_document_number", "product_key", "supplier_social_reason", "entry_number", "fiscal_manufacturer", "supplier_document_type", "supplier_document_number")
    def _compute_entries_ok(self):
        """Checks if all line fields are filled."""
        for record in self:
            errors = []
            if not record.product_key:
                errors.append(_("Without product key"))
            if not record.supplier_social_reason:
                errors.append(_("Without supplier name"))
            if not record.entry_number:
                errors.append(_("Without entrie number"))
            if not record.fiscal_manufacturer:
                errors.append(_("Without regime"))
            if not record.supplier_document_type:
                errors.append(_("Without supplier document"))
            if not record.supplier_document_number:
                errors.append(_("Without document number"))
            if not record.kgs > 0.0:
                errors.append(_("Without Weiht"))
            if not record.no_recycling_kgs > 0.0:
                errors.append(_("Without Weiht non recyclable"))

            # record.entries_ok = bool(not errors)
            record.entries_ok = True
            record.error_text = ", ".join(errors)
