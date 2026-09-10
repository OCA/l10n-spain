# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import float_round

# Coeficiente legal art. 29.3 Ley 20/1991 (IGIC minoristas).
MINORISTA_COEFFICIENT_FACTOR = 0.7
ATC_VERIFACTU_TAX_KEY = "03"


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _get_atc_tax_agency(self):
        return self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )

    def _is_atc_verifactu_company(self):
        self.ensure_one()
        agency = self._get_atc_tax_agency()
        return bool(agency and self.company_id.tax_agency_id == agency)

    @api.depends("company_id", "company_id.tax_agency_id")
    def _compute_verifactu_tax_key(self):
        res = super()._compute_verifactu_tax_key()
        for document in self:
            if (
                document._is_atc_verifactu_company()
                and not document.fiscal_position_id.verifactu_tax_key
            ):
                document.verifactu_tax_key = ATC_VERIFACTU_TAX_KEY
        return res

    @api.depends("company_id", "company_id.tax_agency_id")
    def _compute_verifactu_registration_key(self):
        res = super()._compute_verifactu_registration_key()
        for document in self:
            if document.fiscal_position_id:
                continue
            if document._is_atc_verifactu_company():
                document.verifactu_registration_key = self.env[
                    "verifactu.registration.key"
                ].search(
                    [
                        ("code", "=", "01"),
                        ("verifactu_tax_key", "=", ATC_VERIFACTU_TAX_KEY),
                    ],
                    limit=1,
                )
        return res

    @api.model
    def _is_igic_minorista_sale_tax(self, tax):
        cmino_group = self.env.ref(
            "l10n_es_igic.tax_group_igic_cmino", raise_if_not_found=False
        )
        if not cmino_group:
            return False
        return (
            tax.type_tax_use == "sale"
            and tax.tax_group_id == cmino_group
            and tax.amount_type == "percent"
            and not tax.amount
        )

    def _get_igic_theoretical_sale_taxes_from_product(self, product):
        self.ensure_one()
        if not product:
            return self.env["account.tax"]
        cmino_group = self.env.ref("l10n_es_igic.tax_group_igic_cmino")
        return product.taxes_id.filtered(
            lambda tax: (
                tax.company_id == self.company_id
                and tax.type_tax_use == "sale"
                and tax.amount > 0
                and tax.amount_type == "percent"
                and tax.tax_group_id != cmino_group
            )
        )

    def _get_theoretical_percent_from_fp_mapping(self, inv_line, minorista_tax):
        self.ensure_one()
        fp = self.fiscal_position_id
        if not fp:
            return None
        mappings = fp.tax_ids.filtered(
            lambda mapping: (
                mapping.tax_dest_id == minorista_tax and mapping.tax_src_id.amount > 0
            )
        )
        if not mappings:
            return None
        product_taxes = self._get_igic_theoretical_sale_taxes_from_product(
            inv_line.product_id
        )
        if product_taxes:
            matched = mappings.filtered(
                lambda mapping: mapping.tax_src_id in product_taxes
            )
            if matched:
                return matched[0].tax_src_id.amount
        if len(mappings) == 1:
            return mappings.tax_src_id.amount
        return None

    def _get_igic_minorista_theoretical_percent(self, minorista_tax):
        self.ensure_one()
        invoice_lines = self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
            and minorista_tax in line.tax_ids
        )
        if not invoice_lines:
            raise UserError(
                _("No invoice line found for IGIC retailer tax %s.")
                % minorista_tax.display_name
            )
        theoretical_percents = []
        for line in invoice_lines:
            theoretical_taxes = self._get_igic_theoretical_sale_taxes_from_product(
                line.product_id
            )
            if len(theoretical_taxes) > 1:
                raise UserError(
                    _("Product %s has multiple IGIC sale taxes configured.")
                    % line.product_id.display_name
                )
            if theoretical_taxes:
                theoretical = theoretical_taxes.amount
            else:
                theoretical = self._get_theoretical_percent_from_fp_mapping(
                    line, minorista_tax
                )
            if theoretical is None:
                raise UserError(
                    _(
                        "Cannot determine theoretical IGIC rate for minorista "
                        "line '%(line)s'. Configure product '%(product)s' with "
                        "its usual IGIC sale tax (igic_r_*)."
                    )
                    % {
                        "line": line.name,
                        "product": line.product_id.display_name,
                    }
                )
            theoretical_percents.append(theoretical)
        unique_rates = set(theoretical_percents)
        if len(unique_rates) > 1:
            raise UserError(
                _(
                    "Minorista invoice '%(invoice)s' mixes theoretical IGIC "
                    "rates (%(rates)s). Use separate invoices."
                )
                % {
                    "invoice": self.display_name,
                    "rates": ", ".join(str(rate) for rate in sorted(unique_rates)),
                }
            )
        return unique_rates.pop()

    def _get_igic_minorista_implicit_coefficient(self, theoretical_percent):
        """Return purchase division percent (= 0,7 x T) from existing igic_sop_*_cmino."""
        self.ensure_one()
        expected = MINORISTA_COEFFICIENT_FACTOR * theoretical_percent
        cmino_group = self.env.ref("l10n_es_igic.tax_group_igic_cmino")
        purchase_taxes = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("type_tax_use", "=", "purchase"),
                ("amount_type", "=", "division"),
                ("tax_group_id", "=", cmino_group.id),
            ]
        )
        for tax in purchase_taxes:
            if abs(tax.amount - expected) < 0.011:
                return tax.amount
        raise UserError(
            _(
                "No IGIC retailer purchase tax found for theoretical rate "
                "%(rate)s%% (expected coefficient %(coef)s)."
            )
            % {"rate": theoretical_percent, "coef": expected}
        )

    def _get_verifactu_tax_dict(self, tax_line, tax_lines, *args, **kwargs):
        self.ensure_one()
        tax_dict = super()._get_verifactu_tax_dict(tax_line, tax_lines, *args, **kwargs)
        if self.verifactu_registration_key_code != "17":
            return tax_dict
        tax = tax_line["tax"]
        if not self._is_igic_minorista_sale_tax(tax):
            return tax_dict
        theoretical = self._get_igic_minorista_theoretical_percent(tax)
        self._get_igic_minorista_implicit_coefficient(theoretical)
        base = tax_line["base"]
        carga = float_round(
            base * MINORISTA_COEFFICIENT_FACTOR * theoretical / 100.0,
            precision_digits=2,
        )
        tax_dict["TipoImpositivo"] = str(float(theoretical))
        tax_dict["CargaImpositivaImplicitadeMinoristas"] = carga
        return tax_dict
