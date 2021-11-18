# Copyright (2021) Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, _, exceptions, api
from collections import OrderedDict
import base64
import gzip
from datetime import datetime
from lxml import etree
from ..lroe.lroe_xml_schema import LROEXMLSchema,\
    LROEXMLSchemaModeNotSupported,\
    LROEOperationTypeEnum
from enum import Enum


class LROEModelEnum(Enum):
    model_pj_240 = '240'
    model_pf_140 = '140'


class LROEChapterEnum(Enum):
    chapter_pj_240 = '1'
    chapter_pj_240_full = '1- Facturas emitidas'
    chapter_pf_140 = '1'
    chapter_pf_140_full = '1 - Ingresos y facturas emitidas'
    subchapter_pj_240 = '1.1'
    subchapter_pj_240_full = '1.1 - Facturas emitidas con Software garante'
    subchapter_pf_140 = '1.1'
    subchapter_pf_140_full = '1.1 - Ingresos con facturas con Software garante'


class LROEOperationEnum(Enum):
    create = 'A00'
    cancel = 'AN0'
    update = 'M00'
    query = 'C00'


class LROEOperationStateEnum(Enum):
    DRAFT = 'draft'
    ERROR = 'error'
    CANCEL = 'cancel'
    RECORDED_WARNING = 'recorded_warning'
    RECORDED = 'recorded'


class LROEOperationVersion(Enum):
    v1 = '1.0'


class LROEOperation(models.Model):
    _name = "lroe.operation"
    _description = "LROE Operation"
    _order = 'id desc'

    name = fields.Char(compute='_compute_lroe_operation_name', store=True)
    company_id = fields.Many2one('res.company', required=True)
    type = fields.Selection([
        (LROEOperationEnum.create.value, 'Create'),
        (LROEOperationEnum.cancel.value, 'Cancel'),
        (LROEOperationEnum.update.value, 'Update'),
        (LROEOperationEnum.query.value, 'Query')],
        string="Type",
        required=True,
        default=LROEOperationEnum.create.value)
    model = fields.Selection(
        "Model",
        related='company_id.lroe_model',
        readonly=True,
        required=True)
    state = fields.Selection(
        selection=[(LROEOperationStateEnum.DRAFT.value, 'Draft'),
                   (LROEOperationStateEnum.ERROR.value, 'Error'),
                   (LROEOperationStateEnum.CANCEL.value, 'Cancel'),
                   (LROEOperationStateEnum.RECORDED_WARNING.value, 'Recorded Warning'),
                   (LROEOperationStateEnum.RECORDED.value, 'Recorded')],
        string="State",
        default=LROEOperationStateEnum.DRAFT.value)
    tbai_invoice_ids = fields.One2many(
        comodel_name='tbai.invoice',
        inverse_name='lroe_operation_id',
        string="TBai Customer Invoices")
    xml_datas = fields.Binary()
    xml_datas_fname = fields.Char('XML File Name')
    xml_file_size = fields.Integer('File Size')
    trx_gzip_file = fields.Binary()
    trx_gzip_fname = fields.Char('XML File Name')
    trx_gzip_fsize = fields.Integer('File Size')
    response_ids = fields.One2many(comodel_name='lroe.operation.response',
                                   inverse_name='lroe_operation_id',
                                   string="Operation global responses")

    @api.depends('model', 'type')
    def _compute_lroe_operation_name(self):
        for lroe_operation in self:
            lroe_operation.name = lroe_operation._get_printed_report_name()

    def _get_printed_report_name(self):
        self.ensure_one()
        report_name = None
        if self.model == LROEModelEnum.model_pj_240.value:
            if self.type == LROEOperationEnum.create.value:
                report_name = _('LROE_model_pj_240_create') + '_' + str(self.id)
            elif self.type == LROEOperationEnum.cancel.value:
                report_name = _('LROE_model_pj_240_cancel') + '_' + str(self.id)
        elif self.model == LROEModelEnum.model_pf_140.value:
            if self.type == LROEOperationEnum.create.value:
                report_name = _('LROE_model_pf_140_create') + '_' + str(self.id)
            elif self.type == LROEOperationEnum.cancel.value:
                report_name = _('LROE_model_pf_140_cancel') + '_' + str(self.id)
        return report_name

    @api.multi
    def set_trx_gzip_file(self):
        self.ensure_one()
        data_content = gzip.compress(base64.b64decode(self.xml_datas))
        data_length = len(data_content)
        self.trx_gzip_file = base64.b64encode(data_content)
        self.trx_gzip_fname = self.xml_datas_fname + '.gz'
        self.trx_gzip_fsize = data_length
        return str(data_length), data_content

    def build_ingresos(self, lroe_op_enum):

        def build_renta():
            # TODO LROE
            res_dict = {
                "DetalleRenta": OrderedDict([
                    ("Epigrafe", "197330"),
                    # ("IngresoAComputarIRPFDiferenteBaseImpoIVA", ""),
                    # ("ImporteIngresoIRPF", ""),
                    # ("CriterioCobros", "")
                ])}
            return res_dict

        self.ensure_one()
        ingresos = []
        if self.tbai_invoice_ids:
            if lroe_op_enum == LROEOperationEnum.create.value:
                for tbai_customer_invoice_id in self.tbai_invoice_ids:
                    ingresos.append(OrderedDict([
                        ("TicketBai", tbai_customer_invoice_id.datas),
                        ("Renta", build_renta()),
                    ]))
            elif lroe_op_enum == LROEOperationEnum.cancel.value:
                for tbai_customer_cancel_id in self.tbai_invoice_ids:
                    ingresos.append(OrderedDict([
                        ("AnulacionTicketBai",
                         tbai_customer_cancel_id.datas)]))
        return {'Ingreso': ingresos}

    def build_facturas_emitidas(self, lroe_op_enum):
        self.ensure_one()
        facturas_emitidas = []
        if self.tbai_invoice_ids:
            if lroe_op_enum == LROEOperationEnum.create.value:
                for tbai_customer_invoice_id in self.tbai_invoice_ids:
                    facturas_emitidas.append(OrderedDict([
                        ("TicketBai",
                         tbai_customer_invoice_id.datas)]))
            elif lroe_op_enum == LROEOperationEnum.cancel.value:
                for tbai_customer_cancel_id in self.tbai_invoice_ids:
                    facturas_emitidas.append(OrderedDict([
                        ("AnulacionTicketBai",
                         tbai_customer_cancel_id.datas)]))
        return {'FacturaEmitida': facturas_emitidas}

    def build_cabecera_ejercicio(self, lroe_op_enum):
        self.ensure_one()
        if self.tbai_invoice_ids:
            if lroe_op_enum == LROEOperationEnum.create.value:
                return str(datetime.strptime(
                    self.tbai_invoice_ids[0].expedition_date,
                    '%d-%m-%Y').date().year)
            elif lroe_op_enum == LROEOperationEnum.cancel.value:
                return str(datetime.strptime(
                    self.tbai_invoice_ids[0].expedition_date,
                    '%d-%m-%Y').date().year)
        return str(datetime.now().year)

    def build_obligado_tributario(self):
        partner = self.company_id.partner_id
        nif = partner.tbai_get_value_nif()
        if not nif:
            raise exceptions.ValidationError(_(
                "Company %s VAT number should not be empty!") % partner.name)
        return OrderedDict([
            ("NIF", nif),
            ("ApellidosNombreRazonSocial",
                partner.tbai_get_value_apellidos_nombre_razon_social())
        ])

    def build_cabecera_pj_240(self, lroe_op_enum):
        self.ensure_one()
        return OrderedDict([
            ("Modelo", LROEModelEnum.model_pj_240.value),
            ("Capitulo", LROEChapterEnum.chapter_pj_240.value),
            ("Subcapitulo", LROEChapterEnum.subchapter_pj_240.value),
            ("Operacion", lroe_op_enum),
            ("Version", LROEOperationVersion.v1.value),
            ("Ejercicio", self.build_cabecera_ejercicio(lroe_op_enum)),
            ("ObligadoTributario", self.build_obligado_tributario()),
        ])

    def build_cabecera_pf_140(self, lroe_op_enum):
        self.ensure_one()
        return OrderedDict([
            ("Modelo", LROEModelEnum.model_pf_140.value),
            ("Capitulo", LROEChapterEnum.chapter_pf_140.value),
            ("Subcapitulo", LROEChapterEnum.subchapter_pf_140.value),
            ("Operacion", lroe_op_enum),
            ("Version", LROEOperationVersion.v1.value),
            ("Ejercicio", self.build_cabecera_ejercicio(lroe_op_enum)),
            ("ObligadoTributario", self.build_obligado_tributario()),
        ])

    def build_xml_pj_240(self, lroe_type_enum):
        self.ensure_one()
        res_dict = {}
        root_xml_pj_240 = None
        lroe_op_enum = None
        if lroe_type_enum == LROEOperationTypeEnum.alta_sg_invoice_pj_240.value:
            lroe_op_enum = LROEOperationEnum.create.value
            root_xml_pj_240 = "LROEPJ240FacturasEmitidasConSGAltaPeticion"
        elif lroe_type_enum == LROEOperationTypeEnum.cancel_sg_invoice_pj_240.value:
            lroe_op_enum = LROEOperationEnum.cancel.value
            root_xml_pj_240 = "LROEPJ240FacturasEmitidasConSGAnulacionPeticion"
        if root_xml_pj_240:
            res_dict = {root_xml_pj_240: OrderedDict([
                ("Cabecera", self.build_cabecera_pj_240(lroe_op_enum)),
                ("FacturasEmitidas", self.build_facturas_emitidas(lroe_op_enum)),
            ])}
        return res_dict

    def build_xml_pf_140(self, lroe_type_enum):
        self.ensure_one()
        res_dict = {}
        root_xml_pf_140 = None
        lroe_op_enum = None
        if lroe_type_enum == LROEOperationTypeEnum.alta_sg_invoice_pf_140.value:
            lroe_op_enum = LROEOperationEnum.create.value
            root_xml_pf_140 = "LROEPF140IngresosConFacturaConSGAltaPeticion"
        elif lroe_type_enum == LROEOperationTypeEnum.cancel_sg_invoice_pf_140.value:
            lroe_op_enum = LROEOperationEnum.cancel.value
            root_xml_pf_140 = "LROEPF140IngresosConFacturaConSGAnulacionPeticion"
        if root_xml_pf_140:
            res_dict = {root_xml_pf_140: OrderedDict([
                ("Cabecera", self.build_cabecera_pf_140(lroe_op_enum)),
                ("Ingresos", self.build_ingresos(lroe_op_enum)),
            ])}
        return res_dict

    def get_lroe_operations_xml(self):
        self.ensure_one()
        operation_type = None
        if self.model == LROEModelEnum.model_pj_240.value:
            if self.type == LROEOperationEnum.create.value:
                operation_type = LROEOperationTypeEnum.alta_sg_invoice_pj_240.value
            elif self.type == LROEOperationEnum.cancel.value:
                operation_type = LROEOperationTypeEnum.cancel_sg_invoice_pj_240.value
            lroe_xml_schema = LROEXMLSchema(operation_type)
            my_ordered_dict = self.build_xml_pj_240(operation_type)
        elif self.model == LROEModelEnum.model_pf_140.value:
            if self.type == LROEOperationEnum.create.value:
                operation_type = LROEOperationTypeEnum.alta_sg_invoice_pf_140.value
            elif self.type == LROEOperationEnum.cancel.value:
                operation_type = LROEOperationTypeEnum.cancel_sg_invoice_pf_140.value
            lroe_xml_schema = LROEXMLSchema(operation_type)
            my_ordered_dict = self.build_xml_pf_140(operation_type)
        else:
            raise LROEXMLSchemaModeNotSupported(
                "TicketBAI - Batuz LROE XML model not supported!")
        if lroe_xml_schema and my_ordered_dict:
            return lroe_xml_schema.dict2xml(my_ordered_dict)

    def build_xml_file(self):
        self.ensure_one()
        if self.tbai_invoice_ids:
            root = self.get_lroe_operations_xml()
            root_str = etree.tostring(root, xml_declaration=True, encoding='utf-8')
            self.xml_datas = base64.b64encode(root_str)
            self.xml_datas_fname = self._get_printed_report_name() + '.xml'
            self.xml_file_size = len(root_str)
            self.state = 'draft'
