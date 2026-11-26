# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError

SPFE_PROPERTY_SITUATIONS = [
    ("01", "[01] Inmueble con ref. catastral en España (excepto País Vasco y Navarra)"),
    ("02", "[02] Inmueble con ref. catastral en País Vasco o Navarra"),
    ("03", "[03] Inmueble sin referencia catastral"),
    ("04", "[04] Inmueble situado en el extranjero"),
]

SPFE_COLLECTION_LINE_TYPES = [
    ("SUPL", "[SUPL] Suplido / Cargo en nombre de un tercero"),
    ("MINO", "[MINO] Minoración en nombre de un tercero"),
    ("IEDMT", "[IEDMT] Impuesto Especial sobre Determinados Medios de Transporte"),
    ("OTROS", "[OTROS] Otras tasas o impuestos en nombre de un tercero"),
]


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    spfe_registration_key_id = fields.Many2one(
        comodel_name="l10n.es.spfe.registration.key",
        string="SPFE Regime Key",
        compute="_compute_spfe_registration_key_id",
        store=True,
        readonly=False,
        help="REGI: Regime key reported in SPFE AdditionalItemProperty.",
    )
    spfe_second_registration_key_id = fields.Many2one(
        comodel_name="l10n.es.spfe.registration.key",
        string="SPFE 2nd Regime Key",
    )
    spfe_real_estate_id = fields.Many2one(
        comodel_name="l10n.es.aeat.real_estate",
        string="AEAT Real Estate",
    )
    spfe_property_situation = fields.Selection(
        selection=SPFE_PROPERTY_SITUATIONS,
        string="SPFE Property Situation",
        help="Lista L6: Property location code for lease operations.",
    )
    spfe_cadastral_reference = fields.Char(
        string="SPFE Cadastral Reference",
        size=25,
        help="RCAT: Cadastral reference reported on leased property lines.",
    )
    spfe_line_info = fields.Char(
        string="SPFE Line Regulatory Info",
        help="INFO: Additional regulatory mention at invoice line level.",
    )
    spfe_collection_line_type = fields.Selection(
        selection=SPFE_COLLECTION_LINE_TYPES,
        string="SPFE Third-Party Collection Type",
        help="Lista L7: Disbursement or third-party collection line type.",
    )

    @api.depends("tax_ids", "move_id.fiscal_position_id")
    def _compute_spfe_registration_key_id(self):
        default_key = self.env.ref(
            "l10n_es_spfe.spfe_reg_key_iva_01", raise_if_not_found=False
        )
        for line in self:
            if line.display_type != "product":
                line.spfe_registration_key_id = False
                continue
            key = False
            for tax in line.tax_ids:
                if tax.spfe_registration_key_id:
                    key = tax.spfe_registration_key_id
                    break
            if not key and line.move_id.fiscal_position_id.spfe_registration_key_id:
                key = line.move_id.fiscal_position_id.spfe_registration_key_id
            line.spfe_registration_key_id = key or default_key

    def _get_spfe_split_taxes(self):
        """Return (main_vat_tax, surcharge_tax, withholding_taxes) for this line."""
        self.ensure_one()
        wth_taxes = self.tax_ids.filtered(
            lambda t: t.spfe_is_withholding or t.amount < 0
        )
        surcharge_taxes = self.tax_ids.filtered(lambda t: t.spfe_is_surcharge)
        vat_taxes = self.tax_ids - wth_taxes - surcharge_taxes
        if not vat_taxes:
            raise UserError(
                self.env._(
                    "Invoice line '%(line)s' must have one main VAT/IGIC/IPSI "
                    "tax configured for SPFE.",
                    line=self.name or self.id,
                )
            )
        return vat_taxes[0], surcharge_taxes[:1], wth_taxes

    def _get_spfe_effective_registration_keys(self):
        self.ensure_one()
        keys = self.spfe_registration_key_id
        if not keys:
            keys = self.env.ref(
                "l10n_es_spfe.spfe_reg_key_iva_01", raise_if_not_found=False
            )
        if (
            self.spfe_second_registration_key_id
            and self.spfe_second_registration_key_id != keys
        ):
            keys |= self.spfe_second_registration_key_id
        return keys

    def _get_spfe_real_estate_info(self):
        self.ensure_one()
        if self.spfe_property_situation:
            return self.spfe_cadastral_reference, self.spfe_property_situation
        if self.spfe_real_estate_id:
            re_rec = self.spfe_real_estate_id
            ref = re_rec.reference
            if re_rec.country_id and re_rec.country_id.code != "ES":
                return "-", "04"
            if not ref:
                return "-", "03"
            state_code = (re_rec.state_id.code or "").upper()
            foral_codes = (
                "NA",
                "VI",
                "SS",
                "BI",
                "ES-NA",
                "ES-VI",
                "ES-SS",
                "ES-BI",
            )
            if state_code in foral_codes:
                return ref, "02"
            return ref, "01"
        return False, False
