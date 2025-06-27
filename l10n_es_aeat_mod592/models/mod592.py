# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class L10nEsAeatmod592Report(models.Model):
    _name = "l10n.es.aeat.mod592.report"
    _inherit = "l10n.es.aeat.report"
    _description = "AEAT 592 report"
    _aeat_number = "592"
    _period_quarterly = True
    _period_monthly = True
    _period_yearly = False

    number = fields.Char(default="592")
    company_plastic_acquirer = fields.Boolean(
        related="company_id.company_plastic_acquirer"
    )
    company_plastic_manufacturer = fields.Boolean(
        related="company_id.company_plastic_manufacturer"
    )
    amount_plastic_tax = fields.Float(
        string="Amount tax for non recyclable", store=True, default=0.45
    )
    manufacturer_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod592.report.line.manufacturer",
        inverse_name="report_id",
        string="Manufacturer entries",
        copy=False,
        readonly=True,
    )
    acquirer_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod592.report.line.acquirer",
        inverse_name="report_id",
        string="Acquirer entries",
        copy=False,
        readonly=True,
    )
    # ACQUIRER TOTALS
    total_acquirer_entries = fields.Integer(
        compute="_compute_total_acquirer_entries",
        string="Total acquirer entries",
        store=False,
    )
    total_weight_acquirer = fields.Float(
        compute="_compute_total_weight_acquirer",
        string="Total weight acquirer",
        store=False,
    )
    total_weight_acquirer_non_reclyclable = fields.Float(
        compute="_compute_total_weight_acquirer_non_reclyclable",
        string="Total weight acquirer non reclyclable",
        store=False,
    )
    total_amount_acquirer = fields.Float(
        compute="_compute_total_amount_acquirer",
        string="Total amount acquirer",
        store=False,
        digits="Product Price",
    )
    # MANUFACTURER TOTALS
    total_manufacturer_entries = fields.Integer(
        compute="_compute_total_manufacturer_entries",
        string="Total manufacturer entries",
        store=True,
    )
    total_weight_manufacturer = fields.Float(
        compute="_compute_total_weight_manufacturer",
        string="Total weight manufacturer",
        store=True,
    )
    total_weight_manufacturer_non_reclyclable = fields.Float(
        compute="_compute_total_weight_manufacturer_non_reclyclable",
        string="Total weight manufacturer non reclyclable",
        store=True,
    )
    total_amount_manufacturer = fields.Float(
        compute="_compute_total_amount_manufacturer",
        string="Total amount manufacturer",
        store=True,
        digits="Product Price",
    )
    # Only for smart Buttons, Can not use total_manufacturer_entries_records
    # if appears twice in the same view
    num_lines_acquirer = fields.Integer(
        string="Number of lines acquirer", compute="_compute_num_lines_acquirer"
    )
    num_lines_manufacturer = fields.Integer(
        string="Number of lines manufacturer", compute="_compute_num_lines_manufacturer"
    )
    show_error_acquirer = fields.Boolean(
        string="Acquirer lines with error", compute="_compute_show_error_acquirer"
    )
    show_error_manufacturer = fields.Boolean(
        string="Manufacturer lines with error",
        compute="_compute_show_error_manufacturer",
    )

    @api.depends("acquirer_line_ids")
    def _compute_total_acquirer_entries(self):
        for item in self:
            item.total_acquirer_entries = len(item.acquirer_line_ids)

    @api.depends("acquirer_line_ids", "acquirer_line_ids.kgs")
    def _compute_total_weight_acquirer(self):
        for item in self:
            item.total_weight_acquirer = sum(item.mapped("acquirer_line_ids.kgs"))

    @api.depends("acquirer_line_ids", "acquirer_line_ids.no_recycling_kgs")
    def _compute_total_weight_acquirer_non_reclyclable(self):
        for item in self:
            item.total_weight_acquirer_non_reclyclable = sum(
                item.mapped("acquirer_line_ids.no_recycling_kgs")
            )

    @api.depends(
        "acquirer_line_ids", "acquirer_line_ids.no_recycling_kgs", "amount_plastic_tax"
    )
    def _compute_total_amount_acquirer(self):
        for item in self:
            total = 0
            for line in item.acquirer_line_ids:
                total += line.no_recycling_kgs * item.amount_plastic_tax
            item.total_amount_acquirer = total

    @api.depends("manufacturer_line_ids")
    def _compute_total_manufacturer_entries(self):
        for item in self:
            item.total_manufacturer_entries = len(item.manufacturer_line_ids)

    @api.depends("manufacturer_line_ids", "manufacturer_line_ids.kgs")
    def _compute_total_weight_manufacturer(self):
        for item in self:
            item.total_weight_manufacturer = sum(
                item.mapped("manufacturer_line_ids.kgs")
            )

    @api.depends("manufacturer_line_ids", "manufacturer_line_ids.no_recycling_kgs")
    def _compute_total_weight_manufacturer_non_reclyclable(self):
        for item in self:
            item.total_weight_manufacturer_non_reclyclable = sum(
                item.mapped("manufacturer_line_ids.no_recycling_kgs")
            )

    @api.depends(
        "manufacturer_line_ids",
        "manufacturer_line_ids.no_recycling_kgs",
        "amount_plastic_tax",
    )
    def _compute_total_amount_manufacturer(self):
        for item in self:
            total = 0
            for line in item.manufacturer_line_ids:
                total += line.no_recycling_kgs * item.amount_plastic_tax
            item.total_amount_manufacturer = total

    @api.depends("total_acquirer_entries")
    def _compute_num_lines_acquirer(self):
        for item in self:
            item.num_lines_acquirer = item.total_acquirer_entries

    @api.depends("total_manufacturer_entries")
    def _compute_num_lines_manufacturer(self):
        for item in self:
            item.num_lines_manufacturer = item.total_manufacturer_entries

    @api.depends("acquirer_line_ids", "acquirer_line_ids.entries_ok")
    def _compute_show_error_acquirer(self):
        for report in self:
            report.show_error_acquirer = any(
                not x.entries_ok for x in report.acquirer_line_ids
            )

    @api.depends("manufacturer_line_ids", "manufacturer_line_ids.entries_ok")
    def _compute_show_error_manufacturer(self):
        for report in self:
            report.show_error_manufacturer = any(
                not x.entries_ok for x in report.manufacturer_line_ids
            )

    def _cleanup_report(self):
        """Remove previous partner records and partner refunds in report."""
        self.ensure_one()
        self.manufacturer_line_ids.unlink()
        self.acquirer_line_ids.unlink()

    def get_acquirer_moves_domain(self):
        """
        Search intracomunitary incoming moves with plastic tax
        TODO: Date range search by invoice related date or day 15 of next month
        whathever is first
        """
        domain_base = [
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            ("state", "=", "done"),
            ("picking_id.partner_id", "!=", False),
            ("company_id", "=", self.company_id.id),
            ("product_id.is_plastic_tax", "=", True),
        ]
        # Intracomunitary Adquisitions
        domain_concept_1 = [
            ("location_id.usage", "=", "supplier"),
            ("picking_id.partner_id.plastic_document_type", "=", "2"),
        ]
        # Deduction by: Non Spanish Shipping
        domain_concept_2 = [
            ("location_dest_id.usage", "=", "customer"),
            ("picking_id.partner_id.plastic_document_type", "!=", "1"),
        ]
        # Deduction by: Scrap
        # TODO: No scrap if quant is not intracomunitaty acquisition
        domain_concept_3 = [
            ("location_dest_id.scrap_location", "=", True),
        ]
        # Deduction by adquisition returns
        domain_concept_4 = [
            ("location_dest_id.usage", "=", "supplier"),
            ("origin_returned_move_id", "!=", False),
        ]
        domain = expression.AND(
            [
                domain_base,
                expression.OR(
                    [
                        domain_concept_1,
                        domain_concept_2,
                        domain_concept_3,
                        domain_concept_4,
                    ]
                ),
            ]
        )
        return domain

    def get_manufacturer_moves_domain(self):
        """
        TODO: Dependency on mrp module could be heavy. we need strong
        traceability of manufactured quants to covear each case
        Temporaly retunf a domain that return no records as we dont have
        this casuistic yet (l10n_es_aeat_mod592_mrp for example).
        """
        false_domain = [("id", "<", 0)]
        # Code below is only a idea od what we could do whithout develop
        # strong traceability of manofactured quants.
        # domain_base = [
        #     ("date", ">=", self.date_start),
        #     ("date", "<=", self.date_end),
        #     ("state", "=", "done"),
        #     ("picking_id.partner_id", "!=", False),
        #     ("company_id", "=", self.company_id.id),
        #     ("product_id.is_plastic_tax", "=", True),
        #     ("product_id.tax_plastic_type", "in", ('manufacturer', 'both')),
        # ]
        # # Initial Existence
        # # If first sale, locate all existence
        # # domain_concept_1 = [
        # #     ("location_dest_id.usage", "=", "internal"),
        # # ]
        # # Manufacturation by Atticle 71.b of Law 7/2022
        # # domain_concept_2 = [
        # #     ("location_dest_id.usage", "=", "production"),
        # # ]
        # # Return products for destruction, or re-manufacturation
        # domain_concept_3 = [
        #     ("location_dest_id.scrap_location", "=", True),
        # ]
        # # Sales to non spanish customers
        # domain_concept_4 = [
        #     ("location_dest_id.usage", "=", 'customer'),
        #     ("picking_id.partner_id.plastic_document_type", "=", '1'),
        # ]
        # # ? Another destructions
        # # domain_concept_5 = [
        # #     ("location_dest_id.scrap_location", "=", True),
        # # ]
        # # domain = expression.AND([
        # #     domain_base, expression.OR([
        # #         domain_concept_1, domain_concept_2,
        # #         domain_concept_3, domain_concept_4])])
        # domain = expression.AND([
        #     domain_base, expression.OR([
        #         domain_concept_3, domain_concept_4])])
        # # return domain
        return false_domain

    def _get_acquirer_moves(self):
        """Returns the stock moves of the acquirer."""
        self.ensure_one()
        return self.env["stock.move"].search(self.get_acquirer_moves_domain())

    def _get_manufacturer_moves(self):
        """Returns the stock moves of the manufacturer."""
        self.ensure_one()
        return self.env["stock.move"].search(self.get_manufacturer_moves_domain())

    def calculate(self):
        """Computes the records in report."""
        res = super().calculate()
        for item in self:
            # Create acquirer_lines
            if item.company_plastic_acquirer:
                acquirer_lines = []
                for sm in item._get_acquirer_moves():
                    acquirer_line = item.acquirer_line_ids.filtered(
                        lambda x: x.stock_move_id == sm
                    )
                    acquirer_vals = {"stock_move_id": sm.id}
                    if acquirer_line:
                        acquirer_lines.append((1, acquirer_line.id, acquirer_vals))
                    else:
                        acquirer_lines.append((0, 0, acquirer_vals))
                item.acquirer_line_ids = acquirer_lines
            # Create manufacturer_lines
            if item.company_plastic_manufacturer:
                manufacturer_lines = []
                for sm in item._get_manufacturer_moves():
                    manufacturer_line = item.manufacturer_line_ids.filtered(
                        lambda x: x.stock_move_id == sm
                    )
                    m_vals = {"stock_move_id": sm.id}
                    if manufacturer_line:
                        manufacturer_lines.append((1, manufacturer_line.id, m_vals))
                    else:
                        manufacturer_lines.append((0, 0, m_vals))
                item.manufacturer_line_ids = manufacturer_lines
        item.env.flush_all()
        return res

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
        if any(x.show_error_acquirer or x.show_error_manufacturer for x in self):
            raise UserError(
                _(
                    "All entries records fields (Entrie number, VAT number "
                    "Concept, Key product, Fiscal regime, etc must be filled."
                )
            )

    def get_report_file_name(self):
        return "{}{}C{}".format(
            self.year, self.company_vat, re.sub(r"[\W_]+", "", self.company_id.name)
        )

    def button_confirm(self):
        """Checks if all the fields of the report are correctly filled"""
        self._check_report_lines()
        return super().button_confirm()

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

    def _format_csv(self, rows, delimiter):
        csv_string = ""
        for row in rows:
            for field in row:
                csv_string += field and str(field) or ""
                csv_string += delimiter
            csv_string += "\n"
        return csv_string

    def view_action_mod592_report_line_acquirer(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_es_aeat_mod592.action_l10n_es_aeat_mod592_report_line_acquirer"
        )
        action["domain"] = [("id", "in", self.acquirer_line_ids.ids)]
        return action

    def view_action_mod592_report_line_manufacturer(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_es_aeat_mod592.action_l10n_es_aeat_mod592_report_line_manufacturer"
        )
        action["domain"] = [("id", "in", self.manufacturer_line_ids.ids)]
        return action
