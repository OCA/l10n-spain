# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    spfe_enabled = fields.Boolean(
        string="SPFE Enabled",
        tracking=True,
        help="Enable AEAT Public Electronic Invoicing Solution (SPFE).",
    )
    spfe_test = fields.Boolean(
        string="SPFE Test Environment (PRE)",
        default=True,
        tracking=True,
        help="Send SPFE requests to AEAT pre-production (PRE) endpoints.",
    )
    spfe_use_seal_certificate = fields.Boolean(
        string="Use Electronic Seal Certificate",
        default=False,
        help="Connect using Electronic Seal ports (prewww10/www10) instead of "
        "personal/representative certificate ports (prewww1/www1).",
    )
    spfe_auto_send = fields.Boolean(
        string="Send Automatically on Invoice Post",
        default=False,
        help="Queue customer invoices for automatic SPFE submission via cron.",
    )
    spfe_auto_send_payment = fields.Boolean(
        string="Auto-Send Full Collection / Payment to SPFE",
        default=True,
        tracking=True,
        help="Automatically communicate full invoice collection (SETTLEMENT) "
        "and full bill payment (PAYMENT) to AEAT SPFE via scheduled action.",
    )
    spfe_start_date = fields.Date(
        string="SPFE Start Date",
        default="2026-10-06",
        help="Minimum invoice issue date eligible for SPFE (Orden HAC/1028/2026 "
        "entry into force: 2026-10-06).",
    )
    spfe_sender_vat = fields.Char(
        string="SPFE Sender Certificate NIF",
        help="Optional NIF of the certificate holder (Social Collaborator or "
        "Representative) for ebMS From/PartyId. Defaults to the company NIF.",
    )
    spfe_company_legal_form = fields.Char(
        string="SPFE Mercantile / Legal Information",
        help="BT-33: Additional legal or commercial registry information included in "
        "PartyLegalEntity/CompanyLegalForm.",
    )
    spfe_third_party_issuer_id = fields.Many2one(
        comodel_name="res.partner",
        string="SPFE Third-Party Issuer",
        help="BG-ES-1: Third party materially issuing invoices on behalf of the "
        "company (art. 5 RD 1619/2012, FacturaciónPorTercero).",
    )
    spfe_billing_authorization_ref = fields.Char(
        string="SPFE Billing Authorization Ref.",
        help="AUT: Reference number of special billing authorization granted by AEAT.",
    )
    spfe_billing_authorization_desc = fields.Char(
        string="SPFE Billing Authorization Description",
    )

    def write(self, vals):
        res = super().write(vals)
        if vals.get("spfe_enabled"):
            self.env["account.journal"].sudo().search(
                [
                    ("company_id", "in", self.ids),
                    ("type", "in", ("sale", "purchase")),
                ]
            ).spfe_enabled = True
            self._configure_spfe_spanish_taxes()
        return res

    def _get_spfe_tax_agency(self):
        self.ensure_one()
        return self.tax_agency_id or self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")

    def _get_spfe_sender_party_id(self):
        self.ensure_one()
        if self.spfe_sender_vat:
            return self.spfe_sender_vat.strip().upper()
        _country, _id_type, nif = self.partner_id._parse_aeat_vat_info()
        return (nif or self.vat or "").strip().upper()

    def _get_spfe_legal_form_text(self):
        self.ensure_one()
        if self.spfe_company_legal_form:
            return self.spfe_company_legal_form
        partner = self.partner_id
        if hasattr(partner, "es_registro_mercantil") and partner.es_registro_mercantil:
            parts = [f"R.M. {partner.es_registro_mercantil}"]
            for label, attr in (
                ("Tomo", "es_tomo"),
                ("Libro", "es_libro"),
                ("Folio", "es_folio"),
                ("Sección", "es_seccion"),
                ("Hoja", "es_hoja"),
            ):
                val = getattr(partner, attr, False)
                if val:
                    parts.append(f"{label} {val}")
            return ", ".join(parts)
        return False

    def action_configure_spfe_spanish_taxes(self):
        self._configure_spfe_spanish_taxes()
        return True

    def _get_spfe_unece_refs(self):
        xmlids = {
            "vat": "account_tax_unece.tax_type_vat",
            "wth": "l10n_es_spfe.tax_type_wth",
            "S": "account_tax_unece.tax_categ_s",
            "Z": "account_tax_unece.tax_categ_z",
            "E": "account_tax_unece.tax_categ_e",
            "AE": "account_tax_unece.tax_categ_ae",
            "O": "account_tax_unece.tax_categ_o",
            "G": "account_tax_unece.tax_categ_g",
            "L": "account_tax_unece.tax_categ_l",
            "N": "l10n_es_spfe.tax_categ_n",
            "vx_iva20": "l10n_es_spfe.tax_vatex_es_iva20",
            "vx_iva22": "l10n_es_spfe.tax_vatex_es_iva22",
            "vx_iva23_24": "l10n_es_spfe.tax_vatex_es_iva23_24",
            "vx_otros": "l10n_es_spfe.tax_vatex_es_otros",
            "vx_ic": "account_tax_unece.tax_vatex_eu_ic",
            "vx_ae": "account_tax_unece.tax_vatex_eu_ae",
            "vx_g": "account_tax_unece.tax_vatex_eu_g",
            "vx_n1": "l10n_es_spfe.tax_vatex_es_n1",
            "vx_n2": "l10n_es_spfe.tax_vatex_es_n2",
            "reg_iva_01": "l10n_es_spfe.spfe_reg_key_iva_01",
            "reg_iva_02": "l10n_es_spfe.spfe_reg_key_iva_02",
            "reg_igic_01": "l10n_es_spfe.spfe_reg_key_igic_01",
        }
        return {
            k: self.env.ref(xid, raise_if_not_found=False) for k, xid in xmlids.items()
        }

    def _spfe_withholding_vals_for_tax(self, tax, desc_low, refs):
        vals = {"spfe_is_withholding": True}
        if not tax.spfe_withholding_type:
            rules = (
                (("arrend", "alquiler", "115"), "06"),
                (("agr", "ganad"), "02"),
                (("forest",), "03"),
                (("modul", "empresar"), "04"),
            )
            wtype = "01"
            for keywords, code in rules:
                if any(kw in desc_low for kw in keywords):
                    wtype = code
                    break
            vals["spfe_withholding_type"] = wtype
        if refs["wth"] and not tax.unece_type_id:
            vals["unece_type_id"] = refs["wth"].id
        if refs["S"] and not tax.unece_categ_id:
            vals["unece_categ_id"] = refs["S"].id
        return vals

    def _spfe_zero_vat_categ_and_vatex(self, tax, refs):
        if tax.l10n_es_type == "sujeto_isp":
            return refs["AE"], refs["vx_ae"]
        if tax.l10n_es_type == "no_sujeto":
            return refs["O"], refs["vx_n1"]
        if tax.l10n_es_type == "no_sujeto_loc":
            return refs["O"], refs["vx_n2"]
        if tax.l10n_es_type == "exento":
            return {
                "E1": (refs["E"], refs["vx_iva20"]),
                "E2": (refs["G"], refs["vx_g"]),
                "E3": (refs["E"], refs["vx_iva22"]),
                "E4": (refs["E"], refs["vx_iva23_24"]),
                "E5": (refs["E"], refs["vx_ic"]),
            }.get(tax.l10n_es_exempt_reason, (refs["E"], refs["vx_otros"]))
        return refs["Z"], False

    def _spfe_vat_vals_for_tax(self, tax, desc_low, refs):
        vals = {}
        if refs["vat"] and not tax.unece_type_id:
            vals["unece_type_id"] = refs["vat"].id
        is_igic = "igic" in desc_low
        if not tax.unece_categ_id:
            if tax.amount > 0:
                cat = refs["L"] if is_igic else refs["S"]
                if cat:
                    vals["unece_categ_id"] = cat.id
            else:
                cat, vx = self._spfe_zero_vat_categ_and_vatex(tax, refs)
                if cat:
                    vals["unece_categ_id"] = cat.id
                if vx and not tax.unece_vatex_id:
                    vals["unece_vatex_id"] = vx.id
        if not tax.spfe_registration_key_id:
            reg_key = (
                refs["reg_iva_02"]
                if tax.l10n_es_exempt_reason == "E2"
                else (refs["reg_igic_01"] if is_igic else refs["reg_iva_01"])
            )
            if reg_key:
                vals["spfe_registration_key_id"] = reg_key.id
        return vals

    def _configure_spfe_spanish_taxes(self):
        """Populate default UNECE and SPFE fields on standard Spanish taxes."""
        refs = self._get_spfe_unece_refs()
        taxes = (
            self.env["account.tax"]
            .sudo()
            .search([("company_id", "in", self.ids), ("amount_type", "=", "percent")])
        )
        for tax in taxes:
            desc_low = f"{tax.name or ''} {tax.description or ''}".lower()
            is_surcharge = tax.l10n_es_type == "recargo"
            if tax.l10n_es_type == "retencion":
                vals = self._spfe_withholding_vals_for_tax(tax, desc_low, refs)
            elif is_surcharge:
                vals = {"spfe_is_surcharge": True}
                if refs["vat"] and not tax.unece_type_id:
                    vals["unece_type_id"] = refs["vat"].id
                if refs["N"] and not tax.unece_categ_id:
                    vals["unece_categ_id"] = refs["N"].id
            else:
                vals = self._spfe_vat_vals_for_tax(tax, desc_low, refs)
            if vals:
                tax.write(vals)
