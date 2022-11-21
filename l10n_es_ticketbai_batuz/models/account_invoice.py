# Copyright (2021) Binovo IT Human Project SL
# Copyright 2021 Digital5, S.L.
# Copyright 2021 KERNET INTERNET Y NUEVAS TECNOLOGIAS S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, exceptions, fields, models, _
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
from collections import OrderedDict
import json

LROE_VALID_INVOICE_STATES = ["open", "in_payment", "paid"]
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


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    lroe_response_line_ids = fields.Many2many(
        comodel_name="lroe.operation.response.line",
        compute="_compute_lroe_response_line_ids",
        string="LROE Responses",
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
        string="LROE last content sent",
        copy=False,
        readonly=True,
    )

    @api.depends(
        'tbai_invoice_ids',
        'tbai_invoice_ids.state',
        'tbai_cancellation_ids',
        'tbai_cancellation_ids.state')
    def _compute_lroe_response_line_ids(self):
        for record in self:
            response_line_model = self.env['lroe.operation.response.line']
            response_ids = record.tbai_invoice_ids.mapped('tbai_response_ids').ids
            response_ids += record.tbai_cancellation_ids.mapped('tbai_response_ids').ids
            response_lines = response_line_model.search(
                [('tbai_response_id', 'in', response_ids)]
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
        if "refund" in vals.get("type", ""):
            if not vals.get("tbai_refund_type"):
                vals["tbai_refund_type"] = RefundType.differences.value
            if "tbai_refund_key" not in vals:
                vals["tbai_refund_key"] = RefundCode.R1.value
        if "name" in vals and vals["name"]:
            vals["tbai_description_operation"] = vals["name"]

        invoice = super(AccountInvoice, self).create(vals)
        if vals.get("fiscal_position_id"):
            invoice.onchange_fiscal_position_id_lroe_vat_regime_key()
        return invoice

    @api.onchange("fiscal_position_id")
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

    @api.multi
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

    @api.multi
    def _get_batuz_description(self):
        """Concatenamos la referencia/descripción de la factura con el
        número interno de la misma. De esta forma es más sencillo identificarla
        en el sistema de hacienda."""
        self.ensure_one()
        description = self.number
        if self.name:
            description += ' | ' + self.name
        return description

    def batuz_get_supplier_serie_factura(self):
        """Consultamos a hacienda cómo extraer la serie de una factura de proveedor.
        Al no ser posible en algunos casos, decidimos tomar ciertos caracteres
        como serie y el resto como número.
        Aunque la serie no es obligatoria en facturas recibidas,
        sí lo es en las rectificativas, por lo que es necesario informarla siempre."""
        return self.reference[:3]

    def _get_amount_company_currency(self, amount=0.0):
        """Convertimos el importe amount a la moneda de la compañía."""
        if self.currency_id != self.company_id.currency_id:
            currency = self.currency_id.with_context(
                date=self._get_currency_rate_date(),
                company_id=self.company_id.id
                )
            amount_cur = currency.compute(
                amount,
                self.company_id.currency_id
                )
        else:
            amount_cur = amount
        return amount_cur

    def batuz_get_supplier_num_factura(self):
        return self.reference[3:]

    @api.multi
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
        country_code = partner._parse_aeat_vat_info()[0]
        if idtype == TicketBaiCustomerIdType.T02.value:
            if country_code != "ES":
                id_type = "06" if vat == "NO_DISPONIBLE" else "02"
                res["IDOtro"] = OrderedDict(
                    [
                        ("IDType", id_type),
                        ("ID", vat),
                    ]
                )
            else:
                res["NIF"] = vat[2:] if vat.startswith(country_code) else vat
        elif idtype:
            res["IDOtro"] = OrderedDict([
                ("CodigoPais", country_code),
                ("IDType", idtype),
                ("ID", vat),
            ])
        res["ApellidosNombreRazonSocial"] = \
            partner.tbai_get_value_apellidos_nombre_razon_social()
        return res

    @api.multi
    def _is_lroe_simplified_invoice(self):
        """Inheritable method to allow control when an
        invoice are simplified or normal"""
        partner = self.partner_id.commercial_partner_id
        is_simplified = partner.lroe_simplified_invoice
        return is_simplified

    @api.multi
    def _get_operation_date(self):
        """ Inheritable method to allow set operation date of an invoice """
        self.ensure_one()
        return False

    @api.multi
    def _get_last_move_number(self):
        """Inheritable method to allow set the last number of the move when an
        invoice is move summary"""
        self.ensure_one()
        return False

    @api.multi
    def _change_date_format(self, date):
        if not date:
            return False
        datetime_object = fields.Date.from_string(date)
        new_date = datetime_object.strftime("%d-%m-%Y")
        return new_date

    @api.multi
    def _get_lroe_invoice_header(self):
        self.ensure_one()
        invoice_date = self._change_date_format(self.date_invoice)
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
        if self.type == "in_refund" and self.refund_invoice_id:
            origin = self.refund_invoice_id
            origin_date = self._change_date_format(self.refund_invoice_id.date_invoice)
            header["FacturaRectificativa"] = OrderedDict(
                [
                    ("Codigo", self.tbai_refund_key),
                    ("Tipo", self.tbai_refund_type),
                ]
            )
            if self.tbai_refund_type == "S":
                header["FacturaRectificativa"]["ImporteRectificacionSustitutiva"] = \
                    OrderedDict([
                        ("BaseRectificada", abs(origin.amount_untaxed_signed)),
                        ("CuotaRectificada", abs(
                            origin._get_amount_company_currency(origin.amount_total) -
                            origin.amount_untaxed_signed
                        )),
                        # (CuotaRecargoRectificada, False),
                    ])
            header["FacturasRectificadasSustituidas"] = OrderedDict([
                ("IDFacturaRectificadaSustituida",
                    OrderedDict([
                        ("SerieFactura",
                            origin.batuz_get_supplier_serie_factura()[:20]),
                        ("NumFactura", origin.batuz_get_supplier_num_factura()[:20]),
                        ("FechaExpedicionFactura", origin_date)
                    ])),
            ])
        return header

    @api.multi
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

    @api.multi
    def _get_lroe_taxes_map(self, codes):
        """Return the codes that correspond to that LROE map line codes.

        :param self: Invoice record
        :param codes: List of code strings to get the mapping.
        :return: Recordset with the corresponding codes
        """
        self.ensure_one()
        tbai_maps = self.env["tbai.tax.map"].search([("code", "in", codes)])
        tax_templates = tbai_maps.mapped("tax_template_ids")
        return self.env['l10n.es.aeat.report'].new(
            {'company_id': self.company_id.id}).get_taxes_from_templates(
                tax_templates)

    @api.multi
    def _get_lroe_sign(self):
        self.ensure_one()
        return -1.0 if self.tbai_refund_type == "I" and "refund" in self.type else 1.0

    @api.multi
    def _get_lroe_tax_line_req(self, tax):
        """Get the invoice tax line for 'Recargo equivalencia'.

        :param self: Single invoice record.
        :param tax: Initial tax for searching for the RE twin tax.
        :return: Invoice tax line (if any) for the correspondent RE tax.
        """
        self.ensure_one()
        taxes_re = self._get_lroe_taxes_map(["RE"])
        inv_lines = self.invoice_line_ids.filtered(
            lambda x: tax in x.mapped("invoice_line_tax_ids")
        )
        re_tax = inv_lines.mapped("invoice_line_tax_ids").filtered(
            lambda x: x in taxes_re
        )
        if len(re_tax) > 1:
            raise exceptions.UserError(
                _("There's a mismatch in taxes for RE. Check them.")
            )
        return self.tax_line_ids.filtered(lambda x: x.tax_id == re_tax)

    @api.model
    def _get_lroe_tax_dict(self, tax_line, sign, deductible=True):
        """Get the LROE tax dictionary for the passed tax line.
        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :param sign: Sign of the operation (only refund by differences is
          negative).
        :param deductible: is deductible or not
        :return: A dictionary with the corresponding LROE tax values.
        """
        tax = tax_line.tax_id
        if tax.amount_type == "group":
            tax_type = abs(tax.children_tax_ids.filtered("amount")[:1].amount)
        else:
            tax_type = abs(tax.amount)

        base = self._get_amount_company_currency(tax_line.base)
        cuota = self._get_amount_company_currency(tax_line.amount_total)

        if self.company_id.lroe_model == "240":
            tax_dict = OrderedDict(
                [
                    ("CompraBienesCorrientesGastosBienesInversion", "C"),  # C, G o I
                    ("InversionSujetoPasivo", "N"),
                    ("BaseImponible", sign * base),
                    ("TipoImpositivo", str(tax_type)),
                    ("CuotaIVASoportada", sign * cuota),
                    ("CuotaIVADeducible", (sign * cuota) * int(deductible)),
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
                    ("BaseImponible", sign * base),
                    ("TipoImpositivo", str(tax_type)),
                    ("CuotaIVASoportada", sign * cuota),
                    ("CuotaIVADeducible", (sign * cuota) * int(deductible)),
                    # TODO: 140 - ImporteGastoIRPF
                    # TODO: 140 - CriterioCobrosYPagos
                ]
            )
            # Recargo de equivalencia
            re_tax_line = self._get_lroe_tax_line_req(tax)
            if re_tax_line:
                tax_dict["TipoRecargoEquivalencia"] = abs(re_tax_line.tax_id.amount)
                tax_dict["CuotaRecargoEquivalencia"] = sign * re_tax_line.amount
        return tax_dict

    @api.multi
    def _get_lroe_in_taxes(self, sign):
        """Get taxes for purchase invoices
        :param self: invoice record
        """
        self.ensure_one()
        lroe_model = self.company_id.lroe_model
        if lroe_model == "240":
            taxes_dict = {"IVA": {"DetalleIVA": []}}
        elif lroe_model == "140":
            taxes_dict = {"RentaIVA": {"DetalleRentaIVA": []}}
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
        tax_amount = 0.0
        not_in_amount_total = 0.0
        for tax_line in self.tax_line_ids:
            tax = tax_line.tax_id
            deductible = False
            if tax in taxes_frisp + taxes_frs + taxes_frbc + taxes_frbi:
                deductible = True
            tax_dict = self._get_lroe_tax_dict(tax_line, sign, deductible)
            if tax in taxes_not_in_total:
                amount = self._get_amount_company_currency(tax_line.amount_total)
                not_in_amount_total += amount

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

            if lroe_model == "240":
                if tax in taxes_frbc:
                    tax_dict["CompraBienesCorrientesGastosBienesInversion"] = "C"
                elif tax in taxes_frs:
                    tax_dict["CompraBienesCorrientesGastosBienesInversion"] = "G"
                elif tax in taxes_frbi:
                    tax_dict["CompraBienesCorrientesGastosBienesInversion"] = "I"

            if tax in taxes_frisp + taxes_frs + taxes_frbc:
                tax_amount += self._get_amount_company_currency(tax_line.amount_total)

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

    @api.multi
    def _get_lroe_invoice_data(self, amount_total):
        self.ensure_one()
        res = OrderedDict([
            ("DescripcionOperacion", self._get_batuz_description()[:250]),
            ("Claves", self._get_lroe_claves()),
            ("ImporteTotalFactura",
             amount_total or self._get_amount_company_currency(self.amount_total)),
            # Base imponible a coste (para grupos de IVA – nivel avanzado (240))
            # ("BaseImponibleACoste", False),
        ])
        return res

    # SPECIFIC LROE CHAPTER METHODS
    @api.multi
    def _get_lroe_140_2_1_dict(self, cancel=False):
        """
        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the invoice.
        :return: invoice (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        if cancel:
            invoice_date = self._change_date_format(self.date_invoice)
            lroe_identifier = self._get_lroe_identifier()
            lroe_identifier.pop("ApellidosNombreRazonSocial")
            id_gasto = OrderedDict([
                ("IDGasto", OrderedDict([
                    ("SerieFactura", self.batuz_get_supplier_serie_factura()[:20]),
                    ("NumFactura", self.batuz_get_supplier_num_factura[:20]),
                    ("FechaExpedicionFactura", invoice_date),
                    ("EmisorFacturaRecibida", lroe_identifier),
                ]))
            ])
            inv_dict = OrderedDict([
                ("Gasto", id_gasto)
            ])
        else:
            # Check if refund type is "By differences". Negative amounts!
            sign = self._get_lroe_sign()
            taxes_dict, tax_amount, not_in_amount_total = self._get_lroe_in_taxes(sign)
            amount_total = (
                abs(self._get_amount_company_currency(self.amount_total))
                - not_in_amount_total
            ) * sign
            inv_dict = OrderedDict([
                ("Gasto", OrderedDict([
                    ("EmisorFacturaRecibida", self._get_lroe_identifier()),
                    ("CabeceraFactura", self._get_lroe_invoice_header()),
                    ("DatosFactura", self._get_lroe_invoice_data(amount_total)),
                    ("RentaIVA", taxes_dict["RentaIVA"]),
                    # ("OtraInformacionTrascendenciaTributaria", False),
                ]))
            ])
        return inv_dict

    @api.multi
    def _get_lroe_240_2_dict(self, cancel=False):
        """
        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the invoice.
        :return: invoice (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        if cancel:
            invoice_date = self._change_date_format(self.date_invoice)
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
            inv_dict = OrderedDict([
                ("FacturaRecibida", OrderedDict([(
                    "IDRecibida", id_recibida)
                ]))
            ])
        else:
            # Check if refund type is "By differences". Negative amounts!
            sign = self._get_lroe_sign()
            taxes_dict, tax_amount, not_in_amount_total = self._get_lroe_in_taxes(sign)
            amount_total = (
                abs(self._get_amount_company_currency(self.amount_total))
                - not_in_amount_total
            ) * sign
            inv_dict = OrderedDict([
                ("FacturaRecibida", OrderedDict([
                    ("EmisorFacturaRecibida", self._get_lroe_identifier()),
                    ("CabeceraFactura", self._get_lroe_invoice_header()),
                    ("DatosFactura", self._get_lroe_invoice_data(amount_total)),
                    ("IVA", taxes_dict["IVA"]),
                    # ("OtraInformacionTrascendenciaTributaria", False),
                ]))
            ])
        return inv_dict

    # COMMON LROE METHODS
    @api.model
    def _prepare_lroe_operation_values(
        self, company_id=False, optn_type=None, chapter=None, subchapter=None
    ):
        """
        Buscamos lroe.operation pendiente de envío con misma operacion (type)
        y mismo capítulo + subcapítulo
        :param company_id: (int) company id
        :param type: LROEOperationEnum.value
        :param chapter: LROEChapterEnum.value
        :param subchapter: LROEChapterEnum.value
        :return: lroe.operation object if any
        """
        if not chapter or not optn_type:
            raise exceptions.ValidationError(
                _("Chapter and Operation Type are required"
                  " for search a pending LROE Operation")
            )
        chapter_id = self.env["lroe.chapter"].search([("code", "=", chapter)], limit=1)
        res = {
            "lroe_chapter_id": chapter_id.id,
            "type": optn_type.value,
        }
        if subchapter:
            subchapter_id = self.env["lroe.chapter"].search([("code", "=", subchapter)])
            res.update({
                "lroe_subchapter_id": subchapter_id.id,
            })
        if company_id:
            res.update({"company_id": company_id})
        return res

    @api.multi
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
            optn_type=operation_type,
            chapter=chapter,
            subchapter=subchapter,
        )
        lroe_operation = lroe_model.sudo().create(vals)
        return lroe_operation

    @api.multi
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
                inv_dict = getattr(
                    invoice, "_get_lroe_%s_%s_dict" % (model, action,))(cancel)
            else:
                raise exceptions.ValidationError(
                    _("LROE Build: method for model %s chapter %s not implemented!")
                    % (model, chapter)
                )
            round_by_keys(
                inv_dict,
                KEYS_TO_ROUND,
            )
            lroe_operation = invoice._get_lroe_operation(operation_type=operation_type)
            inv_vals = {
                "lroe_invoice_dict": json.dumps(inv_dict, indent=4),
                "lroe_operation_ids": [(4, lroe_operation.id)],
            }
            invoice.write(inv_vals)
            invoice.set_lroe_state_pending()
            lroe_operation.process()

    @api.multi
    def action_send_lroe_manually(self):
        lroe_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled
            and (
                x.type == "in_invoice"
                or (
                    x.type == "in_refund"
                    and x.refund_invoice_id
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
    @api.multi
    def set_lroe_state_not_sent(self):
        self.write({"lroe_state": "not_sent"})

    @api.multi
    def set_lroe_state_pending(self):
        self.write({"lroe_state": "pending"})

    @api.multi
    def set_lroe_state_error(self):
        self.write({"lroe_state": "error"})

    @api.multi
    def set_lroe_state_recorded(self):
        self.write({"lroe_state": "recorded"})

    @api.multi
    def set_lroe_state_recorded_warning(self):
        self.write({"lroe_state": "recorded_warning"})

    @api.multi
    def set_lroe_state_recorded_modified(self):
        self.write({"lroe_state": "recorded_modified"})

    @api.multi
    def set_lroe_state_cancel(self):
        self.write({"lroe_state": "cancel"})

    @api.multi
    def set_lroe_state_cancel_modified(self):
        self.write({"lroe_state": "cancel_modified"})

    # INHERITED INVOICE METHODS
    @api.multi
    def action_cancel(self):
        if not self.mapped("lroe_operation_ids")._cancel_jobs():
            raise exceptions.Warning(
                _(
                    "You can not cancel this invoice because"
                    " there is a job running!"
                )
            )
        res = super().action_cancel()
        lroe_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled
            and x.date and x.date >= x.journal_id.tbai_active_date
            and (
                x.type == "in_invoice"
                or (
                    x.type == "in_refund"
                    and x.refund_invoice_id
                    and x.tbai_refund_type
                    in (RefundType.differences.value, RefundType.substitution.value)
                )
            )
        )
        for invoice in lroe_invoices:
            # If the LORE operation hasn't been sent yet.
            # It's not necessary a trace or register of the operation.
            # We can cancel the invoice and remove the LROE information.
            if invoice.lroe_state in ("pending", "error"):
                invoice.sudo().lroe_response_line_ids.unlink()
                invoice.sudo().lroe_operation_ids.unlink()
                invoice.update({
                    "lroe_state": "not_sent",
                    'lroe_response_line_ids': False,
                    'lroe_operation_ids': False,
                    'lroe_invoice_dict': False,
                })
            elif invoice.lroe_state in (
                    "recorded", "recorded_warning", "recorded_modified"):
                invoice.set_lroe_state_recorded_modified()
                lroe_invoices._prepare_invoice_for_lroe(
                    operation_type=LROEOperationEnum.cancel
                )

        return res

    @api.multi
    def action_invoice_draft(self):
        if not self.sudo().mapped("lroe_operation_ids")._cancel_jobs():
            raise exceptions.Warning(
                _(
                    "You can not set to draft this invoice because"
                    " there is a job running!"
                )
            )
        return super().action_invoice_draft()

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        lroe_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled
            and x.date and x.date >= x.journal_id.tbai_active_date
            and (
                x.type == "in_invoice"
                or (
                    x.type == "in_refund"
                    and x.refund_invoice_id
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
    def _prepare_refund(
        self, invoice, date_invoice=None, date=None, description=None, journal_id=None
    ):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice,
            date_invoice=date_invoice,
            date=date,
            description=description,
            journal_id=journal_id,
        )
        supplier_invoice_number_refund = \
            self.env.context.get("batuz_supplier_invoice_number")
        if supplier_invoice_number_refund:
            res["reference"] = supplier_invoice_number_refund
        return res
