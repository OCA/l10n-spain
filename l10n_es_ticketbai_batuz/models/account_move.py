# Copyright (2021) Binovo IT Human Project SL
# Copyright 2021 Digital5, S.L.
# Copyright 2021 KERNET INTERNET Y NUEVAS TECNOLOGIAS S.L.
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
from collections import OrderedDict

from odoo import _, api, exceptions, fields, models

from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import (
    RefundCode,
    RefundType,
)
from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice_customer import (
    TicketBaiCustomerIdType,
)
from odoo.addons.l10n_es_ticketbai_api_batuz.models.lroe_operation import (
    LROEModelEnum,
    LROEOperationEnum,
)

LROE_COUNTRY_CODE_MAPPING = {
    "RE": "FR",
    "GP": "FR",
    "MQ": "FR",
    "GF": "FR",
}
LROE_STATES = [
    ("not_sent", "Not recorded"),
    ("pending", "Registration in LROE planned"),
    ("error", "Registration error"),
    ("recorded", "Recorded"),
    ("recorded_warning", "Recorded with warnings"),
    ("recorded_modified", "Registered in LROE but last modifications not recorded"),
    ("cancel", "Cancel"),
    ("cancel_modified", "Cancelled in LROE but last modifications not recorded"),
]
KEYS_TO_ROUND = [
    "BaseRectificada",
    "CuotaRectificada",
    "CuotaRecargoEquivalencia",
    "ImporteTotalFactura",
    "BaseImponibleACoste",
    "BaseImponible",
    "CuotaIVASoportada",
    "CuotaIVADeducible",
    "ImporteGastoIRPF",
    "ImporteCompensacionREAGYP",
    "TipoRecargoEquivalencia",
    "CuotaImpuesto",
]


def round_by_keys(elem, search_keys, prec=2):
    """This uses ``round`` method directly as if has been tested that Odoo's
    ``float_round`` still returns incorrect amounts for certain values. Try
    3 units x 3,77 €/unit with 10% tax and you will be hit by the error
    (on regular x86 architectures)."""
    if isinstance(elem, dict):
        for key, value in elem.items():
            if key in search_keys:
                elem[key] = str(round(elem[key], prec))
            else:
                round_by_keys(value, search_keys)
    elif isinstance(elem, list):
        for value in elem:
            round_by_keys(value, search_keys)


class AccountMove(models.Model):
    _inherit = "account.move"

    lroe_response_line_ids = fields.Many2many(
        comodel_name="lroe.operation.response.line",
        compute="_compute_lroe_response_line_ids",
        string="Responses",
    )
    lroe_operation_ids = fields.Many2many(
        comodel_name="lroe.operation",
        relation="account_invoice_lroe_operation_rel",
        column1="invoice_id",
        column2="lroe_operation_id",
        string="LROE Operations",
        copy=False,
    )
    lroe_state = fields.Selection(
        selection=LROE_STATES,
        string="LROE state",
        default="not_sent",
        copy=False,
        help="Indicates the state of this invoice in relation with LROE/Batuz",
    )
    tbai_vat_regime_purchase_key = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="Purchase VAT Regime Key",
        domain=[("type", "=", "purchase")],
        copy=True,
    )
    tbai_vat_regime_purchase_key2 = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="Purchase VAT Regime 2nd Key",
        domain=[("type", "=", "purchase")],
        copy=True,
    )
    tbai_vat_regime_purchase_key3 = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="Purchase VAT Regime 3rd Key",
        domain=[("type", "=", "purchase")],
        copy=True,
    )
    lroe_invoice_dict = fields.Text(
        string="LROE last content sent", copy=False, readonly=True,
    )

    @api.depends(
        "tbai_invoice_ids",
        "tbai_invoice_ids.state",
        "tbai_cancellation_ids",
        "tbai_cancellation_ids.state",
    )
    def _compute_lroe_response_line_ids(self):
        for record in self:
            response_line_model = self.env["lroe.operation.response.line"]
            response_ids = record.tbai_invoice_ids.mapped("tbai_response_ids").ids
            response_ids += record.tbai_cancellation_ids.mapped("tbai_response_ids").ids
            response_lines = response_line_model.search(
                [("tbai_response_id", "in", response_ids)]
            )
            record.lroe_response_line_ids = [(6, 0, response_lines.ids)]

    @api.model
    def create(self, vals):
        company = self.env["res.company"].browse(
            vals.get("company_id", self.env.user.company_id.id)
        )
        tbai_tax_agency_id = company.tbai_tax_agency_id
        if (
            not company.tbai_enabled
            or not tbai_tax_agency_id
            or tbai_tax_agency_id.id
            != self.env.ref("l10n_es_ticketbai_api_batuz.tbai_tax_agency_bizkaia").id
        ):
            return super().create(vals)
        invoice_type = vals.get("type", False) or self._context.get(
            "default_type", False
        )
        refund_method = (
            self._context.get("refund_method", False) or invoice_type == "in_refund"
        )
        if refund_method and invoice_type:
            if "in_refund" == invoice_type:
                if not vals.get("tbai_refund_type", False):
                    vals["tbai_refund_type"] = RefundType.differences.value
                if not vals.get("tbai_refund_key", False):
                    vals["tbai_refund_key"] = RefundCode.R1.value
        if "name" in vals and vals["name"]:
            vals["tbai_description_operation"] = vals["name"]

        invoice = super(AccountMove, self).create(vals)
        if vals.get("fiscal_position_id"):
            invoice.onchange_fiscal_position_id_lroe_vat_regime_key()
        return invoice

    @api.onchange("fiscal_position_id", "partner_id")
    def onchange_fiscal_position_id_lroe_vat_regime_key(self):
        if self.fiscal_position_id and ("in" in self.type):
            self.tbai_vat_regime_purchase_key = (
                self.fiscal_position_id.tbai_vat_regime_purchase_key.id
            )
            self.tbai_vat_regime_purchase_key2 = (
                self.fiscal_position_id.tbai_vat_regime_purchase_key2.id
            )
            self.tbai_vat_regime_purchase_key3 = (
                self.fiscal_position_id.tbai_vat_regime_purchase_key3.id
            )

    def _get_chapter_subchapter(self):
        """ Identificamos el capitulo y subcapitulo """
        self.ensure_one()
        if self.company_id.lroe_model == LROEModelEnum.model_pj_240.value:
            chapter = self.env.ref("l10n_es_ticketbai_api_batuz.lroe_chapter_pj_240_2")
            return chapter.code, False
        elif self.company_id.lroe_model == LROEModelEnum.model_pf_140.value:
            chapter = self.env.ref("l10n_es_ticketbai_api_batuz.lroe_chapter_pf_140_2")
            subchapter = self.env.ref(
                "l10n_es_ticketbai_api_batuz.lroe_subchapter_pf_140_2_1"
            )
            return chapter.code, subchapter.code

    def _get_lroe_country_code(self):
        self.ensure_one()
        country_code = (
            self.partner_id.commercial_partner_id.country_id.code
            or (self.partner_id.vat or "")[:2]
        ).upper()
        return LROE_COUNTRY_CODE_MAPPING.get(country_code, country_code)

    def _get_batuz_description(self):
        """Concatenamos la referencia/descripción de la factura con el
        número interno de la misma. De esta forma es más sencillo identificarla
        en el sistema de hacienda."""
        self.ensure_one()
        return self.name

    def batuz_get_supplier_serie_factura(self):
        """Consultamos a hacienda cómo extraer la serie de una factura de proveedor.
        Al no ser posible en algunos casos, decidimos tomar ciertos caracteres
        como serie y el resto como número.
        Aunque la serie no es obligatoria en facturas recibidas,
        sí lo es en las rectificativas, por lo que es necesario informarla siempre."""
        return self.ref[:3]

    def batuz_get_supplier_num_factura(self):
        return self.ref[3:]

    def _get_lroe_identifier(self):
        """Get the LROE structure for a partner identifier.
        [('1', 'National'), ('2', 'Intracom'), ('3', 'Export')]
        """
        self.ensure_one()
        res = OrderedDict()
        partner = self.partner_id.commercial_partner_id
        idtype = partner.tbai_partner_idtype
        if partner.vat:
            vat = "".join(e for e in partner.vat if e.isalnum()).upper()
        else:
            vat = "NO_DISPONIBLE"
        country_code = self._get_lroe_country_code()
        if idtype == TicketBaiCustomerIdType.T02.value:
            if country_code != "ES":
                id_type = "06" if vat == "NO_DISPONIBLE" else "02"
                res["IDOtro"] = OrderedDict(
                    [("CodigoPais", country_code), ("IDType", id_type), ("ID", vat)]
                )
            else:
                res["NIF"] = vat[2:] if vat.startswith(country_code) else vat
        elif idtype:
            res["IDOtro"] = OrderedDict(
                [("CodigoPais", country_code), ("IDType", idtype), ("ID", vat)]
            )
        res[
            "ApellidosNombreRazonSocial"
        ] = partner.tbai_get_value_apellidos_nombre_razon_social()
        return res

    def _is_lroe_simplified_invoice(self):
        """Inheritable method to allow control when an
        invoice are simplified or normal"""
        partner = self.partner_id.commercial_partner_id
        is_simplified = partner.lroe_simplified_invoice
        return is_simplified

    def _get_operation_date(self):
        """ Inheritable method to allow set operation date of an invoice """
        self.ensure_one()
        return False

    def _get_last_move_number(self):
        """Inheritable method to allow set the last number of the move when an
        invoice is move summary"""
        self.ensure_one()
        return False

    def _change_date_format(self, date):
        if not date:
            return False
        datetime_object = fields.Date.from_string(date)
        new_date = datetime_object.strftime("%d-%m-%Y")
        return new_date

    def _get_lroe_invoice_header(self):
        self.ensure_one()
        invoice_date = self._change_date_format(self.invoice_date)
        operation_date = self._change_date_format(self._get_operation_date())
        reception_date = self._change_date_format(self.date)
        tipo_factura = "F2" if self._is_lroe_simplified_invoice() else "F1"
        last_number = self._get_last_move_number()
        header = OrderedDict()
        header["SerieFactura"] = self.batuz_get_supplier_serie_factura()[:20]
        header["NumFactura"] = self.batuz_get_supplier_num_factura()[:20]
        if last_number:
            # NumFacturaFin = número de la factura que identifica a la
            #  última factura cuando se trata de un asiento resumen de facturas
            header["NumFacturaFin"] = last_number[:20]
        header["FechaExpedicionFactura"] = invoice_date
        if operation_date:
            header["FechaOperacion"] = operation_date
        header["FechaRecepcion"] = reception_date
        header["TipoFactura"] = tipo_factura
        if self.type == "in_refund":
            header["FacturaRectificativa"] = OrderedDict(
                [("Codigo", self.tbai_refund_key), ("Tipo", self.tbai_refund_type)]
            )
            if self.reversed_entry_id:
                origin = self.reversed_entry_id
                origin_date = self._change_date_format(
                    self.reversed_entry_id.invoice_date
                )
                header["FacturasRectificadasSustituidas"] = OrderedDict(
                    [
                        (
                            "IDFacturaRectificadaSustituida",
                            OrderedDict(
                                [
                                    (
                                        "SerieFactura",
                                        origin.batuz_get_supplier_serie_factura()[:20],
                                    ),
                                    (
                                        "NumFactura",
                                        origin.batuz_get_supplier_num_factura()[:20],
                                    ),
                                    ("FechaExpedicionFactura", origin_date),
                                ]
                            ),
                        ),
                    ]
                )
            elif self.tbai_refund_origin_ids:
                origins = list()
                for refund_origin_id in self.tbai_refund_origin_ids:
                    vals = list()
                    if refund_origin_id.number_prefix:
                        vals.append(("SerieFactura", refund_origin_id.number_prefix))
                    vals.append(("NumFactura", refund_origin_id.number))
                    vals.append(
                        ("FechaExpedicionFactura", refund_origin_id.expedition_date)
                    )

                    origins.append(
                        ("IDFacturaRectificadaSustituida", OrderedDict(vals)),
                    )
                header["FacturasRectificadasSustituidas"] = OrderedDict(origins)

        return header

    def _get_lroe_purchase_key_codes(self):
        self.ensure_one()
        regime_keys = (
            self.tbai_vat_regime_purchase_key
            | self.tbai_vat_regime_purchase_key2
            | self.tbai_vat_regime_purchase_key3
        )
        return regime_keys.mapped("code")

    def _get_lroe_claves(self):
        res = {"IDClave": []}
        keys = self._get_lroe_purchase_key_codes()
        for key in keys:
            res["IDClave"].append({"ClaveRegimenIvaOpTrascendencia": key})
        return res

    def _get_lroe_taxes_map(self, codes):
        """Return the codes that correspond to that LROE map line codes.

        :param self: Invoice record
        :param codes: List of code strings to get the mapping.
        :return: Recordset with the corresponding codes
        """
        self.ensure_one()
        tbai_maps = self.env["tbai.tax.map"].search([("code", "in", codes)])
        tax_templates = tbai_maps.mapped("tax_template_ids")
        return self.company_id.get_taxes_from_templates(tax_templates)

    def _get_lroe_tax_line_req(self, tax):
        """Get the invoice tax line for 'Recargo equivalencia'.

        :param self: Single invoice record.
        :param tax: Initial tax for searching for the RE twin tax.
        :return: Invoice tax line (if any) for the correspondent RE tax.
        """
        self.ensure_one()
        taxes_re = self._get_lroe_taxes_map(["RE"])
        re_lines = self.line_ids.filtered(
            lambda x: tax in x.tax_ids and x.tax_ids & taxes_re
        )
        re_tax = re_lines.mapped("tax_ids") & taxes_re
        if len(re_tax) > 1:
            raise exceptions.UserError(
                _("There's a mismatch in taxes for RE. Check them.")
            )
        return re_tax

    @api.model
    def _get_lroe_tax_dict(self, tax_line, tax_lines, deductible=True):
        """Get the LROE tax dictionary for the passed tax line.
        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :param deductible: is deductible or not
        :return: A dictionary with the corresponding LROE tax values.
        """
        tax = tax_line["tax"]
        if tax.amount_type == "group":
            tax_type = abs(tax.children_tax_ids.filtered("amount")[:1].amount)
        else:
            tax_type = abs(tax.amount)

        base = tax_line["base"]
        cuota = tax_line["amount"]

        if self.company_id.lroe_model == "240":
            tax_dict = OrderedDict(
                [
                    ("CompraBienesCorrientesGastosBienesInversion", "C"),  # C, G o I
                    ("InversionSujetoPasivo", "N"),
                    ("BaseImponible", base),
                    ("TipoImpositivo", str(tax_type)),
                    ("CuotaIVASoportada", cuota),
                    ("CuotaIVADeducible", cuota * int(deductible)),
                ]
            )
        else:
            tax_dict = OrderedDict(
                [
                    ("Epigrafe", self.company_id.main_activity_iae),
                    # TODO: 140 - BienAfectoIRPFYOIVA --> valor por defecto "N"
                    # TODO: 140 - Concepto --> grupo de cuenta contable L20
                    # TODO: 140 - ReferenciaBien
                    ("InversionSujetoPasivo", "N"),
                    # TODO: 140 - OperacionEnRecargoDeEquivalenciaORegimenSimplificado
                    ("BaseImponible", base),
                    ("TipoImpositivo", str(tax_type)),
                    ("CuotaIVASoportada", cuota),
                    ("CuotaIVADeducible", cuota * int(deductible)),
                    # TODO: 140 - ImporteGastoIRPF
                    # TODO: 140 - CriterioCobrosYPagos
                ]
            )
            # Recargo de equivalencia
            req_tax = self._get_lroe_tax_line_req(tax)
            if req_tax:
                tax_dict["TipoRecargoEquivalencia"] = req_tax.amount
                tax_dict["CuotaRecargoEquivalencia"] = tax_lines[req_tax]["amount"]
        return tax_dict

    def _get_lroe_in_taxes(self):
        """Get taxes for purchase invoices
        :param self: invoice record
        """
        self.ensure_one()
        lroe_model = self.company_id.lroe_model
        taxes_dict = (
            {"IVA": {"DetalleIVA": []}}
            if lroe_model == "240"
            else {"RentaIVA": {"DetalleRentaIVA": []}}
        )
        # Facturas Recibidas Servicios
        taxes_frs = self._get_lroe_taxes_map(["FRS"])
        # Facturas Recibidas Bienes Corrientes
        taxes_frbc = self._get_lroe_taxes_map(["FRBC"])
        # Facturas Recibidas Bienes de Inversión
        taxes_frbi = self._get_lroe_taxes_map(["FRBI"])
        # Facturas Recibidas Agricultura
        taxes_frsa = self._get_lroe_taxes_map(["FRSA"])
        # Facturas Recibidas ISP
        taxes_frisp = self._get_lroe_taxes_map(["FRISP"])
        # Facturas Recibidas No Sujeta
        taxes_frns = self._get_lroe_taxes_map(["FRNS"])
        # Facturas Recibidas No Deducible
        taxes_frnd = self._get_lroe_taxes_map(["FRND"])
        # Impuestos no incluidos en Importe Total
        taxes_not_in_total = self._get_lroe_taxes_map(["NotIncludedInTotal"])
        # Impuestos no incluidos en Importe Total (negativos)
        taxes_not_in_total_negative = self._get_lroe_taxes_map(
            ["NotIncludedInTotalNegative"]
        )
        tax_amount = 0.0
        not_in_amount_total = 0.0
        tax_lines = self._get_tax_info().values()
        for tax_line in tax_lines:
            tax = tax_line["tax"]
            deductible = tax in taxes_frisp + taxes_frs + taxes_frbc + taxes_frbi
            tax_dict = self._get_lroe_tax_dict(tax_line, tax_lines, deductible)
            if tax in taxes_not_in_total:
                amount = tax_line["amount"]
                not_in_amount_total += amount
            elif tax in taxes_not_in_total_negative:
                amount = tax_line["amount"]
                not_in_amount_total -= amount

            if tax in taxes_frisp:
                tax_dict["InversionSujetoPasivo"] = "S"
            elif (
                tax
                in taxes_frs
                + taxes_frbc
                + taxes_frbi
                + taxes_frsa
                + taxes_frns
                + taxes_frnd
            ):
                tax_dict["InversionSujetoPasivo"] = "N"
            else:
                # No informar de DetalleIVA sobre IRPF
                continue

            if tax in taxes_frbc and lroe_model == "240":
                tax_dict["CompraBienesCorrientesGastosBienesInversion"] = "C"
            elif tax in taxes_frs and lroe_model == "240":
                tax_dict["CompraBienesCorrientesGastosBienesInversion"] = "G"
            elif tax in taxes_frbi and lroe_model == "240":
                tax_dict["CompraBienesCorrientesGastosBienesInversion"] = "I"

            if tax in taxes_frisp + taxes_frs + taxes_frbc:
                tax_amount += tax_line["amount"]

            if tax in taxes_frns:
                tax_dict.pop("TipoImpositivo")
                tax_dict.pop("CuotaIVASoportada")
                tax_dict.pop("CuotaIVADeducible")
            elif tax in taxes_frsa:
                if "02" in self._get_lroe_purchase_key_codes():
                    tax_dict["PorcentajeCompensacionREAGYP"] = tax_dict.pop(
                        "TipoImpositivo"
                    )
                    tax_dict["ImporteCompensacionREAGYP"] = tax_dict.pop(
                        "CuotaIVASoportada"
                    )
            if "13" in self._get_lroe_purchase_key_codes():
                # Eliminamos la clave CuotaIVADeducible en importaciones
                tax_dict.pop("CuotaIVADeducible")
            if lroe_model == "240":
                taxes_dict["IVA"]["DetalleIVA"].append(tax_dict)
            elif lroe_model == "140":
                taxes_dict["RentaIVA"]["DetalleRentaIVA"].append(tax_dict)
        return taxes_dict, tax_amount, not_in_amount_total

    def _get_tax_info(self):
        self.ensure_one()
        res = {}
        for line in self.line_ids:
            sign = -1 if self.type[:3] == "out" else 1
            for tax in line.tax_ids:
                res.setdefault(tax, {"tax": tax, "base": 0, "amount": 0})
                res[tax]["base"] += line.balance * sign
            if line.tax_line_id:
                tax = line.tax_line_id
                if "invoice" in self.type:
                    repartition_lines = tax.invoice_repartition_line_ids
                else:
                    repartition_lines = tax.refund_repartition_line_ids
                if (
                    len(repartition_lines) > 2
                    and line.tax_repartition_line_id.factor_percent < 0
                ):
                    # taxes with more than one "tax" repartition line must be discarded
                    continue
                res.setdefault(tax, {"tax": tax, "base": 0, "amount": 0})
                res[tax]["amount"] += line.balance * sign
        return res

    def _get_lroe_invoice_data(self, amount_total):
        self.ensure_one()
        res = OrderedDict(
            [
                ("DescripcionOperacion", self._get_batuz_description()[:250]),
                ("Claves", self._get_lroe_claves()),
                ("ImporteTotalFactura", amount_total or self.amount_total),
                # Base imponible a coste (para grupos de IVA – nivel avanzado (240))
                # ("BaseImponibleACoste", False),
            ]
        )
        return res

    # SPECIFIC LROE CHAPTER METHODS
    def _get_lroe_140_2_1_dict(self, cancel=False):
        """
        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the invoice.
        :return: invoice (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        if cancel:
            invoice_date = self._change_date_format(self.invoice_date)
            lroe_identifier = self._get_lroe_identifier()
            lroe_identifier.pop("ApellidosNombreRazonSocial")
            id_gasto = OrderedDict(
                [
                    (
                        "IDGasto",
                        OrderedDict(
                            [
                                (
                                    "SerieFactura",
                                    self.batuz_get_supplier_serie_factura()[:20],
                                ),
                                (
                                    "NumFactura",
                                    self.batuz_get_supplier_num_factura[:20],
                                ),
                                ("FechaExpedicionFactura", invoice_date),
                                ("EmisorFacturaRecibida", lroe_identifier),
                            ]
                        ),
                    )
                ]
            )
            inv_dict = OrderedDict([("Gasto", id_gasto)])
        else:
            # Check if refund type is "By differences". Negative amounts!
            taxes_dict, tax_amount, not_in_amount_total = self._get_lroe_in_taxes()
            amount_total = -self.amount_total_signed - not_in_amount_total
            inv_dict = OrderedDict(
                [
                    (
                        "Gasto",
                        OrderedDict(
                            [
                                ("EmisorFacturaRecibida", self._get_lroe_identifier()),
                                ("CabeceraFactura", self._get_lroe_invoice_header()),
                                (
                                    "DatosFactura",
                                    self._get_lroe_invoice_data(amount_total),
                                ),
                                ("RentaIVA", taxes_dict["RentaIVA"]),
                                # ("OtraInformacionTrascendenciaTributaria", False),
                            ]
                        ),
                    )
                ]
            )
        return inv_dict

    def _get_lroe_240_2_dict(self, cancel=False):
        """
        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the invoice.
        :return: invoice (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        if cancel:
            invoice_date = self._change_date_format(self.invoice_date)
            lroe_identifier = self._get_lroe_identifier()
            lroe_identifier.pop("ApellidosNombreRazonSocial")
            last_number = self._get_last_move_number()
            id_recibida = OrderedDict()
            id_recibida["SerieFactura"] = self.batuz_get_supplier_serie_factura()[:20]
            id_recibida["NumFactura"] = self.batuz_get_supplier_num_factura()[:20]
            if last_number:
                id_recibida["NumFacturaFin"] = last_number[:20]
            id_recibida["FechaExpedicionFactura"] = invoice_date
            id_recibida["EmisorFacturaRecibida"] = lroe_identifier
            inv_dict = OrderedDict(
                [("FacturaRecibida", OrderedDict([("IDRecibida", id_recibida)]))]
            )
        else:
            # Check if refund type is "By differences". Negative amounts!
            taxes_dict, tax_amount, not_in_amount_total = self._get_lroe_in_taxes()
            amount_total = -self.amount_total_signed - not_in_amount_total
            inv_dict = OrderedDict(
                [
                    (
                        "FacturaRecibida",
                        OrderedDict(
                            [
                                ("EmisorFacturaRecibida", self._get_lroe_identifier()),
                                ("CabeceraFactura", self._get_lroe_invoice_header()),
                                (
                                    "DatosFactura",
                                    self._get_lroe_invoice_data(amount_total),
                                ),
                                ("IVA", taxes_dict["IVA"]),
                                # ("OtraInformacionTrascendenciaTributaria", False),
                            ]
                        ),
                    )
                ]
            )
        return inv_dict

    # COMMON LROE METHODS
    @api.model
    def _prepare_lroe_operation_values(
        self, company_id=False, operation_type=None, chapter=None, subchapter=None
    ):
        """
        Buscamos lroe.operation pendiente de envío con misma operacion (type)
        y mismo capítulo + subcapítulo
        :param company_id: (int) company id
        :param operation_type: LROEOperationEnum.value
        :param chapter: LROEChapterEnum.value
        :param subchapter: LROEChapterEnum.value
        :return: lroe.operation object if any
        """
        if not chapter or not operation_type:
            raise exceptions.ValidationError(
                _("Chapter and type are required for search a pending LROE Operation")
            )
        chapter_id = self.env["lroe.chapter"].search([("code", "=", chapter)], limit=1)
        res = {
            "lroe_chapter_id": chapter_id.id,
            "type": operation_type.value,
        }
        if subchapter:
            subchapter_id = self.env["lroe.chapter"].search([("code", "=", subchapter)])
            res.update({"lroe_subchapter_id": subchapter_id.id})
        if company_id:
            res.update({"company_id": company_id})
        return res

    def _get_lroe_operation(self, operation_type=None):
        """
        Creamos lroe.operation con operation_type y mismo capítulo + subcapítulo
        :param operation_type:
        :return: lroe.operation object
        """
        self.ensure_one()
        lroe_model = self.env["lroe.operation"]
        chapter, subchapter = self._get_chapter_subchapter()
        vals = self._prepare_lroe_operation_values(
            company_id=self.company_id.id,
            operation_type=operation_type,
            chapter=chapter,
            subchapter=subchapter,
        )
        lroe_operation = lroe_model.sudo().create(vals)
        return lroe_operation

    def _prepare_invoice_for_lroe(self, operation_type=None):
        """Se genera y guarda el diccionario correspondiente a la factura en base al
        capítulo/subcapítulo. Se crea un objeto lroe.operation por cada factura.
        Aunque hacienda permite un envio LROE con hasta 1.000 facturas TBAI
        o 10.000 facturas recibidas.
        :param operation_type: LROEOperationEnum
        :return:
        """
        if not operation_type:
            raise exceptions.ValidationError(
                _("LROE Build: operation type is necessary!")
            )
        for invoice in self:
            if not invoice.lroe_operation_ids._cancel_jobs():
                raise exceptions.Warning(
                    _(
                        "You can not communicate this invoice at this moment "
                        "because there is a job running!"
                    )
                )
            cancel = True if operation_type == LROEOperationEnum.cancel else False
            chapter, subchapter = invoice._get_chapter_subchapter()
            action = subchapter.replace(".", "_") if subchapter else chapter
            model = invoice.company_id.lroe_model
            if hasattr(invoice, "_get_lroe_%s_%s_dict" % (model, action,)):
                inv_dict = getattr(invoice, "_get_lroe_%s_%s_dict" % (model, action,))(
                    cancel
                )
            else:
                raise exceptions.ValidationError(
                    _("LROE Build: method for model %s chapter %s not implemented!")
                    % (model, chapter)
                )
            round_by_keys(
                inv_dict, KEYS_TO_ROUND,
            )
            lroe_operation = invoice._get_lroe_operation(operation_type=operation_type)
            inv_vals = {
                "lroe_invoice_dict": json.dumps(inv_dict, indent=4),
                "lroe_operation_ids": [(4, lroe_operation.id)],
            }
            invoice.write(inv_vals)
            invoice.set_lroe_state_pending()
            lroe_operation.process()

    def action_send_lroe_manually(self):
        lroe_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled
            and (
                x.type == "in_invoice"
                or (
                    x.type == "in_refund"
                    and (x.reversed_entry_id or x.tbai_refund_origin_ids)
                    and x.tbai_refund_type
                    in (RefundType.differences.value, RefundType.substitution.value)
                )
            )
        )
        for lroe_invoice in lroe_invoices:
            if lroe_invoice.lroe_state in (
                "recorded",
                "recorded_modified",
                "cancel_modified",
            ):
                lroe_invoices._prepare_invoice_for_lroe(
                    operation_type=LROEOperationEnum.update
                )
            elif lroe_invoice.lroe_state in ("not_sent", "cancel", "error"):
                lroe_invoices._prepare_invoice_for_lroe(
                    operation_type=LROEOperationEnum.create
                )

    # LROE STATE MANAGEMENT
    def set_lroe_state_pending(self):
        self.write({"lroe_state": "pending"})

    def set_lroe_state_error(self):
        self.write({"lroe_state": "error"})

    def set_lroe_state_recorded(self):
        self.write({"lroe_state": "recorded"})

    def set_lroe_state_recorded_warning(self):
        self.write({"lroe_state": "recorded_warning"})

    def set_lroe_state_recorded_modified(self):
        self.write({"lroe_state": "recorded_modified"})

    def set_lroe_state_cancel(self):
        self.write({"lroe_state": "cancel"})

    def set_lroe_state_cancel_modified(self):
        self.write({"lroe_state": "cancel_modified"})

    # INHERITED INVOICE METHODS
    def button_cancel(self):
        if not self.mapped("lroe_operation_ids")._cancel_jobs():
            raise exceptions.Warning(
                _(
                    "You can not set to draft this invoice because"
                    " there is a job running!"
                )
            )
        res = super().button_cancel()
        lroe_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled
            and x.lroe_state not in ("error")
            and (
                x.type == "in_invoice"
                or (
                    x.type == "in_refund"
                    and (x.reversed_entry_id or x.tbai_refund_origin_ids)
                    and x.tbai_refund_type
                    in (RefundType.differences.value, RefundType.substitution.value)
                )
            )
        )
        for invoice in lroe_invoices:
            if invoice.lroe_state == "recorded":
                invoice.set_lroe_state_recorded_modified()
            elif invoice.lroe_state == "cancel_modified":
                # Case when repoen a cancelled invoice, validate and cancel
                # again without any LROE communication.
                invoice.set_lroe_state_cancel()
        lroe_invoices._prepare_invoice_for_lroe(operation_type=LROEOperationEnum.cancel)
        return res

    def action_invoice_draft(self):
        if not self.sudo().mapped("lroe_operation_ids")._cancel_jobs():
            raise exceptions.Warning(
                _(
                    "You can not set to draft this invoice because"
                    " there is a job running!"
                )
            )
        return super().action_invoice_draft()

    def post(self):
        res = super(AccountMove, self).post()
        lroe_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled
            and (
                x.type == "in_invoice"
                or (
                    x.type == "in_refund"
                    and (x.reversed_entry_id or x.tbai_refund_origin_ids)
                    and x.tbai_refund_type
                    in (RefundType.differences.value, RefundType.substitution.value)
                )
            )
        )
        for lroe_invoice in lroe_invoices:
            if lroe_invoice.lroe_state in (
                "recorded",
                "recorded_modified",
                "cancel_modified",
            ):
                lroe_invoices._prepare_invoice_for_lroe(
                    operation_type=LROEOperationEnum.update
                )
            elif lroe_invoice.lroe_state in ("not_sent", "cancel", "error"):
                lroe_invoices._prepare_invoice_for_lroe(
                    operation_type=LROEOperationEnum.create
                )
        return res

    @api.model
    def _reverse_moves(self, default_values_list=None, cancel=False):
        # OVERRIDE
        if not default_values_list:
            default_values_list = [{} for move in self]
        for move, default_values in zip(self, default_values_list):
            extra_dict = {}
            supplier_invoice_number_refund = move.env.context.get(
                "batuz_supplier_invoice_number", False
            )
            if supplier_invoice_number_refund:
                extra_dict["ref"] = supplier_invoice_number_refund
            if extra_dict:
                default_values.update(extra_dict)
        res = super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel,
        )
        return res
