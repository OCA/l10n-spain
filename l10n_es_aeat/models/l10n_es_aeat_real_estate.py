# Copyright 2023 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from .aeat_data import AEAT_ADDRESS_TYPES, AEAT_STATES_CODE_MAP


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
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        domain="[('country_id.code', '=', 'ES')]",
        required=True,
    )
    state_code = fields.Char(
        compute="_compute_state_related_fields",
        store=True,
        compute_sudo=True,
    )
    township_domain = fields.Many2many(
        comodel_name="l10n.es.aeat.township",
        compute="_compute_state_related_fields",
        store=False,
        compute_sudo=True,
    )
    township_id = fields.Many2one(
        comodel_name="l10n.es.aeat.township",
        string="Township",
        domain="[('id', 'in', township_domain)]",
        required=True,
    )
    city = fields.Char(
        compute="_compute_city",
        store=True,
        readonly=False,
        size=30,
        required=True,
    )
    postal_code = fields.Char(
        size=5,
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

    @api.depends("state_id")
    def _compute_state_related_fields(self):
        leat_model = self.env["l10n.es.aeat.township"]
        self.township_domain = []
        for record in self:
            state_code = AEAT_STATES_CODE_MAP.get(record.state_id.code, False)
            record.state_code = state_code
            if state_code:
                record.township_domain = leat_model.search(
                    [("state_code", "=", state_code)]
                ).ids

    @api.depends("township_id")
    def _compute_city(self):
        for record in self:
            record.city = record.township_id and record.township_id.name or False

    @api.depends("state_code")
    def _compute_check_ok(self):
        self.update({"check_ok": False, "error_text": False})
        for record in self:
            errors = []
            if not record.state_code:
                errors.append(_("Without state"))
            record.check_ok = not bool(errors)
            record.error_text = bool(errors) and ", ".join(errors)
