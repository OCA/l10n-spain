# Copyright 2025 Sistema de datos - Mario Montes
# Copyright 2025 Tecnativa - Sergio Teruel
import logging
import re

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

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
_ATC_ART25_PURCHASE_KEY = "17"
_ATC_ART25_SALE_KEY = "19"
# Claves compra ATC que no admiten CuotaSoportada / CuotaDeducible (REPEP, Art.25…).
_ATC_NO_CUOTA_PURCHASE_KEYS = frozenset({"08", "16", "17", "18"})
# Plantillas IGIC compra exenta: DesgloseIGIC solo con BaseImponible.
_ATC_PURCHASE_EXEMPT_TAX_TEMPLATES = ("account_tax_template_igic_p_ex",)
# 1281: si la única clave es una de estas, el desglose solo puede ser Sujeta/Exenta.
_ATC_EXEMPT_ONLY_REGIMES = frozenset({"02", "17", "18", "19"})
_ATC_DUA_INVOICE_TYPES = frozenset({"F5", "LC"})
# igic_sop_7_cmino: el amount del impuesto es el 70 %; el SII pide el tipo nominal.
_ATC_CMINO_RATE = re.compile(r"igic_sop_(?:i_)?(\d+(?:_\d+)?)_cmino$")


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

    sii_operation_date = fields.Date(
        string="SII operation date",
        copy=False,
        help="Required for ATC registration key 14 (public works certification). "
        "Must be later than the invoice date (FechaExpedicionFacturaEmisor). "
        "Enter the real certification / devengo date.",
    )
    sii_art25_required = fields.Boolean(
        compute="_compute_sii_art25_required",
    )
    sii_art25_prepayment = fields.Selection(
        string="Art. 25 prepayment",
        selection=[("S", "Yes"), ("N", "No")],
        copy=False,
        help="ATC Lista L31 (PagoAnticipadoArt25) for REF Art. 25 investment goods.",
    )
    sii_art25_document_id = fields.Selection(
        string="Art. 25 document type",
        selection=[
            ("01", "[01] Notarial deed"),
            ("02", "[02] Private document"),
            ("03", "[03] Other"),
        ],
        copy=False,
        help="ATC Lista L33 (IDDocumentoArt25).",
    )
    sii_art25_protocol_number = fields.Char(
        string="Art. 25 protocol number",
        copy=False,
    )
    sii_art25_notary_name = fields.Char(
        string="Art. 25 notary full name",
        copy=False,
    )

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
            # ATC admite solo 1.0 (test y producción); 1.1 provoca error 4100.
            header["IDVersionSii"] = "1.0"
        return header

    def _get_sii_in_taxes(self):
        taxes_dict, tax_amount, not_in_amount_total = super()._get_sii_in_taxes()
        if not self._is_atc_sii_agency() or self.move_type[:2] != "in":
            return taxes_dict, tax_amount, not_in_amount_total
        taxes_dict, tax_amount, not_in_amount_total = self._atc_patch_sfrbi_in_taxes(
            taxes_dict, tax_amount, not_in_amount_total
        )
        taxes_dict, tax_amount = self._atc_patch_exempt_purchase_in_taxes(
            taxes_dict, tax_amount
        )
        taxes_dict, tax_amount, not_in_amount_total = self._atc_patch_dua_in_taxes(
            taxes_dict, tax_amount, not_in_amount_total
        )
        # *_retail / *_retail_inv: la cuota va en el gasto o el activo.
        tax_amount -= self._atc_retail_nondeductible_amount()
        return taxes_dict, tax_amount, not_in_amount_total

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

    def _atc_purchase_exempt_taxes(self):
        """Impuestos IGIC de compra exenta (p.ej. EXENTO S / igic_p_ex)."""
        self.ensure_one()
        taxes = self.env["account.tax"]
        for template_name in _ATC_PURCHASE_EXEMPT_TAX_TEMPLATES:
            tax_id = self.company_id._get_tax_id_from_xmlid(template_name)
            if tax_id:
                taxes |= self.env["account.tax"].browse(tax_id)
        return taxes

    def _atc_patch_exempt_purchase_in_taxes(self, taxes_dict, tax_amount):
        """ATC compras exentas: solo BaseImponible (sin Tipo/Cuota; 1322/1325).

        El mapa SFRS incluye ``igic_p_ex`` para evitar DesgloseFactura vacío (1157).
        El builder genérico emite TipoImpositivo/CuotaSoportada a 0; aquí se omiten.
        """
        self.ensure_one()
        exempt_taxes = self._atc_purchase_exempt_taxes()
        if not exempt_taxes:
            return taxes_dict, tax_amount
        tax_lines = self._get_aeat_tax_info()
        exempt_lines = [
            tax_line
            for tax_line in tax_lines.values()
            if tax_line["tax"] in exempt_taxes
        ]
        if not exempt_lines:
            return taxes_dict, tax_amount
        base_dict = taxes_dict.setdefault("DesgloseIVA", {"DetalleIVA": []})
        detalle = base_dict["DetalleIVA"]
        for tax_line in exempt_lines:
            tax_dict = self._get_sii_tax_dict(tax_line, tax_lines)
            base_val = tax_dict.get("BaseImponible")
            matched = False
            for idx, detail in enumerate(detalle):
                if abs(float(detail.get("BaseImponible", 0)) - float(base_val or 0)) > (
                    0.01
                ):
                    continue
                # Misma base: o es la línea 0% del genérico, o ya estaba strippeada.
                tipo = detail.get("TipoImpositivo")
                if tipo is not None and abs(float(tipo)) > 0.01:
                    continue
                stripped = {"BaseImponible": detail["BaseImponible"]}
                if detail.get("BienInversion"):
                    stripped["BienInversion"] = detail["BienInversion"]
                detalle[idx] = stripped
                matched = True
                break
            if not matched:
                detalle.append({"BaseImponible": base_val})
            else:
                # Super (SFRS) ya sumó deductible_amount; exento no debe aportar.
                tax_amount -= tax_line.get("deductible_amount") or 0.0
        return taxes_dict, tax_amount

    def _atc_tax_template_name(self, tax):
        """Sufijo de plantilla, p.ej. ``igic_sop_7_cmino``."""
        self.ensure_one()
        data = (
            self.env["ir.model.data"]
            .sudo()
            .search([("model", "=", "account.tax"), ("res_id", "=", tax.id)], limit=1)
        )
        name = data.name or ""
        prefix = f"{self.company_id.id}_"
        if name.startswith(prefix):
            name = name[len(prefix) :]
        template_prefix = "account_tax_template_"
        if name.startswith(template_prefix):
            name = name[len(template_prefix) :]
        return name

    def _atc_cmino_nominal_rate(self, tax):
        """Tipo nominal de ``igic_sop_*_cmino``. None si no aplica."""
        match = _ATC_CMINO_RATE.search(self._atc_tax_template_name(tax))
        if not match:
            return None
        return float(match.group(1).replace("_", "."))

    def _atc_is_retail_nondeductible(self, tax):
        """Cuota integrada en gasto o activo (``*_retail`` y ``*_retail_inv``)."""
        return "_retail" in self._atc_tax_template_name(tax)

    def _atc_retail_nondeductible_amount(self):
        self.ensure_one()
        total = 0.0
        for tax_line in self._get_aeat_tax_info().values():
            if self._atc_is_retail_nondeductible(tax_line["tax"]):
                total += tax_line.get("deductible_amount") or 0.0
        return total

    def _atc_patch_dua_in_taxes(self, taxes_dict, tax_amount, not_in_amount_total):
        """Incluye impuestos DUA que el desglose genérico no clasifica (error 1157).

        Los que ya están en SFRS/SFRBI/SFRISP no se duplican. No van a ISP:
        F5 y LC no admiten ``InversionSujetoPasivo`` (1339/1340).
        """
        self.ensure_one()
        taxes_dua = self._get_aeat_taxes_map(["DUA"], self.date)
        if not taxes_dua:
            return taxes_dict, tax_amount, not_in_amount_total
        already = self.env["account.tax"]
        for code in ("SFRS", "SFRBI", "SFRISP", "SFRNS"):
            already |= self._get_aeat_taxes_map([code], self.date)
        tax_lines = self._get_aeat_tax_info()
        pending = [
            tax_line
            for tax_line in tax_lines.values()
            if tax_line["tax"] in taxes_dua and tax_line["tax"] not in already
        ]
        if not pending:
            return taxes_dict, tax_amount, not_in_amount_total
        base_dict = taxes_dict.setdefault("DesgloseIVA", {"DetalleIVA": []})
        detalle = base_dict["DetalleIVA"]
        for tax_line in pending:
            tax_dict = self._get_sii_tax_dict(tax_line, tax_lines)
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

    def _get_sii_tax_dict(self, tax_line, tax_lines):
        tax_dict = super()._get_sii_tax_dict(tax_line, tax_lines)
        if not self._is_atc_sii_agency() or self.move_type[:2] != "in":
            return tax_dict
        nominal = self._atc_cmino_nominal_rate(tax_line["tax"])
        if nominal is None:
            return tax_dict
        # El impuesto ya trae el 70 % deducible; el SII pide el tipo nominal y la CII.
        tax_dict["TipoImpositivo"] = nominal
        tax_dict["CuotaSoportada"] = tax_line["amount"]
        tax_dict["CargaImpositivaImplicita"] = tax_line["amount"]
        return tax_dict

    def _merge_tax_dict(self, vat_list, tax_dict, comp_keys, merge_keys):
        merge_keys = list(merge_keys)
        if (
            tax_dict.get("CargaImpositivaImplicita") is not None
            and "CargaImpositivaImplicita" not in merge_keys
        ):
            merge_keys.append("CargaImpositivaImplicita")
        return super()._merge_tax_dict(vat_list, tax_dict, comp_keys, merge_keys)

    def _get_sii_exempt_cause(self, applied_taxes):
        cause = super()._get_sii_exempt_cause(applied_taxes)
        if cause or not self._is_atc_sii_agency():
            return cause
        # Art. 50.Uno.27º Ley 4/2012 (E1 en este módulo).
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if self._atc_tax_template_name(tax) == "igic_cmino":
                    return "E1"
        return cause

    @api.depends("company_id", "fiscal_position_id", "invoice_line_ids.tax_ids")
    def _compute_dua_invoice(self):
        res = super()._compute_dua_invoice()
        for invoice in self.filtered(lambda move: move._is_atc_sii_agency()):
            if invoice.sii_dua_invoice:
                continue
            fiscal_date = (
                invoice.date
                or invoice.invoice_date
                or fields.Date.context_today(invoice)
            )
            dua_taxes = invoice._get_aeat_taxes_map(["DUA"], fiscal_date)
            if not dua_taxes:
                continue
            line_taxes = invoice.line_ids.tax_ids
            if (line_taxes | line_taxes.children_tax_ids) & dua_taxes:
                invoice.sii_dua_invoice = True
        return res

    def _get_aeat_invoice_dict(self):
        inv_dict = super()._get_aeat_invoice_dict()
        round_by_keys(inv_dict, ["CargaImpositivaImplicita"])
        return inv_dict

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
            inv_dict = self._atc_inject_art25_datos(inv_dict, "FacturaExpedida")
        return inv_dict

    def _get_aeat_invoice_dict_in(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_in(cancel=cancel)
        if cancel:
            return inv_dict
        if self._is_atc_sii_agency():
            inv_dict = self._sii_atc_replace_tax_keys(inv_dict)
            inv_dict = self._atc_prune_invoice_dict_in(inv_dict)
            inv_dict = self._atc_force_cuota_deducible_no_cuota_keys(inv_dict)
            inv_dict = self._atc_inject_art25_datos(inv_dict, "FacturaRecibida")
        return inv_dict

    def _atc_prune_invoice_dict_in(self, inv_dict):
        """Quita bloques de desglose vacíos tras el mapeo IVA→IGIC."""
        factura = inv_dict.get("FacturaRecibida") or {}
        desglose = factura.get("DesgloseFactura")
        if not isinstance(desglose, dict):
            return inv_dict
        for block_key, detail_key in (
            ("DesgloseIGIC", "DetalleIGIC"),
            ("DesgloseIVA", "DetalleIVA"),
        ):
            block = desglose.get(block_key)
            if isinstance(block, dict) and not block.get(detail_key):
                desglose.pop(block_key, None)
        # F5 y LC no admiten InversionSujetoPasivo (ATC 1339/1340).
        if factura.get("TipoFactura") in _ATC_DUA_INVOICE_TYPES:
            desglose.pop("InversionSujetoPasivo", None)
        return inv_dict

    def _atc_force_cuota_deducible_no_cuota_keys(self, inv_dict):
        """Claves 08/16/17/18: CuotaDeducible = 0 (ATC no admite cuota)."""
        self.ensure_one()
        if self.sii_registration_key_code not in _ATC_NO_CUOTA_PURCHASE_KEYS:
            return inv_dict
        factura = inv_dict.get("FacturaRecibida")
        if isinstance(factura, dict):
            factura["CuotaDeducible"] = 0.0
        return inv_dict

    @api.depends("sii_registration_key", "sii_registration_key.code", "move_type")
    def _compute_sii_art25_required(self):
        for move in self:
            move.sii_art25_required = move._atc_requires_art25_block()

    @api.onchange("sii_registration_key")
    def _onchange_sii_registration_key_art25(self):
        """Clear Art. 25 fields when leaving claves 17 (compra) / 19 (venta)."""
        if self._atc_requires_art25_block():
            return
        self.sii_art25_prepayment = False
        self.sii_art25_document_id = False
        self.sii_art25_protocol_number = False
        self.sii_art25_notary_name = False

    def _atc_requires_art25_block(self):
        self.ensure_one()
        if not self._is_atc_sii_agency() or not self.is_invoice():
            return False
        code = self.sii_registration_key.code if self.sii_registration_key else False
        if self.move_type.startswith("in_"):
            return code == _ATC_ART25_PURCHASE_KEY
        if self.move_type.startswith("out_"):
            return code == _ATC_ART25_SALE_KEY
        return False

    def _atc_has_art25_invoice_fields(self):
        self.ensure_one()
        return bool(
            self.sii_art25_prepayment
            or self.sii_art25_document_id
            or self.sii_art25_protocol_number
            or self.sii_art25_notary_name
        )

    def _atc_art25_invoice_lines(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product" and line.product_id
        )

    def _atc_get_art25_tipo_bien(self, line):
        self.ensure_one()
        tipo = line.product_id.sii_art25_tipo_bien
        if not tipo and self.fiscal_position_id.sii_art25_tipo_bien:
            tipo = self.fiscal_position_id.sii_art25_tipo_bien
        return tipo

    def _atc_get_art25_datos_dict(self):
        self.ensure_one()
        if not self._atc_requires_art25_block():
            return None
        details = []
        for line in self._atc_art25_invoice_lines():
            tipo_bien = self._atc_get_art25_tipo_bien(line)
            if not tipo_bien:
                continue
            detail = {
                "PagoAnticipadoArt25": self.sii_art25_prepayment,
                "TipoBienArt25": tipo_bien,
                "IDDocumentoArt25": self.sii_art25_document_id,
            }
            if self.sii_art25_document_id == "01":
                detail["NumeroProtocolo"] = self.sii_art25_protocol_number or ""
                detail["ApellidosNombreNotario"] = self.sii_art25_notary_name or ""
            details.append(detail)
        if not details:
            return None
        return {"DetalleArticulo25": details}

    def _atc_inject_art25_datos(self, inv_dict, section_key):
        self.ensure_one()
        art25 = self._atc_get_art25_datos_dict()
        if art25 and section_key in inv_dict:
            inv_dict[section_key]["DatosArticulo25"] = art25
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
        self._aeat_check_regime_exempt_only()
        self._aeat_check_cuota_deducible_key_17()
        self._aeat_check_repep_cii()
        self._aeat_check_dua_no_isp()
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

    def _aeat_check_regime_exempt_only(self):
        """Error ATC 1281: claves 02/17/18/19 solo admiten operación Sujeta/Exenta."""
        self.ensure_one()
        if not self.move_type.startswith("out_"):
            return
        if self.sii_registration_key.code not in _ATC_EXEMPT_ONLY_REGIMES:
            return
        if (
            self.sii_registration_key_additional1
            or self.sii_registration_key_additional2
        ):
            return
        factura = self._atc_get_invoice_section("out")
        if self._atc_walk_nodes(factura, "NoExenta"):
            raise UserError(
                self.env._(
                    "ATC error 1281: registration key %(reg)s only allows a "
                    "Sujeta/Exenta breakdown.",
                    reg=self.sii_registration_key.code,
                )
            )

    def _aeat_check_cuota_deducible_key_17(self):
        """Error ATC 1329: CuotaDeducible debe ser 0 con clave 17."""
        self.ensure_one()
        if (
            not self.move_type.startswith("in_")
            or self.sii_registration_key.code != "17"
        ):
            return
        factura = self._atc_get_invoice_section("in")
        if abs(float(factura.get("CuotaDeducible") or 0)) > 0.01:
            raise UserError(
                self.env._(
                    "ATC error 1329: CuotaDeducible must be zero when the "
                    "registration key is 17."
                )
            )

    def _aeat_check_repep_cii(self):
        """ATC 1330/1350: CII exige tipo nominal y CuotaDeducible igual a la CII."""
        self.ensure_one()
        if not self.move_type.startswith("in_"):
            return
        factura = self._atc_get_invoice_section("in")
        cii_sum = 0.0
        has_cii = False
        for detalle in self._atc_walk_nodes(factura, "DetalleIGIC"):
            if "CargaImpositivaImplicita" not in detalle:
                continue
            has_cii = True
            if detalle.get("TipoImpositivo") in (None, False, ""):
                raise UserError(
                    self.env._(
                        "ATC error 1330: TipoImpositivo is required when "
                        "CargaImpositivaImplicita is set."
                    )
                )
            cii_sum += float(detalle.get("CargaImpositivaImplicita") or 0)
        if self.sii_registration_key.code == "15" and has_cii:
            deductible = float(factura.get("CuotaDeducible") or 0)
            if abs(deductible - cii_sum) > 0.02:
                raise UserError(
                    self.env._(
                        "ATC error 1350: CuotaDeducible (%(ded)s) must equal "
                        "CargaImpositivaImplicita (%(cii)s) for registration key 15.",
                        ded=deductible,
                        cii=cii_sum,
                    )
                )

    def _aeat_check_dua_no_isp(self):
        """Errores ATC 1339/1340: F5 y LC no admiten InversionSujetoPasivo."""
        self.ensure_one()
        if not self.move_type.startswith("in_"):
            return
        factura = self._atc_get_invoice_section("in")
        if factura.get("TipoFactura") not in _ATC_DUA_INVOICE_TYPES:
            return
        desglose = factura.get("DesgloseFactura") or {}
        if isinstance(desglose, dict) and desglose.get("InversionSujetoPasivo"):
            raise UserError(
                self.env._(
                    "ATC error 1339: InversionSujetoPasivo is not allowed on "
                    "invoice type %(tipo)s.",
                    tipo=factura.get("TipoFactura"),
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
        """Error ATC 2042: ImporteTotal debe cuadrar con el desglose IGIC.

        En compras con bloque ``InversionSujetoPasivo`` la cuota es
        autorrepercutida: ``ImporteTotal`` es la base (importe al proveedor),
        no base+cuota. Ver ``_atc_compute_breakdown_total``.
        """
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
        # El SII base no envía ImporteTotal en facturas DUA.
        importe_total = factura.get("ImporteTotal")
        if importe_total in (None, False, ""):
            return
        importe_total = abs(float(importe_total))
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

    @api.model
    def _atc_iter_tax_details(self, factura):
        """Yield ``(detalle, under_isp)`` for ``DetalleIGIC`` / ``DetalleIVA``.

        ``under_isp`` is True when the detail lives under
        ``InversionSujetoPasivo`` (purchase reverse charge).
        """
        found = []

        def walk(item, under_isp=False):
            if isinstance(item, dict):
                if "InversionSujetoPasivo" in item:
                    walk(item["InversionSujetoPasivo"], under_isp=True)
                for detail_key in ("DetalleIGIC", "DetalleIVA"):
                    if detail_key not in item:
                        continue
                    # Only count details at this level when we are inside ISP
                    # or outside an ISP sibling (DesgloseIGIC / DesgloseFactura).
                    if detail_key in item and (
                        under_isp or "InversionSujetoPasivo" not in item
                    ):
                        value = item[detail_key]
                        if isinstance(value, list):
                            for detalle in value:
                                if isinstance(detalle, dict):
                                    found.append((detalle, under_isp))
                        elif isinstance(value, dict):
                            found.append((value, under_isp))
                for key, value in item.items():
                    if key in (
                        "InversionSujetoPasivo",
                        "DetalleIGIC",
                        "DetalleIVA",
                    ):
                        continue
                    walk(value, under_isp=under_isp)
            elif isinstance(item, list):
                for sub in item:
                    walk(sub, under_isp=under_isp)

        walk(factura)
        return found

    def _atc_compute_breakdown_total(self, factura, primary_cuota_keys):
        """Suma bases (+ cuotas) del desglose para contrastar con ImporteTotal.

        En ``InversionSujetoPasivo`` solo cuenta la base: la cuota es
        autorrepercutida y no forma parte del importe pagado al proveedor
        (ni de ``amount_total`` / ``ImporteTotal`` en Odoo).
        """
        total = 0.0
        detail_count = 0
        # CargaImpositivaImplicita repite la cuota deducible; no se suma otra vez.
        extra_cuota_keys = (
            "CuotaAIEM",
            "CuotaRecargoMinorista",
        )
        for detalle, under_isp in self._atc_iter_tax_details(factura):
            detail_count += 1
            total += float(detalle.get("BaseImponible", 0) or 0)
            if under_isp:
                continue
            for key in primary_cuota_keys + extra_cuota_keys:
                total += float(detalle.get(key, 0) or 0)
        for detalle in self._atc_walk_nodes(factura, "DetalleExenta"):
            detail_count += 1
            total += float(detalle.get("BaseImponible", 0) or 0)
        for block in self._atc_walk_nodes(factura, "NoSujeta"):
            for key, value in block.items():
                if key.startswith("Importe"):
                    detail_count += 1
                    total += float(value)
        if not detail_count:
            return None
        return total
