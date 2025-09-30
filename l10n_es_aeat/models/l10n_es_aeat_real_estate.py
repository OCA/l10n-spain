# Copyright 2025 Netkia - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

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
    city_id = fields.Many2one(
        comodel_name="res.city",
        string="City ID",
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
    real_estate_situation = fields.Selection(
        [("1", "01"), ("2", "02"), ("3", "03"), ("4", "04")],
        compute="_compute_real_estate_situation",
        store=True,
        readonly=False,
    )

    @api.depends("reference", "state_id")
    def _compute_real_estate_situation(self):
        for rec in self:
            if not rec.reference:
                rec.real_estate_situation = "4"
            else:
                rec.real_estate_situation = "1"
                if rec.state_id:
                    code = rec.state_id.code
                    if code in ["BI", "SS", "VI"]:
                        rec.real_estate_situation = "2"
                    elif code == "NA":
                        rec.real_estate_situation = "3"

    @api.depends("partner_id.vat")
    def _compute_representative_vat(self):
        for record in self:
            record.representative_vat = record.partner_id.vat

    @api.depends("city_id")
    def _compute_city(self):
        for record in self:
            if record.city_id and record.city_id.name:
                record.city = record.city_id.name
            else:
                record.city = ""

    @api.depends("state_code")
    def _compute_check_ok(self):
        self.update({"check_ok": False, "error_text": False})
        for record in self:
            errors = []
            if not record.state_code:
                errors.append(self.env._("Without state"))
            record.check_ok = not bool(errors)
            record.error_text = bool(errors) and ", ".join(errors)

    @api.constrains("reference")
    def _check_reference(self):
        for record in self:
            ref = record.reference
            if not ref:
                continue

            ref = self._normalize_reference(ref)
            if not self._is_valid_reference(ref):
                raise ValidationError(
                    _("The cadastral reference '%s' is not valid.") % record.reference
                )

    @api.model
    def _normalize_reference(self, value):
        """Remove common separators and uppercase the reference."""
        return re.sub(r"[\s\-_\.]", "", value or "").upper()

    @api.model
    def _is_valid_reference(self, ref):
        """Validate Spanish cadastral reference with control characters.

        Standard DGC references contain 20 alphanumeric characters.
        Last 2 characters are calculated from positions:
        - First control char: positions 1-7 + positions 15-18
        - Second control char: positions 8-14 + positions 15-18
        """
        if not ref or not re.fullmatch(r"[0-9A-ZÑ]{20}", ref):
            return False

        expected_control = self._calculate_control(ref)
        return ref[18:20] == expected_control

    @api.model
    def _calculate_control(self, ref):
        weights = [13, 15, 12, 5, 4, 17, 9, 21, 3, 7, 1]
        control_letters = "MQWERTYUIOPASDFGHJKLBZX"

        def char_value(c):
            if c.isdigit():
                return int(c)
            if c == "Ñ":
                return 15
            v = ord(c) - 64  # A=1..N=14
            return v if v <= 14 else v + 1  # O=16..Z=27 (saltar posición Ñ)

        def weighted_mod23(chain):
            return (
                sum(char_value(c) * w for c, w in zip(chain, weights, strict=False))
                % 23
            )

        first = ref[0:7] + ref[14:18]
        second = ref[7:14] + ref[14:18]
        return (
            control_letters[weighted_mod23(first)]
            + control_letters[weighted_mod23(second)]
        )
