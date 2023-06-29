# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import re
from odoo import api, fields, models, exceptions, _
from odoo.osv import expression
from pprint import pprint


class L10nEsAeatmod592Report(models.Model):
    _name = "l10n.es.aeat.mod592.report"
    _inherit = "l10n.es.aeat.report"
    _description = "AEAT 592 report"
    _aeat_number = "592"
    _period_quarterly = False
    _period_monthly = True
    _period_yearly = False

    number = fields.Char(default="592")
    amount_plastic_tax = fields.Float(
        string="Amount tax for non recyclable", store=True, default=0.45
    )
    manufacturer_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod592.report.line.manufacturer",
        inverse_name="report_id",
        string="Mod592 Journal entries",
        copy=False,
        readonly=True,
    )
    acquirer_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.mod592.report.line.acquirer",
        inverse_name="report_id",
        string="Mod592 Journal entries",
        copy=False,
        readonly=True,
    )

    # ACQUIRER TOTALS
    total_acquirer_entries_records = fields.Integer(
        compute="_compute_totals_acquirer",
        string="Total entries records",
        store=False,
    )
    total_weight_acquirer_records = fields.Float(
        compute="_compute_totals_acquirer",
        string="Total weight records",
        store=False,
    )
    total_weight_acquirer_non_reclyclable_records = fields.Float(
        compute="_compute_totals_acquirer",
        string="Total weight records non reclyclable",
        store=False,
    )
    total_amount_acquirer_records = fields.Float(
        compute="_compute_totals_acquirer",
        string="Total amount acquirer records",
        store=False,
    )

    # MANUFACTURER TOTALS
    total_manufacturer_entries_records = fields.Integer(
        compute="_compute_totals_manufacturer",
        string="Total entries records",
        store=True,
    )
    total_weight_manufacturer_records = fields.Float(
        compute="_compute_totals_manufacturer",
        string="Total weight records",
        store=True,
    )
    total_weight_manufacturer_non_reclyclable_records = fields.Float(
        compute="_compute_totals_manufacturer",
        string="Total weight records non reclyclable",
        store=True,
    )
    total_amount_manufacturer_records = fields.Float(
        compute="_compute_totals_manufacturer",
        string="Total amount manufacturer records",
        store=True,
    )

    # Only for smart Buttons, Can not use total_manufacturer_entries_records
    # if appears twice in the same view
    num_lines_acquirer = fields.Integer(
        'Number of lines acquirer', compute='_compute_num_lines_acquirer')
    num_lines_manufacturer = fields.Integer(
        'Number of lines manufacturer', 
        compute='_compute_num_lines_manufacturer')
    show_error_acquirer = fields.Boolean(
        'Acquirer lines with error',
        compute='_compute_show_error_acquirer')
    show_error_manufacturer = fields.Boolean(
        'Manufacturer lines with error',
        compute='_compute_show_error_manufacturer')

    def _compute_show_error_acquirer(self):
        for report in self:
            report.show_error_acquirer = any(
                not x.entries_ok for x in report.acquirer_line_ids)

    def _compute_show_error_manufacturer(self):
        for report in self:
            report.show_error_manufacturer = any(
                not x.entries_ok for x in report.manufacturer_line_ids)

    def _compute_totals_acquirer(self):
        for record in self:
            total_acquirer_entries_records = 0
            total_weight_acquirer_records = 0
            total_weight_acquirer_non_reclyclable_records = 0
            total_amount_acquirer_records = 0
            for acquirer_line in self.acquirer_line_ids:
                total_acquirer_entries_records += 1
                total_weight_acquirer_records += acquirer_line.kgs
                total_weight_acquirer_non_reclyclable_records += acquirer_line.no_recycling_kgs
                total_amount_acquirer_records += acquirer_line.no_recycling_kgs * record.amount_plastic_tax
            record.write({
                'total_acquirer_entries_records': total_acquirer_entries_records,
                'total_weight_acquirer_records': total_weight_acquirer_records,
                'total_weight_acquirer_non_reclyclable_records': total_weight_acquirer_non_reclyclable_records,
                'total_amount_acquirer_records': total_amount_acquirer_records,
            })

    def _compute_totals_manufacturer(self):
        for record in self:
            total_manufacturer_entries_records = 0
            total_weight_manufacturer_records = 0
            total_weight_manufacturer_non_reclyclable_records = 0
            total_amount_manufacturer_records = 0
            for manufacturer_line in self.manufacturer_line_ids:
                total_manufacturer_entries_records += 1
                total_weight_manufacturer_records += manufacturer_line.kgs
                total_weight_manufacturer_non_reclyclable_records += manufacturer_line.no_recycling_kgs
                total_amount_manufacturer_records += manufacturer_line.no_recycling_kgs * record.amount_plastic_tax
            record.write({
                'total_manufacturer_entries_records': total_manufacturer_entries_records,
                'total_weight_manufacturer_records': total_weight_manufacturer_records,
                'total_weight_manufacturer_non_reclyclable_records': total_weight_manufacturer_non_reclyclable_records,
                'total_amount_manufacturer_records': total_amount_manufacturer_records,
            })

    def _compute_num_lines_acquirer(self):
        for report in self:
            report.num_lines_acquirer = len(report.acquirer_line_ids)

    def _compute_num_lines_manufacturer(self):
        for report in self:
            report.num_lines_manufacturer = len(report.manufacturer_line_ids)

    def _compute_num_lines_manufacturer(self):
        for report in self:
            report.num_lines_manufacturer = len(report.manufacturer_line_ids)

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
            ("picking_id.partner_id.product_plastic_document_type", "=", '2'),
        ]
        # Deduction by: Non Spanish Shipping
        domain_concept_2 = [
            ("location_dest_id.usage", "=", "customer"),
            ("picking_id.partner_id.product_plastic_document_type", "!=", '1'),
        ]
        # Deduction by: Scrap
        # TODO: No scrap if quant is not intracomunitaty acquisition
        domain_concept_3 = [
            ("location_dest_id.scrap_location", "=", True),
        ]
        # Deduction by adquisition returns
        domain_concept_4 = [
            ("location_dest_id.usage", "=", 'supplier'),
            ("origin_returned_move_id", "!=",False),
        ]
        domain = expression.AND([
            domain_base, expression.OR([
                domain_concept_1, domain_concept_2, 
                domain_concept_3, domain_concept_4])])
        pprint(domain)
        return domain

    def get_manufacturer_moves_domain(self):
        """
        TODO: Dependency on mrp module could be heavy. we need strong
        traceability of manofactured quants to covear each case
        Temporaly retunf a domain that return no records as we dont have
        this casuistic yet.
        """
        false_domain = [('id', '<', 0)]

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
        #     ("picking_id.partner_id.product_plastic_document_type", "=", '1'),
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
        moves = self.env["stock.move"].search(
            self.get_acquirer_moves_domain())
        return moves

    def _get_manufacturer_moves(self):
        """Returns the stock moves of the manufacturer."""
        self.ensure_one()
        moves = self.env["stock.move"].search(
            self.get_manufacturer_moves_domain())
        return moves

    def calculate(self):
        """Computes the records in report."""
        self.ensure_one()
        with self.env.norecompute():
            self._cleanup_report()
            if self.company_id.company_plastic_acquirer:
                acquirer_moves = self._get_acquirer_moves()
                self._create_592_acquirer_details(acquirer_moves)

            if self.company_id.company_plastic_manufacturer:
                manufacturer_moves =  self._get_manufacturer_moves()
                self._create_592_manufacturer_details(manufacturer_moves)

        self.recompute()
        return True

    def _create_592_acquirer_details(self, move_lines):
        # line_values = []
        acquirer_values = []
        prefix = 'ADQ-'
        sequence = 0
        for move_line in move_lines:
            sequence += 1
            entry_number = prefix + str(sequence)
            acquirer_values.append(
                self._get_report_acquirer_vals(move_line, entry_number))

        if acquirer_values:
            self.env['l10n.es.aeat.mod592.report.line.acquirer'].\
                create(acquirer_values)

    def _create_592_manufacturer_details(self, move_lines):
        # line_values = []
        manufacturer_values = []
        prefix = 'FAB-'
        sequence = 0
        for move_line in move_lines:
            sequence += 1
            entry_number = prefix + str(sequence)
            manufacturer_values.append(
                self._get_report_manufacturer_vals(move_line, entry_number))

        if manufacturer_values:
            self.env['l10n.es.aeat.mod592.report.line.manufacturer'].\
                create(manufacturer_values)

    def _get_report_acquirer_vals(self, move_line, entry_number):
        partner = move_line.picking_id.partner_id.commercial_partner_id
        product = move_line.product_id

        # Convert move line qty to base uom of product
        qty = move_line.product_uom_qty
        if move_line.product_uom != product.uom_id:
            qty = move_line.product_uom._compute_quantity(
                qty, product.uom_id)
        
        concept = move_line._get_acquirer_concept_move()
        partner_name = partner.name if concept != '3' else ''
        partner_vat = partner.vat if concept != '3' else ''

        vals = {
            "entry_number": entry_number,
            "date_done": move_line.date,
            "concept": concept,
            "product_key": product.product_plastic_type_key,
            "proof": move_line.picking_id.name,
            "kgs": product.product_plastic_tax_weight * qty,
            "no_recycling_kgs": product.product_plastic_weight_non_recyclable * qty,
            "fiscal_acquirer": product.product_plastic_tax_regime_acquirer,
            "supplier_social_reason": partner_name,
            "supplier_document_number": partner_vat,
            "report_id": self.id,
            "stock_move_id": move_line.id,
            "supplier_document_type": partner.product_plastic_document_type,
        }
        return vals

    def _get_report_manufacturer_vals(self, move_line, entry_number):
        partner = move_line.picking_id.partner_id.commercial_partner_id
        product = move_line.product_id

        # Convert move line qty to base uom of product
        qty = move_line.product_uom_qty
        if move_line.product_uom != product.uom_id:
            qty = move_line.product_uom._compute_quantity(
                qty, product.uom_id)

        concept = move_line._get_manufacturer_concept_move()
        partner_name = partner.name if concept != '5' else ''
        partner_vat = partner.cat if concept != '5' else ''

        vals = {
            "entry_number": entry_number,
            "date_done": move_line.date,
            "concept": concept,
            "product_key": product.product_plastic_type_key,
            "product_description": move_line.product_id.name,
            "proof": move_line.picking_id.name,
            "kgs": product.product_plastic_tax_weight * qty,
            "no_recycling_kgs": product.product_plastic_weight_non_recyclable * qty,
            "fiscal_manufacturer": product.product_plastic_tax_regime_manufacturer,
            "supplier_social_reason": partner_name,
            "supplier_document_number": partner_vat,
            "entry_note": False,
            "report_id": self.id,
            "stock_move_id": move_line.id,
            "supplier_document_type": partner.product_plastic_document_type,
        }
        return vals

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
            if item.show_error_acquirer or item.show_error_manufacturer:
                raise exceptions.UserError(
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

    def view_action_mod592_report_line_acquirer(self):
        action = self.env.ref(
            'l10n_es_aeat_mod592.action_l10n_es_aeat_mod592_report_line_acquirer').read()[0]
        action['domain'] = [('id', 'in', self.acquirer_line_ids.ids)]
        return action

    def view_action_mod592_report_line_manufacturer(self):
        action = self.env.ref(
            'l10n_es_aeat_mod592.action_l10n_es_aeat_mod592_report_line_manufacturer').read()[0]
        action['domain'] = [('id', 'in', self.manufacturer_line_ids.ids)]
        return action
