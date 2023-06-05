# Copyright (2021) Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import gzip
import json
from collections import OrderedDict
from datetime import datetime
from enum import Enum

from lxml import etree

from odoo import _, api, exceptions, fields, models

from ..lroe.lroe_xml_schema import (
    LROEOperationTypeEnum,
    LROEXMLSchema,
    LROEXMLSchemaModeNotSupported,
)


class LROEModelEnum(Enum):
    model_pj_240 = "240"
    model_pf_140 = "140"


class LROEChapterEnum(Enum):
    chapter_pj_240 = "1"
    chapter_pj_240_full = "1- Facturas emitidas"
    subchapter_pj_240 = "1.1"
    subchapter_pj_240_full = "1.1 - Facturas emitidas con Software garante"
    chapter_pj_240_2 = "2"
    chapter_pj_240_2_full = "2 - Facturas recibidas"
    chapter_pj_240_3 = "3"
    chapter_pj_240_3_full = "3 - Bienes de inversión"
    chapter_pj_240_4 = "4"
    chapter_pj_240_4_full = "4 - Determinadas operaciones intracomunitarias"
    subchapter_pj_240_4_1 = "4.1"
    subchapter_pj_240_4_1_full = (
        "4.1 - Transferencias instracomunitarias, informes periciales y otros trabajos"
    )
    subchapter_pj_240_4_2 = "4.2"
    subchapter_pj_240_4_2_full = "4.2 - Ventas de bienes en consigna"
    chapter_pj_240_5 = "5"
    chapter_pj_240_5_full = "5 - Criterio de caja"
    subchapter_pj_240_5_1 = "5.1"
    subchapter_pj_240_5_1_full = "5.1 - Cobros"
    subchapter_pj_240_5_2 = "5.2"
    subchapter_pj_240_5_2_full = "5.2 - Pagos"
    chapter_pj_240_6 = "6"
    chapter_pj_240_6_full = "6 - Otra información con trascendencia tributaria"
    subchapter_pj_240_6_1 = "6.1"
    subchapter_pj_240_6_1_full = (
        "6.1 - Importes superiores a 6.000 euros percibidos en metálico"
    )
    subchapter_pj_240_6_2 = "6.2"
    subchapter_pj_240_6_2_full = "6.2 - Operaciones de seguros"
    subchapter_pj_240_6_3 = "6.2"
    subchapter_pj_240_6_3_full = "6.2 - Agenciasde viajes"

    chapter_pf_140 = "1"
    chapter_pf_140_full = "1 - Ingresos y facturas emitidas"
    subchapter_pf_140 = "1.1"
    subchapter_pf_140_full = "1.1 - Ingresos con facturas con Software garante"
    chapter_pf_140_2 = "2"
    chapter_pf_140_2_full = "2 - Gastos y facturas recibidas"
    subchapter_pf_140_2_1 = "2.1"
    subchapter_pf_140_2_1_full = "2.1 - Gastos con factura"
    subchapter_pf_140_2_2 = "2.2"
    subchapter_pf_140_2_2_full = "2.2 - Gastos sin factura"
    chapter_pf_140_3 = "3"
    chapter_pf_140_3_full = "3 - Bienes afectos o de inversión"
    subchapter_pf_140_3_1 = "3.1"
    subchapter_pf_140_3_1_full = "3.1 - Alta de bienes afectos o de inversión"
    subchapter_pf_140_3_2 = "3.2"
    subchapter_pf_140_3_2_full = "3.2 - Mejora debienes afectos o de inversión"
    subchapter_pf_140_3_3 = "3.3"
    subchapter_pf_140_3_3_full = "3.3 - Baja de bienes afectos o de inversión"
    subchapter_pf_140_3_4 = "3.4"
    subchapter_pf_140_3_4_full = "3.4 - Regularización anual de bienes de inversión"
    chapter_pf_140_4 = "4"
    chapter_pf_140_4_full = "4 - Determinadas operaciones intracomunitarias"
    subchapter_pf_140_4_1 = "4.1"
    subchapter_pf_140_4_1_full = (
        "4.1 - Transferencias intracomunitarias, informes periciales y otros trabajos"
    )
    subchapter_pf_140_4_2 = "4.2"
    subchapter_pf_140_4_2_full = "4.2 - Ventas de bienes en consigna"
    chapter_pf_140_5 = "5"
    chapter_pf_140_5_full = "5 - Criterio de caja / Criterio de cobros y pagos"
    subchapter_pf_140_5_1 = "5.1"
    subchapter_pf_140_5_1_full = "5.1 - Cobros"
    subchapter_pf_140_5_2 = "5.2"
    subchapter_pf_140_5_2_full = "5.2 - Pagos"
    chapter_pf_140_6 = "6"
    chapter_pf_140_6_full = "6 - Provisiones y suplidos"
    chapter_pf_140_7 = "7"
    chapter_pf_140_7_full = "7 - Otra información con trascendencia tributaria"
    subchapter_pf_140_7_1 = "7.1"
    subchapter_pf_140_7_1_full = "7.1 - Variación de existencias"
    subchapter_pf_140_7_2 = "7.2"
    subchapter_pf_140_7_2_full = "7.2 - Arrendamientos de locales de negocios"
    subchapter_pf_140_7_3 = "7.3"
    subchapter_pf_140_7_3_full = "7.3 - Transmisiones de inmuebles sujetas a IVA"
    subchapter_pf_140_7_4 = "7.4"
    subchapter_pf_140_7_4_full = (
        "7.4 - Importes superiores a 6.000 euros percibidos en metálico"
    )
    chapter_pf_140_8 = "8"
    chapter_pf_140_8_full = "8 - Criterio de caja / Criterio de cobros y pagos"
    subchapter_pf_140_8_1 = "8.1"
    subchapter_pf_140_8_1_full = "8.1 - Alta de agrupaciones de bienes"
    subchapter_pf_140_8_2 = "8.2"
    subchapter_pf_140_8_2_full = "8.2 - Baja de agrupaciones de bienes"


class LROEOperationEnum(Enum):
    create = "A00"
    cancel = "AN0"
    update = "M00"
    query = "C00"


class LROEOperationStateEnum(Enum):
    DRAFT = "draft"
    ERROR = "error"
    CANCEL = "cancel"
    RECORDED_WARNING = "recorded_warning"
    RECORDED = "recorded"


class LROEOperationVersion(Enum):
    v1 = "1.0"


class LROEChapter(models.Model):
    _name = "lroe.chapter"
    _description = "LROE Chapter"
    _order = "model, code, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    model = fields.Selection(
        [
            (LROEModelEnum.model_pj_240.value, "LROE PJ 240"),
            (LROEModelEnum.model_pf_140.value, "LROE PF 140"),
        ],
        string="LROE Model",
        required=True,
        default=LROEModelEnum.model_pj_240.value,
    )
    lroe_chapter_id = fields.Many2one(
        comodel_name="lroe.chapter", string="Parent chapter"
    )


class LROEOperation(models.Model):
    _name = "lroe.operation"
    _description = "LROE Operation"
    _order = "id desc"

    name = fields.Char(compute="_compute_lroe_operation_name", store=True)
    company_id = fields.Many2one("res.company", required=True)
    type = fields.Selection(
        [
            (LROEOperationEnum.create.value, "Create"),
            (LROEOperationEnum.cancel.value, "Cancel"),
            (LROEOperationEnum.update.value, "Update"),
            (LROEOperationEnum.query.value, "Query"),
        ],
        required=True,
        default=LROEOperationEnum.create.value,
    )
    model = fields.Selection(
        related="company_id.lroe_model", readonly=True, required=True
    )
    state = fields.Selection(
        selection=[
            (LROEOperationStateEnum.DRAFT.value, "Draft"),
            (LROEOperationStateEnum.ERROR.value, "Error"),
            (LROEOperationStateEnum.CANCEL.value, "Cancel"),
            (LROEOperationStateEnum.RECORDED_WARNING.value, "Recorded Warning"),
            (LROEOperationStateEnum.RECORDED.value, "Recorded"),
        ],
        default=LROEOperationStateEnum.DRAFT.value,
    )
    tbai_invoice_ids = fields.One2many(
        comodel_name="tbai.invoice",
        inverse_name="lroe_operation_id",
        string="TBai Customer Invoices",
    )
    xml_datas = fields.Binary()
    xml_datas_fname = fields.Char("XML File Name")
    xml_file_size = fields.Integer("XML File Size")
    trx_gzip_file = fields.Binary()
    trx_gzip_fname = fields.Char("GZIP File Name")
    trx_gzip_fsize = fields.Integer("GZIP File Size")
    response_ids = fields.One2many(
        comodel_name="lroe.operation.response",
        inverse_name="lroe_operation_id",
        string="Operation global responses",
    )
    lroe_chapter_id = fields.Many2one(
        comodel_name="lroe.chapter", string="Chapter", required=True
    )
    lroe_subchapter_id = fields.Many2one(
        comodel_name="lroe.chapter",
        string="Subchapter",
    )

    @api.depends("model", "type")
    def _compute_lroe_operation_name(self):
        for lroe_operation in self:
            lroe_operation.name = lroe_operation._get_printed_report_name()

    def _get_printed_report_name(self):
        self.ensure_one()
        report_name = self.model + "_" + self.type + "_" + str(self.id)
        if self.model == LROEModelEnum.model_pj_240.value:
            if self.type == LROEOperationEnum.create.value:
                report_name = _("LROE_model_pj_240_create") + "_" + str(self.id)
            elif self.type == LROEOperationEnum.cancel.value:
                report_name = _("LROE_model_pj_240_cancel") + "_" + str(self.id)
            elif self.type == LROEOperationEnum.update.value:
                report_name = _("LROE_model_pj_240_update") + "_" + str(self.id)
        elif self.model == LROEModelEnum.model_pf_140.value:
            if self.type == LROEOperationEnum.create.value:
                report_name = _("LROE_model_pf_140_create") + "_" + str(self.id)
            elif self.type == LROEOperationEnum.cancel.value:
                report_name = _("LROE_model_pf_140_cancel") + "_" + str(self.id)
            elif self.type == LROEOperationEnum.update.value:
                report_name = _("LROE_model_pf_140_update") + "_" + str(self.id)
        return report_name

    def set_trx_gzip_file(self):
        self.ensure_one()
        data_content = gzip.compress(base64.b64decode(self.xml_datas))
        data_length = len(data_content)
        self.trx_gzip_file = base64.b64encode(data_content)
        self.trx_gzip_fname = self.xml_datas_fname + ".gz"
        self.trx_gzip_fsize = data_length
        return str(data_length), data_content

    def build_ingresos(self):
        def build_renta():
            res_dict = {
                "DetalleRenta": OrderedDict(
                    [
                        ("Epigrafe", self.company_id.main_activity_iae),
                        # ("IngresoAComputarIRPFDiferenteBaseImpoIVA", ""),
                        # ("ImporteIngresoIRPF", ""),
                        # ("CriterioCobros", "")
                    ]
                )
            }
            return res_dict

        self.ensure_one()
        ingresos = []
        if self.tbai_invoice_ids:
            if self.type == LROEOperationEnum.create.value:
                for tbai_customer_invoice_id in self.tbai_invoice_ids:
                    ingresos.append(
                        OrderedDict(
                            [
                                ("TicketBai", tbai_customer_invoice_id.datas),
                                ("Renta", build_renta()),
                            ]
                        )
                    )
            elif self.type == LROEOperationEnum.cancel.value:
                for tbai_customer_cancel_id in self.tbai_invoice_ids:
                    ingresos.append(
                        OrderedDict(
                            [("AnulacionTicketBai", tbai_customer_cancel_id.datas)]
                        )
                    )
        return {"Ingreso": ingresos}

    def build_facturas_emitidas(self):
        self.ensure_one()
        facturas_emitidas = []
        if self.tbai_invoice_ids:
            if self.type == LROEOperationEnum.create.value:
                for tbai_customer_invoice_id in self.tbai_invoice_ids:
                    facturas_emitidas.append(
                        OrderedDict([("TicketBai", tbai_customer_invoice_id.datas)])
                    )
            elif self.type == LROEOperationEnum.cancel.value:
                for tbai_customer_cancel_id in self.tbai_invoice_ids:
                    facturas_emitidas.append(
                        OrderedDict(
                            [("AnulacionTicketBai", tbai_customer_cancel_id.datas)]
                        )
                    )
        return {"FacturaEmitida": facturas_emitidas}

    def build_cabecera_ejercicio(self):
        self.ensure_one()
        if self.tbai_invoice_ids:
            return str(
                datetime.strptime(
                    self.tbai_invoice_ids[0].expedition_date, "%d-%m-%Y"
                ).year
            )
        elif self.invoice_ids and self.invoice_ids[0].date:
            date = fields.Date.from_string(self.invoice_ids[0].date)
            return str(date.year)
        return str(datetime.now().year)

    def build_obligado_tributario(self):
        partner = self.company_id.partner_id
        nif = partner.tbai_get_value_nif()
        if not nif:
            raise exceptions.ValidationError(
                _("Company %s VAT number should not be empty!") % partner.name
            )
        return OrderedDict(
            [
                ("NIF", nif),
                (
                    "ApellidosNombreRazonSocial",
                    partner.tbai_get_value_apellidos_nombre_razon_social(),
                ),
            ]
        )

    def build_cabecera_pj_240(self):
        self.ensure_one()
        cabecera = OrderedDict()
        cabecera["Modelo"] = LROEModelEnum.model_pj_240.value
        cabecera["Capitulo"] = self.lroe_chapter_id.code
        if self.lroe_subchapter_id.code:
            # Si se informa de subcapitulo vacío hacienda devuelve error B4_1000001
            cabecera["Subcapitulo"] = self.lroe_subchapter_id.code
        cabecera["Operacion"] = self.type
        cabecera["Version"] = LROEOperationVersion.v1.value
        cabecera["Ejercicio"] = self.build_cabecera_ejercicio()
        cabecera["ObligadoTributario"] = self.build_obligado_tributario()
        return cabecera

    def build_cabecera_pf_140(self):
        self.ensure_one()
        cabecera = OrderedDict()
        cabecera["Modelo"] = LROEModelEnum.model_pf_140.value
        cabecera["Capitulo"] = self.lroe_chapter_id.code
        if self.lroe_subchapter_id.code:
            # Si se informa de subcapitulo vacío hacienda devuelve error B4_1000001
            cabecera["Subcapitulo"] = self.lroe_subchapter_id.code
        cabecera["Operacion"] = self.type
        cabecera["Version"] = LROEOperationVersion.v1.value
        cabecera["Ejercicio"] = self.build_cabecera_ejercicio()
        cabecera["ObligadoTributario"] = self.build_obligado_tributario()
        return cabecera

    def build_xml_240_1_1(self):
        self.ensure_one()
        res_dict = {}
        if self.type in (
            LROEOperationEnum.create.value,
            LROEOperationEnum.update.value,
        ):
            lroe_type_enum = LROEOperationTypeEnum.alta_sg_invoice_pj_240.value
        elif self.type == LROEOperationEnum.cancel.value:
            lroe_type_enum = LROEOperationTypeEnum.cancel_sg_invoice_pj_240.value
        lroe_xml_schema = LROEXMLSchema(lroe_type_enum)
        if lroe_xml_schema:
            res_dict = {
                lroe_xml_schema.root_element: OrderedDict(
                    [
                        ("Cabecera", self.build_cabecera_pj_240()),
                        ("FacturasEmitidas", self.build_facturas_emitidas()),
                    ]
                )
            }
        return res_dict, lroe_xml_schema

    def build_xml_140_1_1(self):
        self.ensure_one()
        res_dict = {}
        if self.type in (
            LROEOperationEnum.create.value,
            LROEOperationEnum.update.value,
        ):
            lroe_type_enum = LROEOperationTypeEnum.alta_sg_invoice_pf_140.value
        elif self.type == LROEOperationEnum.cancel.value:
            lroe_type_enum = LROEOperationTypeEnum.cancel_sg_invoice_pf_140.value
        lroe_xml_schema = LROEXMLSchema(lroe_type_enum)
        if lroe_xml_schema:
            res_dict = {
                lroe_xml_schema.root_element: OrderedDict(
                    [
                        ("Cabecera", self.build_cabecera_pf_140()),
                        ("Ingresos", self.build_ingresos()),
                    ]
                )
            }
        return res_dict, lroe_xml_schema

    def build_facturas_recibidas(self):
        self.ensure_one()
        facturas_recibidas = []
        if self.invoice_ids.filtered(
            lambda ai: ai.move_type in ("in_invoice", "in_refund")
        ):
            if self.type in (
                LROEOperationEnum.create.value,
                LROEOperationEnum.update.value,
            ):
                for invoice in self.invoice_ids:
                    facturas_recibidas.append(
                        json.loads(
                            invoice.lroe_invoice_dict, object_pairs_hook=OrderedDict
                        )
                    )
            elif self.type == LROEOperationEnum.cancel.value:
                for invoice in self.invoice_ids:
                    facturas_recibidas.append(
                        json.loads(
                            invoice.lroe_invoice_dict, object_pairs_hook=OrderedDict
                        )
                    )
        return facturas_recibidas

    def build_xml_140_2_1(self):
        self.ensure_one()
        res_dict = {}
        if self.type in (
            LROEOperationEnum.create.value,
            LROEOperationEnum.update.value,
        ):
            lroe_type_enum = LROEOperationTypeEnum.alta_invoice_in_pf_140.value
        elif self.type == LROEOperationEnum.cancel.value:
            lroe_type_enum = LROEOperationTypeEnum.cancel_invoice_in_pf_140.value
        lroe_xml_schema = LROEXMLSchema(lroe_type_enum)
        if lroe_xml_schema:
            res_dict = {
                lroe_xml_schema.root_element: OrderedDict(
                    [
                        ("Cabecera", self.build_cabecera_pf_140()),
                        ("Gastos", self.build_facturas_recibidas()),
                    ]
                )
            }
        return res_dict, lroe_xml_schema

    def build_xml_240_2(self):
        self.ensure_one()
        res_dict = {}
        if self.type in (
            LROEOperationEnum.create.value,
            LROEOperationEnum.update.value,
        ):
            lroe_type_enum = LROEOperationTypeEnum.alta_invoice_in_pj_240.value
        elif self.type == LROEOperationEnum.cancel.value:
            lroe_type_enum = LROEOperationTypeEnum.cancel_invoice_in_pj_240.value
        lroe_xml_schema = LROEXMLSchema(lroe_type_enum)
        if lroe_xml_schema:
            res_dict = {
                lroe_xml_schema.root_element: OrderedDict(
                    [
                        ("Cabecera", self.build_cabecera_pj_240()),
                        ("FacturasRecibidas", self.build_facturas_recibidas()),
                    ]
                )
            }
        return res_dict, lroe_xml_schema

    def get_lroe_operations_xml(self):
        """Se concatena el modelo + capitulo/subcatpitulo y se busca el
        metodo especifico para crear el xml"""
        self.ensure_one()
        subchapter = self.lroe_subchapter_id
        action = (
            subchapter.code.replace(".", "_")
            if subchapter
            else self.lroe_chapter_id.code
        )
        if hasattr(
            self,
            "build_xml_%s_%s"
            % (
                self.model,
                action,
            ),
        ):
            my_ordered_dict, lroe_xml_schema = getattr(
                self,
                "build_xml_%s_%s"
                % (
                    self.model,
                    action,
                ),
            )()
        else:
            raise LROEXMLSchemaModeNotSupported("Batuz LROE XML model not supported!")
        if my_ordered_dict and lroe_xml_schema:
            return lroe_xml_schema.dict2xml(my_ordered_dict)

    def build_xml_file(self):
        self.ensure_one()
        root = self.get_lroe_operations_xml()
        root_str = etree.tostring(root, xml_declaration=True, encoding="utf-8")
        self.xml_datas = base64.b64encode(root_str)
        self.xml_datas_fname = self._get_printed_report_name() + ".xml"
        self.xml_file_size = len(root_str)
        self.state = LROEOperationStateEnum.DRAFT.value
