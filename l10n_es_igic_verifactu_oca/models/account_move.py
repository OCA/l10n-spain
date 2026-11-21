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

    def _get_verifactu_accepted_tax_agencies(self):
        return super()._get_verifactu_accepted_tax_agencies() + [
            "l10n_es_aeat.aeat_tax_agency_canarias",
        ]

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

    def _igic_repep_sale_taxes(self):
        """IGIC Exento Repercutido (igic_re_ex).

        Es el exento genérico. REPEP solo si la clave queda en 18.
        El arrendamiento usa el mismo impuesto y la posición fiscal pone 11 o 01.
        """
        self.ensure_one()
        tax = self.env.ref(
            f"account.{self.company_id.id}_account_tax_template_igic_re_ex",
            raise_if_not_found=False,
        )
        if not tax or tax.type_tax_use != "sale":
            return self.env["account.tax"]
        return tax

    def _has_igic_repep_sale_tax(self):
        self.ensure_one()
        return bool(self.invoice_line_ids.tax_ids & self._igic_repep_sale_taxes())

    def _is_igic_lease_fiscal_position(self):
        self.ensure_one()
        position = self.fiscal_position_id
        if not position:
            return False
        xmlid = position.get_external_id().get(position.id, "")
        return xmlid.endswith("fp_lease_canary")

    def _igic_export_sale_taxes(self):
        """IGIC 0% (Exportaciones): expedición fuera de Canarias.

        Art. 11 Ley 20/1991.
        """
        self.ensure_one()
        tax = self.env.ref(
            f"account.{self.company_id.id}_account_tax_template_igic_ex_0",
            raise_if_not_found=False,
        )
        if not tax or tax.type_tax_use != "sale":
            return self.env["account.tax"]
        return tax

    def _has_igic_export_sale_tax(self):
        self.ensure_one()
        return bool(self.invoice_line_ids.tax_ids & self._igic_export_sale_taxes())

    def _igic_repep_legend(self):
        """Texto impreso obligatorio en facturas de franquicia fiscal."""
        self.ensure_one()
        return (
            self.move_type in ("out_invoice", "out_refund")
            and self._is_atc_verifactu_company()
            and self.verifactu_registration_key_code == "18"
            and self._has_igic_repep_sale_tax()
        )

    @api.depends(
        "company_id",
        "company_id.tax_agency_id",
        "fiscal_position_id",
        "fiscal_position_id.verifactu_registration_key",
        "invoice_line_ids.tax_ids",
    )
    def _compute_verifactu_registration_key(self):
        res = super()._compute_verifactu_registration_key()
        key_18 = self.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_18",
            raise_if_not_found=False,
        )
        key_02 = self.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_02",
            raise_if_not_found=False,
        )
        for document in self:
            if document._is_igic_lease_fiscal_position():
                continue
            if (
                key_18
                and document.move_type in ("out_invoice", "out_refund")
                and document._is_atc_verifactu_company()
                and document._has_igic_repep_sale_tax()
            ):
                document.verifactu_registration_key = key_18
                continue
            if (
                key_02
                and document.move_type in ("out_invoice", "out_refund")
                and document._is_atc_verifactu_company()
                and document._has_igic_export_sale_tax()
            ):
                document.verifactu_registration_key = key_02
                continue
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
        company = tax.company_id or self.env.company
        cmino_group = self.env.ref(
            f"account.{company.id}_tax_group_igic_cmino", raise_if_not_found=False
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
        cmino_group = self.env.ref(f"account.{self.company_id.id}_tax_group_igic_cmino")
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

    def _get_theoretical_percent_from_product(self, product, minorista_tax):
        """Un solo impuesto de venta del grupo minorista. Si no, no hay tipo."""
        self.ensure_one()
        if not product:
            return None
        candidate_taxes = product.taxes_id.filtered(
            lambda tax: (
                tax.company_id == self.company_id
                and tax.type_tax_use == "sale"
                and tax.tax_group_id == minorista_tax.tax_group_id
            )
        )
        if len(candidate_taxes) != 1:
            return None
        return candidate_taxes.amount

    def _get_igic_minorista_theoretical_percent(self, minorista_tax):
        self.ensure_one()
        invoice_lines = self.invoice_line_ids.filtered(
            lambda line: (
                line.display_type == "product" and minorista_tax in line.tax_ids
            )
        )
        if not invoice_lines:
            raise UserError(
                _("No invoice line found for IGIC retailer tax %s.")
                % minorista_tax.display_name
            )
        theoretical_percents = []
        for line in invoice_lines:
            sale_taxes = self._get_igic_theoretical_sale_taxes_from_product(
                line.product_id
            )
            if len(sale_taxes) > 1:
                raise UserError(
                    _("Product %s has multiple IGIC sale taxes configured.")
                    % line.product_id.display_name
                )
            percents = {
                percent
                for percent in (
                    self._get_theoretical_percent_from_product(
                        line.product_id, minorista_tax
                    ),
                    self._get_theoretical_percent_from_fp_mapping(line, minorista_tax),
                )
                if percent is not None
            }
            # El IGIC del producto no vale solo: el impuesto por defecto del
            # plan (p. ej. IGIC 1%) no es un tipo teórico del minorista.
            # Sí invalida el resultado si no coincide con el mapeo.
            product_percent = sale_taxes.amount if len(sale_taxes) == 1 else None
            if (
                percents
                and product_percent is not None
                and product_percent not in percents
            ):
                percents.add(product_percent)
            if len(percents) != 1:
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
            theoretical_percents.append(percents.pop())
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
        """Return purchase division percent (0,7 x T) from existing igic_sop_*_cmino."""
        self.ensure_one()
        expected = MINORISTA_COEFFICIENT_FACTOR * theoretical_percent
        cmino_group = self.env.ref(f"account.{self.company_id.id}_tax_group_igic_cmino")
        purchase_taxes = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("type_tax_use", "=", "purchase"),
                ("amount_type", "in", ("division", "percent")),
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

    def _get_igic_verifactu_exempt_taxes_map(self):
        """IGIC taxes that must be reported as exempt, by exempt cause.

        17.0's ``l10n_es_verifactu_oca`` has no E-code map (see
        ``facts-17.0-verifactu.md`` F1/F6), so the mapping lives in the addon.
        """
        self.ensure_one()
        Tax = self.env["account.tax"]

        def _tax(name):
            return (
                self.env.ref(
                    f"account.{self.company_id.id}_{name}", raise_if_not_found=False
                )
                or Tax
            )

        return {
            "E1": _tax("account_tax_template_igic_cmino"),
            "E2": _tax("account_tax_template_igic_ex_0"),
            "E7": _tax("account_tax_template_igic_re_ex")
            | _tax("account_tax_template_igic_p_ex"),
        }

    def _get_verifactu_tax_dict(self, tax_line, tax_lines, *args, **kwargs):
        self.ensure_one()
        tax_dict = super()._get_verifactu_tax_dict(tax_line, tax_lines)
        operation_type = args[0] if args else kwargs.get("operation_type")
        tax = tax_line["tax"]
        # 17.0's base calls this as _get_verifactu_tax_dict(tax_line, tax_lines),
        # with no operation_type, so it always arrives None; the head's caller
        # passes "exempt" explicitly. Accept both, so the guard reads the head's
        # intent whether it is handed the head's value or 17.0's None.
        if operation_type in (None, "exempt"):
            exempt_groups = self._get_igic_verifactu_exempt_taxes_map()
            exempt_taxes = self.env["account.tax"]
            for taxes in exempt_groups.values():
                exempt_taxes |= taxes
            if tax in exempt_taxes:
                tax_dict.pop("CalificacionOperacion", None)
                tax_dict.pop("TipoImpositivo", None)
                tax_dict.pop("CuotaRepercutida", None)
                tax_dict["OperacionExenta"] = self._get_igic_verifactu_exempt_cause(
                    tax, exempt_groups
                )
                return tax_dict
        if self.verifactu_registration_key_code != "17":
            return tax_dict
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

    def _igic_lease_exemption(self):
        """Arrendamiento: la posición fiscal deja la clave 11 o 01 y la causa es E1."""
        self.ensure_one()
        if self.verifactu_registration_key_code == "18":
            return False
        if self._is_igic_lease_fiscal_position():
            return True
        return self.verifactu_registration_key_code in ("11", "01")

    def _get_igic_verifactu_exempt_cause(self, tax, exempt_groups):
        """E7 (REPEP) y E8 (otras) antes que E6. El módulo base no las distingue."""
        for code in ("E1", "E2", "E3", "E4", "E5", "E7", "E8", "E6"):
            if tax in exempt_groups.get(code, self.env["account.tax"]):
                if code == "E7" and self._igic_lease_exemption():
                    return "E1"
                return code
        return "E6"

    def _get_verifactu_taxes_map(self, codes, date):
        """Impuestos enlazados al mapa. Los equivalentes AEAT no cuentan.

        Copiar un impuesto rellena aeat_equivalent_tax_id con el original, y
        _get_taxes_from_xmlids lo devolvería como si estuviera mapeado. En 17.0
        el mapa enlaza por XML-ID, así que se resuelve cada clave directamente.
        """
        invoice = self[:1]
        if not invoice or not invoice._is_atc_verifactu_company():
            return super()._get_verifactu_taxes_map(codes, date)
        verifactu_map = invoice._get_verifactu_map(date)
        tax_xmlids = verifactu_map.map_lines.filtered(
            lambda line: line.code in codes
        ).tax_xmlid_ids.mapped("name")
        company = invoice.company_id
        tax_ids = [company._get_tax_id_from_xmlid(xmlid) for xmlid in tax_xmlids]
        return self.env["account.tax"].browse([tax_id for tax_id in tax_ids if tax_id])
