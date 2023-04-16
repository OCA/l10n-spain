# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class L10nEsAeatmod592LineManufacturer(models.Model):

    _description = "AEAT 592 Manufacturer report"
    _name = "l10n.es.aeat.mod592.report.line.manufacturer"

    sequence = fields.Integer(default=1)
    numero_asiento = fields.Char(_('Entrie number'), store=True, limit=20)



    fecha_hecho = fields.Date(_('Date'), store=True, limit=10)
    concepto = fields.Selection(
        [
            ("1", _("(1) Initial existence")),
            ("2", _("(2) Manufacturing")),
            ("3", _("(3) Return of products for destruction or reincorporation into the manufacturing process")),
            ("4", _("(4) Delivery or making available of the products accounted for")),
            ("5", _("(5) Other cancellations of the products accounted for other than their delivery or availability")),
        ],
        string=_('Concept'), store=True, limit=1)
    clave_producto = fields.Selection(
        [
            ("A", _("(A) Non-reusable")),
            ("B", _("(B) Semi-finished")),
            ("C", _("(C) Plastic product intended to allow the closure")),
        ],
        string=_('Key product'), store=True, limit=1)
    descripcion_producto = fields.Char(
        _('Product description'), store=True, limit=30)
    regimen_fiscal_manufacturer = fields.Selection(
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
        string=_("Fiscal regime manufacturer"), store=True, limit=5
    )

    justificante = fields.Char(_('Supporting document'), store=True, limit=40)
    proveedor_tipo_documento = fields.Selection(
        [
            ("1", _("(1) NIF or Spanish NIE")),
            ("2", _("(2) Intra-Community VAT NIF")),
            ("3", _("(3) Others")),
        ],
        string=_('Supplier document type'), store=True, limit=1
    )
    proveedor_numero_documento = fields.Char(
        _('Supplier document number'), store=True, limit=15)
    proveedor_razon_social = fields.Char(
        _('Supplier name'), store=True, limit=150)
    kilogramos = fields.Float(_('Weight'), store=True, limit=17)
    kilogramos_no_reciclados = fields.Float(
        _('Weight non reclycable'), store=True, limit=17)
    observaciones_asiento = fields.Text(
        _('Entries observation'), store=True, limit=200)
    report_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod592.report", string="Mod592 Report")
    move_line_id = fields.Many2one(
        comodel_name="account.move.line", string="Journal Item", required=True
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

    @api.depends("proveedor_numero_documento", "clave_producto", "proveedor_razon_social", "numero_asiento", "regimen_fiscal_manufacturer", "proveedor_tipo_documento", "proveedor_numero_documento")
    def _compute_entries_ok(self):
        """Checks if all line fields are filled."""
        for record in self:
            errors = []
            if not record.proveedor_numero_documento:
                errors.append(_("Without VAT"))
            if not record.clave_producto:
                errors.append(_("Without product key"))
            if not record.proveedor_razon_social:
                errors.append(_("Without supplier name"))
            if not record.numero_asiento:
                errors.append(_("Without entrie number"))
            if not record.regimen_fiscal_manufacturer:
                errors.append(_("Without regime"))
            if not record.proveedor_tipo_documento:
                errors.append(_("Without supplier document"))
            if not record.proveedor_numero_documento:
                errors.append(_("Without document number"))
            if not record.kilogramos > 0.0:
                errors.append(_("Without Weiht"))
            if not record.kilogramos_no_reciclados > 0.0:
                errors.append(_("Without Weiht non recyclable"))

            record.entries_ok = bool(not errors)
            record.error_text = ", ".join(errors)

    # @api.model
    # def create(self, vals):
    #     for record in self:
    #         seq = self.env['ir.sequence'].next_by_code(
    #             'l10n.es.aeat.mod592.report.line.manufacturer')
    #         asiento = self.move_line.move_id.name
    #         record.write({
    #             'numero_asiento': str(seq + asiento),
    #         })
