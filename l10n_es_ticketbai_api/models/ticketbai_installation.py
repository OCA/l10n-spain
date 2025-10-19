# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


class TicketBaiInstallation(models.Model):
    _name = "tbai.installation"
    _description = "TicketBAI installation"

    name = fields.Char(
        string="Software Name",
        required=True,
        copy=False,
        help="Registered name at the Tax Agency.",
    )
    developer_id = fields.Many2one(
        comodel_name="res.partner", string="Developer", required=True, copy=False
    )
    vat = fields.Char("TIN", related="developer_id.vat")
    license_key = fields.Char(required=True, copy=False)
    version = fields.Char(
        string="Software Version",
        required=True,
        copy=False,
        help="Version of the software.",
    )

    @api.constrains("license_key")
    def _check_license_key(self):
        for record in self:
            if not record.license_key:
                raise exceptions.ValidationError(
                    _("TicketBAI License Key is required.")
                )
            elif 20 < len(record.license_key):
                raise exceptions.ValidationError(
                    _(
                        "TicketBAI License Key longer than expected. "
                        "Should be 20 characters max.!"
                    )
                )

    @api.constrains("developer_id")
    def _check_developer_id(self):
        for record in self:
            if not record.developer_id:
                raise exceptions.ValidationError(_("TicketBAI Developer is required."))

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not record.name:
                raise exceptions.ValidationError(
                    _("TicketBAI Software Name is required.")
                )

    _sql_constraints = [
        ("name_ref_uniq", "UNIQUE(name)", _("Software Name must be unique!")),
        ("developer_ref_uniq", "UNIQUE(developer_id)", _("Developer must be unique!")),
        ("license_ref_uniq", "UNIQUE(license_key)", _("License Key must be unique!")),
    ]
