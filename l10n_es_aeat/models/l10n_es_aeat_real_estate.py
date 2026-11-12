# Copyright 2025 Netkia - Carlos Sainz-Pardo
# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL

from .aeat_address_types import AEAT_ADDRESS_TYPES

# Provinces with their own cadastre: Basque Country and Navarre
FORAL_STATE_CODES = ("BI", "NA", "SS", "VI")
# Situation of the model 180 list in the one of the SII (L6) and the model 347
SITUATION_180_TO_SII_347 = {"1": "1", "2": "2", "3": "2", "4": "3"}


class L10nEsAeatRealEstate(models.Model):
    _name = "l10n.es.aeat.real_estate"
    _inherit = ["mail.thread", "mail.activity.mixin"]  # noqa: RUF012
    _description = "Real Estates for AEAT"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda s: s.env.company,
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        help="Partner that owns this real estate",
    )
    owned_by_company = fields.Boolean(
        compute="_compute_owned_by_company",
        compute_sql="_compute_sql_owned_by_company",
        compute_sudo=True,
        help="The owner of the real estate is its company, as the premises it "
        "leases to the partner of an invoice.",
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
        selection="_selection_address_type",
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
        default=lambda self: self.env.ref("base.es"),
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
    )
    city = fields.Char(
        size=30,
        required=True,
    )
    zip = fields.Char(
        size=5,
        readonly=False,
        required=True,
    )
    municipality = fields.Char(
        size=30,
        help="Name of the municipality, when the city is a locality of another "
        "one. The models 180 and 347 take the city when it is empty.",
    )
    municipality_code = fields.Char(
        string="INE Municipality Code",
        size=5,
        help="Code of the municipality given by the Spanish National "
        "Statistics Institute (INE), as the models 180 and 347 ask: the two "
        "digits of the province and the three of the municipality.",
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
        [
            ("1", "01 - Spain except Basque Country and Navarre, with reference"),
            ("2", "02 - Basque Country, with cadastral reference"),
            ("3", "03 - Navarre, with cadastral reference"),
            ("4", "04 - Without cadastral reference"),
        ],
        compute="_compute_real_estate_situation",
        store=True,
        readonly=False,
        help="Situation of the real estate in the list of the model 180.",
    )

    @api.model
    def _selection_address_type(self):
        # Their names are already given in the co-official languages: a method
        # keeps these hundreds of terms out of the translations
        return AEAT_ADDRESS_TYPES

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

    @api.depends("partner_id", "company_id.partner_id")
    def _compute_owned_by_company(self):
        for rec in self:
            rec.owned_by_company = rec.partner_id == rec.company_id.partner_id

    def _compute_sql_owned_by_company(self, table):
        # The same comparison in SQL, so searching the field gives what it shows
        return SQL("%s = %s", table.partner_id, table.company_id.partner_id)

    @api.constrains("municipality_code", "zip", "country_id")
    def _check_municipality_code(self):
        for record in self:
            code = record.municipality_code
            if not code or not record._is_in_spain():
                continue
            if not re.fullmatch(r"\d{5}", code):
                raise ValidationError(
                    self.env._(
                        "The INE municipality code '%s' must have 5 digits.", code
                    )
                )
            if record.zip and record.zip[:2] != code[:2]:
                raise ValidationError(
                    self.env._(
                        "The INE municipality code '%(code)s' does not belong "
                        "to the province of the zip %(zip)s.",
                        code=code,
                        zip=record.zip,
                    )
                )

    @api.depends("partner_id.vat")
    def _compute_representative_vat(self):
        for record in self:
            record.representative_vat = record.partner_id.vat

    @api.depends("state_id")
    def _compute_check_ok(self):
        self.update({"check_ok": False, "error_text": False})
        for record in self:
            errors = []
            if not record.state_id:
                errors.append(self.env._("Without state"))
            record.check_ok = not bool(errors)
            record.error_text = bool(errors) and ", ".join(errors)

    def _is_in_spain(self):
        self.ensure_one()
        return not self.country_id or self.country_id.code == "ES"

    def _get_sii_347_situation(self):
        """Situation in the list of the SII (L6) and the model 347, which
        joins the Basque Country and Navarre and adds the real estates abroad,
        taken from the situation of the model 180 so a manual one is kept."""
        self.ensure_one()
        if not self._is_in_spain():
            return "4"
        return SITUATION_180_TO_SII_347.get(self.real_estate_situation, "3")

    def _get_aeat_location(self):
        """Locality, municipality, INE municipality code, province code and zip
        of the address of the models 180 and 347. The locality is only given
        when it is not the municipality, and the province is the numeric code
        of the INE, not the code of the state."""
        self.ensure_one()
        municipality = self.municipality or self.city or ""
        in_spain = self._is_in_spain()
        return {
            "locality": self.city if self.city != municipality else "",
            "municipality": municipality,
            "municipality_code": self.municipality_code or "",
            "province_code": (
                (self.municipality_code or self.zip or "")[:2] if in_spain else ""
            ),
            "zip": self.zip or "",
        }

    def _has_dgc_reference(self):
        """The cadastral reference is given by the Spanish General Directorate
        of the Cadastre (DGC), with its control characters, except in the
        provinces with their own cadastre and abroad."""
        self.ensure_one()
        return self._is_in_spain() and self.state_id.code not in FORAL_STATE_CODES

    @api.constrains("reference", "country_id", "state_id")
    def _check_reference(self):
        for record in self:
            ref = record.reference
            if not ref or not record._has_dgc_reference():
                continue

            ref = self._normalize_reference(ref)
            if not self._is_valid_reference(ref):
                raise ValidationError(
                    self.env._(
                        "The cadastral reference '%(reference)s' is not valid.",
                        reference=record.reference,
                    )
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
