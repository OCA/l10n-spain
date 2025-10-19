# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class TicketBaiGeneralInfo(models.TransientModel):
    _name = "tbai.info"
    _description = "TicketBAI general information"

    tbai_enabled = fields.Boolean(
        default=lambda self: self.env.user.company_id.tbai_enabled
    )
    name = fields.Char(string="Developer name", compute="_compute_name")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.user.company_id,
    )
    developer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Developer",
        related="company_id.tbai_developer_id",
        readonly=True,
    )
    software = fields.Char(compute="_compute_software")
    device_serial_number = fields.Char(compute="_compute_device_serial_number")

    @api.depends("developer_id", "developer_id.vat", "developer_id.name")
    def _compute_name(self):
        for record in self:
            record.name = "({}) {}".format(
                record.developer_id.vat,
                record.developer_id.name,
            )

    @api.depends("company_id")
    def _compute_software(self):
        for record in self:
            name = "l10n_es_ticketbai"
            name_api = "l10n_es_ticketbai_api"
            software_version = (
                self.sudo()
                .env["ir.module.module"]
                .search([("name", "=", name)])
                .latest_version
            )
            software_version_api = (
                self.sudo()
                .env["ir.module.module"]
                .search([("name", "=", name_api)])
                .latest_version
            )
            record.software = "{} ({} {}, {} {})".format(
                record.company_id.tbai_software_name,
                name_api,
                software_version_api,
                name,
                software_version,
            )

    @api.depends("company_id")
    def _compute_device_serial_number(self):
        for record in self:
            record.device_serial_number = record.company_id.tbai_device_serial_number
