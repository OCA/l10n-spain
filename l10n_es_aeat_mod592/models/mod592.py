# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
import logging

from odoo import api, fields, models, exceptions, _

_logger = logging.getLogger(__name__)


class L10nEsAeatmod592Report(models.Model):
    _name = "l10n.es.aeat.mod592.report"
    _inherit = "l10n.es.aeat.report"
    _description = "AEAT 592 report"
    _aeat_number = "592"
    _period_quarterly = False
    _period_monthly = True
    _period_yearly = False

    number = fields.Char(default="592")
    total_manufacturer_entries_records = fields.Integer(
        compute="_compute_manufacturer_total_entries",
        string=_("Total entries records"),
        store=True,
    )
    total_weight_manufacturer_records = fields.Float(
        compute="_compute_manufacturer_total_weight",
        string=_("Total weight records"),
        store=True,
    )
    total_weight_manufacturer_non_reclyclable_records = fields.Float(
        compute="_compute_manufacturer_total_weight_non_reclyclable",
        string=_("Total weight records non reclyclable"),
        store=True,
    )
    total_amount_manufacturer_records = fields.Float(
        compute="_compute_manufacturer_total_amount",
        string=_("Total amount manufacturer records"),
        store=True,
    )
    total_acquirer_entries_records = fields.Integer(
        compute="_compute_acquirer_total_entries",
        string=_("Total entries records"),
        store=True,
    )
    total_weight_acquirer_records = fields.Float(
        compute="_compute_acquirer_total_weight",
        string=_("Total weight records"),
        store=True,
    )
    total_weight_acquirer_non_reclyclable_records = fields.Float(
        compute="_compute_acquirer_total_weight_non_reclyclable",
        string=_("Total weight records non reclyclable"),
        store=True,
    )
    total_amount_acquirer_records = fields.Float(
        compute="_compute_acquirer_total_amount",
        string=_("Total amount acquirer records"),
        store=True,
    )
    amount_plastic_tax = fields.Float(
        string=_("Amount tax for non recyclable"), store=True, default=0.45
    )
    manufacturer_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod592.report.line.manufacturer",
        inverse_name="report_id",
        string=_("Mod592 Journal entries"),
        copy=False,
        readonly=True,
    )
    acquirer_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod592.report.line.acquirer",
        inverse_name="report_id",
        string=_("Mod592 Journal entries"),
        copy=False,
        readonly=True,
    )

    company_plastic_type = fields.Selection(related="company_id.company_plastic_type")

    @api.depends("manufacturer_line_ids")
    def _compute_manufacturer_total_entries(self):
        for report in self:
            report.total_manufacturer_entries_records = len(
                report.manufacturer_line_ids
            )

    @api.depends("acquirer_line_ids")
    def _compute_acquirer_total_entries(self):
        for report in self:
            report.total_manufacturer_entries_records = len(report.acquirer_line_ids)

    @api.depends("manufacturer_line_ids.kilogramos")
    def _compute_manufacturer_total_weight(self):
        for report in self:
            report.total_weight_manufacturer_records = sum(
                report.mapped("manufacturer_line_ids.kilogramos")
            )

    @api.depends("acquirer_line_ids.kilogramos")
    def _compute_acquirer_total_weight(self):
        for report in self:
            report.total_weight_manufacturer_records = sum(
                report.mapped("acquirer_line_ids.kilogramos")
            )

    @api.depends("manufacturer_line_ids.kilogramos_no_reciclados")
    def _compute_manufacturer_total_weight_non_reclyclable(self):
        for report in self:
            report.total_weight_manufacturer_non_reclyclable_records = sum(
                report.mapped("manufacturer_line_ids.kilogramos_no_reciclados")
            )

    @api.depends("acquirer_line_ids.kilogramos_no_reciclados")
    def _compute_acquirer_total_weight_non_reclyclable(self):
        for report in self:
            report.total_weight_manufacturer_non_reclyclable_records = sum(
                report.mapped("acquirer_line_ids.kilogramos_no_reciclados")
            )

    @api.depends("manufacturer_line_ids.kilogramos_no_reciclados")
    def _compute_manufacturer_total_amount(self):
        for report in self:
            total_amount = 0.0
            for line in report.manufacturer_line_ids:
                total_amount += line.kilogramos_no_reciclados * self.amount_plastic_tax
                report.write(
                    {
                        "total_amount_manufacturer_records": total_amount,
                    }
                )

    @api.depends("acquirer_line_ids.kilogramos_no_reciclados")
    def _compute_acquirer_total_amount(self):
        for report in self:
            total_amount = 0.0
            for line in report.acquirer_line_ids:
                total_amount += line.kilogramos_no_reciclados * self.amount_plastic_tax
                report.write(
                    {
                        "total_amount_acquirer_records": total_amount,
                    }
                )

    # REGISTROS MANUFACTURER
    def _move_line_domain(self):

        return [
            ("parent_state", "=", "posted"),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            ("is_plastic_tax", "=", True),
        ]

    def _stock_move_domain(self):

        return [
            ("state", "=", "done"),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            ("is_plastic_tax", "=", True),
        ]

    def _create_592_details(self, move_lines):
        for move_line in move_lines:
            # if move_line.move_id.move_type in (
            #     "in_invoice",
            #     "out_invoice",
            #     "out_refund",
            #     "in_refund",
            # ):
            self._create_592_manufacturer_record_detail(move_line)
                
            # if self.company_id.company_plastic_type == 'manufacturer':
            #     pass
            # if self.company_id.company_plastic_type == 'acquirer':
            #     pass

    def _create_592_manufacturer_record_detail(self, move_line):

        return self.env["l10n.es.aeat.mod592.report.line.manufacturer"].create(
            {
                "report_id": self.id,
                "move_line_id": move_line.id,
                "fecha_hecho": move_line.date,
                "concepto": move_line.product_plastic_concept_manufacturer,
                "clave_producto": move_line.product_plastic_type_key,
                "descripcion_producto": move_line.name,
                "regimen_fiscal_manufacturer": move_line.product_plastic_tax_regime_manufacturer,
                "justificante": move_line.name,
                "proveedor_tipo_documento": move_line.partner_id.product_plastic_document_type
                or move_line.partner_id.property_account_position_id.product_plastic_document_type,
                "proveedor_numero_documento": move_line.partner_id.vat,
                "proveedor_razon_social": move_line.partner_id.name,
                "kilogramos": move_line.product_plastic_tax_weight,
                "kilogramos_no_reciclados": move_line.product_plastic_weight_non_recyclable,
                "observaciones_asiento": False,
            }
        )

    def _create_592_acquirer_record_detail(self, move_line):
        return self.env["l10n.es.aeat.mod592.report.line.acquirer"].create(
            {
                # "report_id": self.id,
                # "move_line_id": move_line.id,
                # "numero_asiento": move_line.move_id.name,
                # "fecha_hecho": move_line.date,
                # "concepto": move_line.product_plastic_concept_manufacturer,
                # "clave_producto": move_line.product_plastic_type_key,
                # "descripcion_producto": move_line.name,
                # "regimen_fiscal_acquirer": move_line.product_plastic_tax_regime_manufacturer,
                # "justificante": move_line.product_plastic_tax_description,
                # "proveedor_tipo_documento": move_line.move_id.partner_id.product_plastic_document_type or move_line.move_id.partner_id.property_account_position_id.product_plastic_document_type,
                # "proveedor_numero_documento": move_line.move_id.partner_id.vat,
                # "proveedor_razon_social": move_line.move_id.partner_id.name,
                # "kilogramos": move_line.product_plastic_tax_weight,
                # "kilogramos_no_reciclados": move_line.product_plastic_weight_non_recyclable,
                # "observaciones_asiento": False,
            }
        )

    def _cleanup_report(self):
        """Remove previous partner records and partner refunds in report."""
        self.ensure_one()
        self.manufacturer_line_ids.unlink()
        self.acquirer_line_ids.unlink()

    def calculate(self):
        """Computes the records in report."""
        self.ensure_one()
        with self.env.norecompute():
            self._cleanup_report()
            # MOVIMIENTOS DE FACTURAS
            # move_lines = self.env["account.move.line"].search(self._move_line_domain())
            # self._create_592_details(move_lines)
            # MOVIMIENTOS DE STOCK
            stock_moves = self.env["stock.move"].search(self._stock_move_domain())
            self._create_592_details(stock_moves)
        self.recompute()
        return True

    def button_recover(self):
        """Clean children records in this state for allowing things like
        cancelling an invoice that is inside this report.
        """
        self._cleanup_report()
        return super().button_recover()

    def _check_report_lines(self):
        """Checks if all the fields of all the report lines
        (partner records and partner refund) are filled
        """
        for item in self:
            for entries in item.manufacturer_line_ids:
                if not entries.entries_ok:
                    raise exceptions.UserError(
                        _(
                            "All entries records fields (Entrie number, VAT number "
                            "Concept, Key product, Fiscal regime, etc must be filled."
                        )
                    )

    def _write_sequence(self):
        """Checks if all the fields of all the report lines
        (partner records and partner refund) are filled
        """
        for item in self.manufacturer_line_ids:
            item.update(
                {
                    "numero_asiento": self.env["ir.sequence"].next_by_code(
                        "l10n.es.aeat.mod592.report.line.manufacturer"
                    )
                }
            )

    def get_report_file_name(self):
        return "{}{}C{}".format(
            self.year, self.company_vat, re.sub(r"[\W_]+", "", self.company_id.name)
        )

    def button_confirm(self):
        """Checks if all the fields of the report are correctly filled"""
        self._write_sequence()
        self._check_report_lines()

        return super(L10nEsAeatmod592Report, self).button_confirm()

    def export_xlsx_manufacturer(self):
        self.ensure_one()
        return self.env.ref(
            "l10n_es_aeat_mod592.l10n_es_aeat_mod592_xlsx_man"
        ).report_action(self)

    def export_csv_manufacturer(self):
        self.ensure_one()
        return self.env.ref(
            "l10n_es_aeat_mod592.l10n_es_aeat_mod592_csv_man"
        ).report_action(self)

    def export_xlsx_acquirer(self):
        self.ensure_one()
        return self.env.ref(
            "l10n_es_aeat_mod592.l10n_es_aeat_mod592_xlsx_acquirer"
        ).report_action(self)

    def export_csv_acquirer(self):
        self.ensure_one()
        return self.env.ref(
            "l10n_es_aeat_mod592.l10n_es_aeat_mod592_csv_acquirer"
        ).report_action(self)
