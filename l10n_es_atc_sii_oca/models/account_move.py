# Copyright 2025 Sistema de datos - Mario Montes
# Copyright 2025 Tecnativa - Sergio Teruel
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Claves a eliminar del payload SII en ATC (el esquema no incluye nodos RE estilo IVA).
_SII_ATC_DROP_KEYS = frozenset(
    {
        "TipoRecargoEquivalencia",
        "CuotaRecargoEquivalencia",
    }
)

_ATC_IMPORTE_TOTAL_TOLERANCE = 10.0
_ATC_SIMPLIFIED_INVOICE_LIMIT = 3000.0
_ATC_EXEMPT_EXPORT_CAUSES = frozenset({"E2", "E3"})
_ATC_REGIME_07_FORBIDDEN_EXEMPT = frozenset({"E2", "E3", "E4", "E5"})
_ATC_BI_FORBIDDEN_REGIMES = frozenset({"08", "18"})


class AccountMove(models.Model):
    _inherit = "account.move"

    sii_refund_type = fields.Selection(
        selection_add=[("S", "By substitution")],
    )
    # l10n_es_aeat_sii_oca (tipo S) sigue leyendo refund_invoice_id, pero en
    # Odoo 18 el enlace es reversed_entry_id y account_invoice_refund_link
    # solo expone refund_invoice_ids en la factura original. Hasta que el SII
    # base use reversed_entry_id, este alias computed mantiene ImporteRectificacion
    # sin duplicar lógica de payload ni choque de etiquetas con related.
    refund_invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Original invoice (SII substitution)",
        compute="_compute_refund_invoice_id",
    )

    @api.depends("reversed_entry_id")
    def _compute_refund_invoice_id(self):
        for move in self:
            move.refund_invoice_id = move.reversed_entry_id

    def _is_atc_sii_agency(self):
        self.ensure_one()
        canarias = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        return bool(canarias and self._get_sii_tax_agency() == canarias)

    # Ajustes de cabecera SII para la agencia tributaria canaria (ATC).
    def _get_aeat_header(self, tipo_comunicacion=False, cancellation=False):
        header = super()._get_aeat_header(
            tipo_comunicacion=tipo_comunicacion, cancellation=cancellation
        )
        if self._is_atc_sii_agency():
            header["IDVersionSii"] = "1.0" if self.company_id.sii_test else "1.1"
        return header

    def _get_sii_in_taxes(self):
        taxes_dict, tax_amount, not_in_amount_total = super()._get_sii_in_taxes()
        if not self._is_atc_sii_agency() or self.move_type[:2] != "in":
            return taxes_dict, tax_amount, not_in_amount_total
        return self._atc_patch_sfrbi_in_taxes(
            taxes_dict, tax_amount, not_in_amount_total
        )

    def _atc_patch_sfrbi_in_taxes(self, taxes_dict, tax_amount, not_in_amount_total):
        """Añade líneas IGIC SFRBI omitidas en el desglose genérico de compras."""
        self.ensure_one()
        taxes_sfrbi = self._get_aeat_taxes_map(["SFRBI"], self.date)
        if not taxes_sfrbi:
            return taxes_dict, tax_amount, not_in_amount_total
        base_dict = taxes_dict.setdefault("DesgloseIVA", {"DetalleIVA": []})
        detalle = base_dict["DetalleIVA"]
        tax_lines = self._get_aeat_tax_info()
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            if tax not in taxes_sfrbi:
                continue
            tax_dict = self._get_sii_tax_dict(tax_line, tax_lines)
            tax_dict["BienInversion"] = "S"
            if self._merge_tax_dict(
                detalle,
                tax_dict,
                ["TipoImpositivo", "BienInversion"],
                ["BaseImponible", "CuotaSoportada"],
            ):
                continue
            detalle.append(tax_dict)
            tax_amount += tax_line["deductible_amount"]
        return taxes_dict, tax_amount, not_in_amount_total

    @api.model
    def _sii_atc_replace_tax_keys(self, invoice_dic):
        """
        Sustituye recursivamente claves fiscales IVA→IGIC en estructuras anidadas.
        Solo se renombran coincidencias exactas de clave.
        """

        key_map = {
            "DetalleIVA": "DetalleIGIC",
            "DesgloseIVA": "DesgloseIGIC",
            "ImporteTransmisionInmueblesSujetoAIVA": (
                "ImporteTransmisionInmueblesSujetoAIGIC"
            ),
            "ImportePorArticulos7_14_Otros": "ImportePorArticulos9_Otros",
        }
        if isinstance(invoice_dic, dict):
            new_dict = {}
            for key, value in invoice_dic.items():
                if key in _SII_ATC_DROP_KEYS:
                    continue
                new_key = key_map.get(key, key)
                new_dict[new_key] = self._sii_atc_replace_tax_keys(value)
            return new_dict
        if isinstance(invoice_dic, list):
            return [self._sii_atc_replace_tax_keys(item) for item in invoice_dic]
        if isinstance(invoice_dic, tuple):
            return tuple(self._sii_atc_replace_tax_keys(item) for item in invoice_dic)
        return invoice_dic

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if cancel:
            return inv_dict
        if self._is_atc_sii_agency():
            inv_dict = self._sii_atc_replace_tax_keys(inv_dict)
        return inv_dict

    def _get_aeat_invoice_dict_in(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_in(cancel=cancel)
        if cancel:
            return inv_dict
        if self._is_atc_sii_agency():
            inv_dict = self._sii_atc_replace_tax_keys(inv_dict)
        return inv_dict

    def _get_aeat_taxes_map(self, codes, date):
        """Usa el mapa SII ATC para no quedar eclipsado por el mapa AEAT genérico."""
        self.ensure_one()
        atc_agency = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        tax_agency = self._get_sii_tax_agency()
        if atc_agency and tax_agency == atc_agency:
            map_model = self.env["aeat.sii.map"].sudo().with_context(active_test=False)
            domain = [
                "&",
                ("tax_agency_id", "=", atc_agency.id),
                "|",
                ("date_from", "<=", date),
                ("date_from", "=", False),
                "|",
                ("date_to", ">=", date),
                ("date_to", "=", False),
            ]
            sii_map = map_model.search(domain, limit=1)
            if sii_map:
                tax_templates = sii_map.map_lines.filtered(
                    lambda line: line.code in codes
                ).tax_xmlid_ids
                taxes = self.env["account.tax"]
                for template in tax_templates:
                    tax_id = self.company_id._get_tax_id_from_xmlid(template.name)
                    if tax_id:
                        taxes |= self.env["account.tax"].browse(tax_id)
                return taxes
        return super()._get_aeat_taxes_map(codes, date)

    def _get_sii_identifier(self):
        if self._is_atc_sii_agency():
            self = self.with_context(is_canary_tax_agency=True)
        return super()._get_sii_identifier()

    def _aeat_check_atc_local_rules(self):
        """Validaciones locales ATC antes del envío al SII."""
        self.ensure_one()
        self._aeat_check_simplified_limit()
        self._aeat_check_regime_01_exempt_export()
        self._aeat_check_regime_07()
        self._aeat_check_bien_inversion_regime()
        self._aeat_check_importe_total()

    def _aeat_check_exceptions(self):
        res = super()._aeat_check_exceptions()
        if (
            self._is_atc_sii_agency()
            and self.company_id.sii_enabled
            and self.is_invoice()
        ):
            self._aeat_check_atc_local_rules()
        return res

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for invoice in self.filtered(
            lambda x: x._is_atc_sii_agency()
            and x.is_invoice()
            and x.company_id.sii_enabled
            and not x.sii_enabled
        ):
            invoice._aeat_check_atc_local_rules()
        return res

    def _aeat_check_simplified_limit(self):
        """Impide facturas simplificadas (F2) por encima del límite ATC."""
        self.ensure_one()
        if self.move_type not in ("out_invoice",):
            return
        if self._get_sii_invoice_type() != "F2":
            return
        amount = abs(self._get_document_amount_total())
        if amount > _ATC_SIMPLIFIED_INVOICE_LIMIT:
            raise UserError(
                self.env._(
                    "Simplified invoice type F2 cannot exceed 3,000 € for the "
                    "Canary Islands SII (ATC). Amount: %(amount)s",
                    amount=amount,
                )
            )

    def _aeat_check_regime_01_exempt_export(self):
        """Error ATC 1295: exenciones exportación E2/E3 exigen clave de régimen 02."""
        self.ensure_one()
        if (
            not self.move_type.startswith("out_")
            or self.sii_registration_key.code != "01"
        ):
            return
        for line in self.invoice_line_ids:
            cause = line.product_id.product_tmpl_id.sii_exempt_cause
            if cause in _ATC_EXEMPT_EXPORT_CAUSES:
                raise UserError(
                    self.env._(
                        "ATC error 1295: exemption cause %(cause)s is not compatible "
                        "with registration key 01. Use key 02 for exports.",
                        cause=cause,
                    )
                )
        fp_cause = self.fiscal_position_id.sii_exempt_cause
        if fp_cause in _ATC_EXEMPT_EXPORT_CAUSES:
            raise UserError(
                self.env._(
                    "ATC error 1295: exemption cause %(cause)s is not compatible "
                    "with registration key 01. Use key 02 for exports.",
                    cause=fp_cause,
                )
            )
        if self._get_sii_gen_type() == 3:
            exempt_taxes = self._get_aeat_taxes_map(["SFESSE", "SFESBE"], self.date)
            if any(
                tax in exempt_taxes
                for line in self.invoice_line_ids
                for tax in line.tax_ids
            ):
                raise UserError(
                    self.env._(
                        "ATC error 1295: export operations cannot use registration "
                        "key 01. Use key 02 for exports."
                    )
                )

    def _aeat_check_regime_07(self):
        """Criterio de caja (07) incompatible con ISP y causas exentas E2–E5."""
        self.ensure_one()
        if (
            not self.move_type.startswith("out_")
            or self.sii_registration_key.code != "07"
        ):
            return
        isp_taxes = self._get_aeat_taxes_map(["SFESISP"], self.date)
        if isp_taxes and any(
            tax in isp_taxes for line in self.invoice_line_ids for tax in line.tax_ids
        ):
            raise UserError(
                self.env._(
                    "Registration key 07 (cash criterion) is not compatible "
                    "with reverse charge (ISP) operations."
                )
            )
        factura = self._atc_get_invoice_section("out")
        for no_exenta in self._atc_walk_nodes(factura, "NoExenta"):
            if no_exenta.get("TipoNoExenta") in ("S2", "S3"):
                raise UserError(
                    self.env._(
                        "Registration key 07 (cash criterion) is not compatible "
                        "with reverse charge type %(tipo)s.",
                        tipo=no_exenta.get("TipoNoExenta"),
                    )
                )
        exempt_taxes = self._get_aeat_taxes_map(["SFESSE", "SFESBE"], self.date)
        if exempt_taxes:
            exempt_cause = self._get_sii_exempt_cause(exempt_taxes)
            if exempt_cause in _ATC_REGIME_07_FORBIDDEN_EXEMPT:
                raise UserError(
                    self.env._(
                        "Registration key 07 (cash criterion) is not compatible "
                        "with exemption cause %(cause)s.",
                        cause=exempt_cause,
                    )
                )

    def _aeat_check_bien_inversion_regime(self):
        """Error ATC 1349: BienInversion con clave de régimen 08 o 18."""
        self.ensure_one()
        if not self.move_type.startswith("in_"):
            return
        reg = self.sii_registration_key.code
        if reg not in _ATC_BI_FORBIDDEN_REGIMES:
            return
        factura = self._atc_get_invoice_section("in")
        for detalle in self._atc_walk_nodes(factura, "DetalleIGIC"):
            if detalle.get("BienInversion") == "S":
                raise UserError(
                    self.env._(
                        "ATC error 1349: investment goods (BienInversion = S) is not "
                        "compatible with registration key %(reg)s.",
                        reg=reg,
                    )
                )

    def _aeat_check_importe_total(self):
        """Error ATC 2042: ImporteTotal debe cuadrar con el desglose IGIC."""
        self.ensure_one()
        if self.move_type.startswith("out_"):
            factura = self._atc_get_invoice_section("out")
            cuota_keys = ("CuotaRepercutida",)
        elif self.move_type.startswith("in_"):
            factura = self._atc_get_invoice_section("in")
            cuota_keys = ("CuotaSoportada",)
        else:
            return
        igic_details = []
        for detail_key in ("DetalleIGIC", "DetalleIVA"):
            igic_details.extend(self._atc_walk_nodes(factura, detail_key))
        if not any(
            float(d.get("CuotaRepercutida", 0) or d.get("CuotaSoportada", 0))
            for d in igic_details
        ):
            return
        importe_total = abs(float(factura.get("ImporteTotal", 0)))
        expected = self._atc_compute_breakdown_total(factura, cuota_keys)
        if expected is None:
            return
        if abs(importe_total - abs(expected)) > _ATC_IMPORTE_TOTAL_TOLERANCE:
            raise UserError(
                self.env._(
                    "ATC error 2042: ImporteTotal (%(total)s) does not match the "
                    "IGIC breakdown (%(expected)s) within ±%(tol)s €.",
                    total=importe_total,
                    expected=expected,
                    tol=_ATC_IMPORTE_TOTAL_TOLERANCE,
                )
            )

    def _atc_get_invoice_section(self, direction):
        self.ensure_one()
        if direction == "out":
            inv_dict = self._get_aeat_invoice_dict_out()
            if "SuministroLRFacturasEmitidas" in inv_dict:
                return inv_dict["SuministroLRFacturasEmitidas"][
                    "RegistroLRFacturasEmitidas"
                ]["FacturaExpedida"]
            return inv_dict["FacturaExpedida"]
        inv_dict = self._get_aeat_invoice_dict_in()
        if "SuministroLRFacturasRecibidas" in inv_dict:
            return inv_dict["SuministroLRFacturasRecibidas"][
                "RegistroLRFacturasRecibidas"
            ]["FacturaRecibida"]
        return inv_dict["FacturaRecibida"]

    @api.model
    def _atc_walk_nodes(self, node, key):
        found = []

        def walk(item):
            if isinstance(item, dict):
                if key in item:
                    value = item[key]
                    if isinstance(value, list):
                        found.extend(value)
                    elif isinstance(value, dict):
                        found.append(value)
                for value in item.values():
                    walk(value)
            elif isinstance(item, list):
                for sub in item:
                    walk(sub)

        walk(node)
        return found

    def _atc_compute_breakdown_total(self, factura, primary_cuota_keys):
        total = 0.0
        detail_count = 0
        extra_cuota_keys = (
            "CuotaAIEM",
            "CargaImpositivaImplicita",
            "CuotaRecargoMinorista",
        )
        for detail_key in ("DetalleIGIC", "DetalleIVA"):
            for detalle in self._atc_walk_nodes(factura, detail_key):
                detail_count += 1
                total += float(detalle.get("BaseImponible", 0))
                for key in primary_cuota_keys + extra_cuota_keys:
                    total += float(detalle.get(key, 0))
        for detalle in self._atc_walk_nodes(factura, "DetalleExenta"):
            detail_count += 1
            total += float(detalle.get("BaseImponible", 0))
        for block in self._atc_walk_nodes(factura, "NoSujeta"):
            for key, value in block.items():
                if key.startswith("Importe"):
                    detail_count += 1
                    total += float(value)
        if not detail_count:
            return None
        return total
