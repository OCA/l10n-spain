# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


class TicketBAITaxAgency(models.Model):
    _name = "tbai.tax.agency"
    _description = "TicketBAI Tax Agency"

    name = fields.Char(string="Tax Agency name", required=True)
    version = fields.Char(
        string="TicketBAI version", compute="_compute_ticketbai_version", store=True
    )
    qr_base_url = fields.Char(
        string="QR Base URL", compute="_compute_ticketbai_version", store=True
    )
    test_qr_base_url = fields.Char(
        string="Test QR Base URL", compute="_compute_ticketbai_version", store=True
    )
    tax_agency_version_ids = fields.One2many(
        comodel_name="tbai.tax.agency.version", inverse_name="tbai_tax_agency_id"
    )
    rest_url_invoice = fields.Char(
        string="REST API URL for Invoices",
        compute="_compute_ticketbai_version",
        store=True,
    )
    rest_url_cancellation = fields.Char(
        string="REST API URL for Invoice Cancellations",
        compute="_compute_ticketbai_version",
        store=True,
    )
    test_rest_url_invoice = fields.Char(
        string="Test - REST API URL for Invoices",
        compute="_compute_ticketbai_version",
        store=True,
    )
    test_rest_url_cancellation = fields.Char(
        string="Test - REST API URL for Invoice Cancellations",
        compute="_compute_ticketbai_version",
        store=True,
    )
    sign_file_url = fields.Char(string="Sign File URL", required=True)
    sign_file_hash = fields.Char(string="Sign File HASH", required=True)

    def get_current_version(self):
        self.ensure_one()
        today = fields.Date.today()
        search_domain = [
            ("tbai_tax_agency_id", "=", self.id),
            "|",
            ("date_from", "<=", today),
            ("date_from", "=", False),
            "|",
            ("date_to", ">=", today),
            ("date_to", "=", False),
        ]
        return self.env["tbai.tax.agency.version"].search(search_domain)

    @api.depends(
        "tax_agency_version_ids",
        "tax_agency_version_ids.date_from",
        "tax_agency_version_ids.date_to",
        "tax_agency_version_ids.version",
    )
    def _compute_ticketbai_version(self):
        for record in self:
            tax_agency_version = record.get_current_version()
            record.version = tax_agency_version.version
            record.qr_base_url = tax_agency_version.qr_base_url
            record.test_qr_base_url = tax_agency_version.test_qr_base_url
            record.rest_url_invoice = tax_agency_version.rest_url_invoice
            record.rest_url_cancellation = tax_agency_version.rest_url_cancellation
            record.test_rest_url_invoice = tax_agency_version.test_rest_url_invoice
            record.test_rest_url_cancellation = (
                tax_agency_version.test_rest_url_cancellation
            )


class TicketBAITaxAgencyVersion(models.Model):
    _name = "tbai.tax.agency.version"
    _description = "TicketBAI Tax Agency - version"

    @api.constrains("version")
    def _check_ticketbai_version(self):
        for record in self:
            if len(record.version) not in range(1, 6):
                raise exceptions.ValidationError(
                    _(
                        "TicketBAI Tax Agency %(agency)s:\n"
                        "TicketBAI version %(version)s max size is 5 "
                        "characters."
                    )
                    % {
                        "agency": record.tbai_tax_agency_id.name,
                        "version": record.version,
                    }
                )

    @api.constrains("date_from", "date_to")
    def _unique_date_range(self):
        # Based in l10n_es_aeat module
        for record in self:
            domain = [
                ("id", "!=", record.id),
                ("tbai_tax_agency_id", "=", record.tbai_tax_agency_id.id),
            ]
            if record.date_from and record.date_to:
                domain += [
                    "|",
                    "&",
                    ("date_from", "<=", record.date_to),
                    ("date_from", ">=", record.date_from),
                    "|",
                    "&",
                    ("date_to", "<=", record.date_to),
                    ("date_to", ">=", record.date_from),
                    "|",
                    "&",
                    ("date_from", "=", False),
                    ("date_to", ">=", record.date_from),
                    "&",
                    ("date_to", "=", False),
                    ("date_from", "<=", record.date_to),
                ]
            elif record.date_from:
                domain += [("date_to", ">=", record.date_from)]
            elif record.date_to:
                domain += [("date_from", "<=", record.date_to)]
            date_lst = record.search(domain)
            if date_lst:
                raise exceptions.ValidationError(
                    _(
                        "TicketBAI Tax Agency %(agency)s:\n"
                        "Version %(version)s dates of the record "
                        "overlap with an existing record."
                    )
                    % {
                        "agency": record.tbai_tax_agency_id.name,
                        "version": record.version,
                    }
                )

    tbai_tax_agency_id = fields.Many2one(
        comodel_name="tbai.tax.agency", required=True, ondelete="restrict"
    )
    version = fields.Char(string="TicketBAI version", required=True)
    date_from = fields.Date()
    date_to = fields.Date()
    qr_base_url = fields.Char(string="QR Base URL", required=True)
    test_qr_base_url = fields.Char(string="Test - QR Base URL")
    rest_url_invoice = fields.Char(string="REST API URL for Invoices")
    rest_url_cancellation = fields.Char(string="REST API URL for Invoice Cancellations")
    test_rest_url_invoice = fields.Char(string="Test - REST API URL for Invoices")
    test_rest_url_cancellation = fields.Char(
        string="Test - REST API URL for Invoice Cancellations"
    )
