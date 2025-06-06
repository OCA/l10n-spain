# Copyright 2025 Netkia - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from .aeat_address_types import AEAT_ADDRESS_TYPES


class L10nEsAeatRealEstate(models.Model):
    _name = "l10n.es.aeat.real_estate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Real Estates for AEAT"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda s: s.env.company,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        help="Partner that owns this real estate",
    )
    representative_vat = fields.Char(
        string="L.R. VAT number",
        size=32,
        compute="_compute_representative_vat",
        store=True,
        readonly=False,
        help="Legal Representative VAT number of the real estate",
    )
    reference = fields.Char(
        string="Catastral Reference",
        size=25,
    )
    address_type = fields.Selection(
        selection=AEAT_ADDRESS_TYPES,
        help="Valid AEAT Address type",
        default="CALLE",
        required=True,
    )
    address = fields.Char(
        size=50,
        required=True,
    )
    number_type = fields.Selection(
        selection=[
            ("NUM", "Number"),
            ("KM.", "Kilometer"),
            ("S/N", "Without number"),
        ],
        required=True,
        default="NUM",
    )
    number = fields.Integer()
    number_calification = fields.Selection(
        selection=[
            ("BIS", "Bis"),
            ("MOD", "Mod"),
            ("DUP", "Dup"),
            ("ANT", "Ant"),
        ],
    )
    block = fields.Char(size=3)
    portal = fields.Char(size=3)
    stairway = fields.Char(size=3)
    floor = fields.Char(size=3)
    door = fields.Char(size=3)
    complement = fields.Char(
        size=40,
        help="Complement (urbanization, industrial park...)",
    )
    country_id = fields.Many2one(
        comodel_name="res.country",
        string="Country",
        default=lambda self: self.env.ref("base.es"),
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        compute="_compute_state_id",
        readonly=False,
        store=True,
    )
    state_code = fields.Char(
        compute="_compute_state_code",
        store=True,
        readonly=False,
        compute_sudo=True,
    )
    zip_id = fields.Many2one(
        comodel_name="res.city.zip",
        string="ZIP Location",
        index=True,
        compute="_compute_zip_id",
        readonly=False,
        store=True,
    )
    city_id = fields.Many2one(
        index=True,
        compute="_compute_city_id",
        readonly=False,
        store=True,
    )
    city = fields.Char(
        compute="_compute_city",
        store=True,
        readonly=False,
        size=30,
        required=True,
    )
    zip = fields.Char(
        compute="_compute_zip",
        size=5,
        readonly=False,
        required=True,
    )
    # Check for errors
    check_ok = fields.Boolean(
        compute="_compute_check_ok",
        string="Record is OK",
        store=True,
        help="Checked if this record is OK",
    )
    error_text = fields.Char(
        string="Errors",
        compute="_compute_check_ok",
        store=True,
    )

    @api.depends("partner_id.vat")
    def _compute_representative_vat(self):
        for record in self:
            record.representative_vat = record.partner_id.vat

    @api.depends("state_id", "country_id", "zip")
    def _compute_zip_id(self):
        """Empty the zip auto-completion field if data mismatch when on UI."""
        for record in self.filtered("zip_id"):
            fields_map = {
                "zip": "name",
                "city_id": "city_id",
                "state_id": "state_id",
                "country_id": "country_id",
            }
            for rec_field, zip_field in fields_map.items():
                if (
                    record[rec_field]
                    and record[rec_field] != record._origin[rec_field]
                    and record[rec_field] != record.zip_id[zip_field]
                ):
                    record.zip_id = False
                    break

    @api.depends("zip_id")
    def _compute_state_id(self):
        for record in self:
            state = record.zip_id.city_id.state_id
            if state and record.state_id != state:
                record.state_id = record.zip_id.city_id.state_id
            else:
                record.state_id = record.state_id

    @api.depends("state_id")
    def _compute_state_code(self):
        for record in self:
            record.state_code = record.zip_id.name[:2] if record.zip_id else ""

    @api.depends("zip_id")
    def _compute_city_id(self):
        for record in self:
            if record.zip_id:
                record.city_id = record.zip_id.city_id.id

    @api.depends("zip_id")
    def _compute_city(self):
        for record in self:
            prev_city = record.city
            if record.zip_id:
                record.city = record.zip_id.city_id.name
            else:
                record.city = prev_city

    @api.depends("zip_id")
    def _compute_zip(self):
        for record in self:
            if record.zip_id:
                record.zip = record.zip_id.name

    @api.depends("state_code")
    def _compute_check_ok(self):
        self.update({"check_ok": False, "error_text": False})
        for record in self:
            errors = []
            if not record.state_code:
                errors.append(_("Without state"))
            record.check_ok = not bool(errors)
            record.error_text = bool(errors) and ", ".join(errors)
