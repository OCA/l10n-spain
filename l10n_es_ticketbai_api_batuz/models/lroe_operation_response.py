# Copyright (2021) Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from enum import Enum

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_response import (
    TicketBaiCancellationResponseCode,
    TicketBaiInvoiceResponseCode,
    TicketBaiResponseState,
)
from odoo.addons.l10n_es_ticketbai_api.utils import utils as tbai_utils

from ..lroe.lroe_xml_schema import (
    LROEOperationTypeEnum,
    LROEXMLSchema,
    LROEXMLSchemaModeNotSupported,
)
from .lroe_operation import LROEModelEnum, LROEOperationEnum


class LROEOperationResponseState(Enum):
    BUILD_ERROR = "-2"
    REQUEST_ERROR = "-1"
    CORRECT = "Correcto"
    PARTIALLY_CORRECT = "ParcialmenteCorrecto"
    INCORRECT = "Incorrecto"


class LROEOperationResponseLineState(Enum):
    CORRECT = "Correcto"
    CORRECT_WITH_ERRORS = "AceptadoConErrores"
    INCORRECT = "Incorrecto"


class LROEOperationResponseLineCode(tbai_utils.EnumValues):
    DUPLICATED_RECORD = "B4_2000003"
    ALREADY_CANCELLED_RECORD = "B4_2000006"


class LROEOperationResponse(models.Model):
    _name = "lroe.operation.response"
    _description = "LROE Operation Response"

    lroe_operation_id = fields.Many2one(
        comodel_name="lroe.operation", required=True, ondelete="cascade"
    )
    response_line_ids = fields.One2many(
        comodel_name="lroe.operation.response.line",
        inverse_name="lroe_response_id",
        string="Response Line",
    )
    xml = fields.Binary(string="XML Response")
    xml_fname = fields.Char("XML File Name")
    state = fields.Selection(
        selection=[
            (LROEOperationResponseState.BUILD_ERROR.value, "Build error"),
            (LROEOperationResponseState.REQUEST_ERROR.value, "Request error"),
            (LROEOperationResponseState.CORRECT.value, "Correct"),
            (LROEOperationResponseState.PARTIALLY_CORRECT.value, "Partially correct"),
            (LROEOperationResponseState.INCORRECT.value, "Incorrect"),
        ],
        required=True,
    )
    code = fields.Char()
    description = fields.Char()
    lroe_record_id = fields.Char()
    lroe_record_number = fields.Char()
    lroe_record_date = fields.Char()

    @staticmethod
    def get_tbai_state(lroe_response_operation):
        if (
            lroe_response_operation == LROEOperationResponseState.BUILD_ERROR.value
            or lroe_response_operation == LROEOperationResponseState.REQUEST_ERROR.value
        ):
            return lroe_response_operation
        if lroe_response_operation == LROEOperationResponseState.CORRECT.value:
            return TicketBaiResponseState.RECEIVED.value
        if lroe_response_operation == LROEOperationResponseState.INCORRECT.value:
            return TicketBaiResponseState.REJECTED.value
        if (
            lroe_response_operation
            == LROEOperationResponseState.PARTIALLY_CORRECT.value
            or lroe_response_operation
            == LROEOperationResponseLineState.CORRECT_WITH_ERRORS.value
        ):
            # TODO LROE: en caso de e envío de un único fichero se nos
            # puede dar esta respuesta ??? que hacemos ???
            return TicketBaiResponseState.RECEIVED.value
        return None

    @api.model
    def prepare_lroe_error_values(self, lroe_operation, msg, **kwargs):
        values = kwargs
        tbai_response_model = self.env["tbai.response"]
        tbai_response_dict = {
            "tbai_invoice_id": lroe_operation.tbai_invoice_ids[0].id,
            "state": LROEOperationResponse.get_tbai_state(
                LROEOperationResponseState.REQUEST_ERROR.value
            ),
        }
        tbai_response_obj = tbai_response_model.create(tbai_response_dict)
        values.update(
            {
                "lroe_operation_id": lroe_operation.id,
                "state": LROEOperationResponseState.BUILD_ERROR.value,
                "description": _("Internal API or Operation error") + msg,
                "response_line_ids": [
                    (
                        0,
                        0,
                        {
                            "state": LROEOperationResponseLineState.INCORRECT.value,
                            "tbai_response_id": tbai_response_obj.id,
                        },
                    )
                ],
            }
        )
        return values

    @api.model
    def validate_response_line_state(self, response_line_record_state):
        if response_line_record_state not in [
            LROEOperationResponseLineState.CORRECT.value,
            LROEOperationResponseLineState.CORRECT_WITH_ERRORS.value,
            LROEOperationResponseLineState.INCORRECT.value,
        ]:
            raise ValidationError(_("LROEOperationResponseLineState not VALID !"))

    @api.model
    def get_lroe_xml_schema(self, lroe_operation):
        if not lroe_operation:
            raise ValidationError(_("LROE Operation required!"))
        lroe_operation_model = (
            "pj_240"
            if LROEModelEnum.model_pj_240.value == lroe_operation.model
            else "pf_140"
        )
        operation_type_map = {
            LROEOperationEnum.create.value: "resp_alta",
            LROEOperationEnum.update.value: "resp_alta",
            LROEOperationEnum.cancel.value: "resp_cancel",
        }
        operation_chaper_map = {
            "1": "sg_invoice",
            "2": "invoice_in",
        }
        lroe_operation_type = operation_type_map[lroe_operation.type]
        lroe_operation_chapter = operation_chaper_map[
            lroe_operation.lroe_chapter_id.code
        ]
        if hasattr(
            LROEOperationTypeEnum,
            "%s_%s_%s"
            % (
                lroe_operation_type,
                lroe_operation_chapter,
                lroe_operation_model,
            ),
        ):
            operation_type = getattr(
                LROEOperationTypeEnum,
                "%s_%s_%s"
                % (
                    lroe_operation_type,
                    lroe_operation_chapter,
                    lroe_operation_model,
                ),
            ).value
            xml_schema = LROEXMLSchema(operation_type)
        else:
            raise LROEXMLSchemaModeNotSupported("Batuz LROE XML model not supported!")
        return operation_type, xml_schema

    @api.model
    def get_lroe_response_xml_records(self, xml_root):
        xml_lroe_records = xml_root.get("Registros").get("Registro")
        len_lroe_records = 0
        if isinstance(xml_lroe_records, dict):
            len_lroe_records = 1
        elif isinstance(xml_lroe_records, list):
            len_lroe_records = len(xml_lroe_records)
        return len_lroe_records, xml_lroe_records

    @api.model
    def prepare_lroe_response_values(self, lroe_srv_response, lroe_operation, **kwargs):
        def set_tbai_response_lroe_line():
            response_line_record_data = _response_line_record.get("SituacionRegistro")
            response_line_record_state = response_line_record_data.get("EstadoRegistro")
            self.validate_response_line_state(response_line_record_state)
            response_line_record_code = ""
            response_line_record_message = ""
            if (
                not response_line_record_state
                == LROEOperationResponseLineState.CORRECT.value
            ):
                response_line_record_code = response_line_record_data.get(
                    "CodigoErrorRegistro"
                )
                response_line_record_message = (
                    "(ES): "
                    + response_line_record_data.get("DescripcionErrorRegistroES")
                    + "(EU): "
                    + response_line_record_data.get("DescripcionErrorRegistroEU")
                )

            tbai_response_model = tbai_response_obj = self.env["tbai.response"]
            if lroe_operation.tbai_invoice_ids:
                tbai_msg_description = response_line_record_message
                tbai_msg_code = (
                    TicketBaiInvoiceResponseCode.INVOICE_ALREADY_REGISTERED.value
                    if LROEOperationResponseLineCode.DUPLICATED_RECORD.value
                    == response_line_record_code
                    else TicketBaiCancellationResponseCode.INVOICE_ALREADY_CANCELLED.value
                    if LROEOperationResponseLineCode.ALREADY_CANCELLED_RECORD.value
                    == response_line_record_code
                    else response_line_record_code
                    if response_line_record_code
                    else ""
                )
                tbai_response_dict = {
                    "tbai_invoice_id": lroe_operation.tbai_invoice_ids[0].id,
                    "state": LROEOperationResponse.get_tbai_state(
                        response_line_record_state
                    ),
                    "tbai_response_message_ids": [
                        (
                            0,
                            0,
                            {
                                "code": tbai_msg_code,
                                "description": tbai_msg_description,
                            },
                        )
                    ],
                }
                tbai_response_obj = tbai_response_model.create(tbai_response_dict)
            response_line_ids.append(
                (
                    0,
                    0,
                    {
                        "state": response_line_record_state,
                        "code": response_line_record_code,
                        "description": response_line_record_message,
                        "tbai_response_id": tbai_response_obj.id,
                    },
                )
            )
            if response_line_ids:
                values.update({"response_line_ids": response_line_ids})

        lroe_operation_type, lroe_xml_schema = self.get_lroe_xml_schema(lroe_operation)
        values = {}
        lroe_srv_response_type = lroe_srv_response.get_lroe_srv_response_type()
        lroe_srv_response_code = lroe_srv_response.get_lroe_srv_response_code()
        lroe_srv_response_message = lroe_srv_response.get_lroe_srv_response_message()
        lroe_srv_response_date = lroe_srv_response.get_lroe_srv_response_record_date()
        errno = lroe_srv_response.errno
        strerror = lroe_srv_response.strerror
        if lroe_srv_response.error:
            tbai_response_model = self.env["tbai.response"]
            tbai_response_dict = {
                "tbai_invoice_id": lroe_operation.tbai_invoice_ids[:1].id,
                "state": LROEOperationResponse.get_tbai_state(
                    LROEOperationResponseState.REQUEST_ERROR.value
                ),
            }
            tbai_response_obj = tbai_response_model.create(tbai_response_dict)
            values.update(
                {
                    "lroe_operation_id": lroe_operation.id,
                    "state": LROEOperationResponseState.REQUEST_ERROR.value,
                    "code": lroe_srv_response_code if lroe_srv_response_code else errno,
                    "description": lroe_srv_response_message
                    if lroe_srv_response_message
                    else strerror,
                    "response_line_ids": [
                        (
                            0,
                            0,
                            {
                                "state": LROEOperationResponseLineState.INCORRECT.value,
                                "code": lroe_srv_response_code
                                if lroe_srv_response_code
                                else errno,
                                "description": lroe_srv_response_message
                                if lroe_srv_response_message
                                else strerror,
                                "tbai_response_id": tbai_response_obj.id,
                            },
                        )
                    ],
                }
            )
        else:
            values.update(
                {
                    "lroe_operation_id": lroe_operation.id,
                    "state": lroe_srv_response_type,
                }
            )
            if lroe_srv_response_type in [
                LROEOperationResponseState.CORRECT.value,
                LROEOperationResponseState.PARTIALLY_CORRECT.value,
            ]:
                lroe_srv_rec_id = lroe_srv_response.get_lroe_srv_response_record_id()
                lroe_srv_rec_number = (
                    lroe_srv_response.get_lroe_srv_response_record_number()
                )
                values.update(
                    {
                        "lroe_record_date": lroe_srv_response_date,
                        "lroe_record_id": lroe_srv_rec_id,
                        "lroe_record_number": lroe_srv_rec_number,
                    }
                )
            else:
                values.update(
                    {
                        "lroe_record_date": lroe_srv_response_date,
                        "code": lroe_srv_response_code
                        if lroe_srv_response_code
                        else errno,
                        "description": lroe_srv_response_message
                        if lroe_srv_response_message
                        else strerror,
                    }
                )
            xml_data = lroe_srv_response.data
            if xml_data:
                values.update(
                    {
                        "xml": base64.encodebytes(xml_data),
                        "xml_fname": lroe_operation.name + "_response.xml",
                    }
                )
                xml_root = lroe_xml_schema.parse_xml(xml_data)[
                    lroe_xml_schema.root_element
                ]
                (
                    len_response_line_records,
                    response_line_records,
                ) = self.get_lroe_response_xml_records(xml_root)
                response_line_ids = []
                if len_response_line_records == 1:
                    _response_line_record = response_line_records
                    set_tbai_response_lroe_line()
                elif len_response_line_records > 1:
                    for _response_line_record in response_line_records:
                        set_tbai_response_lroe_line()
            else:
                tbai_response_model = tbai_response_obj = self.env["tbai.response"]
                if lroe_operation.tbai_invoice_ids:
                    tbai_response_dict = {
                        "tbai_invoice_id": lroe_operation.tbai_invoice_ids[0].id,
                        "state": LROEOperationResponse.get_tbai_state(
                            lroe_srv_response_type
                        ),
                    }
                    tbai_response_obj = tbai_response_model.create(tbai_response_dict)
                values.update(
                    {
                        "response_line_ids": [
                            (
                                0,
                                0,
                                {
                                    "state": LROEOperationResponseLineState.INCORRECT.value,
                                    "code": lroe_srv_response_code
                                    if lroe_srv_response_code
                                    else errno,
                                    "description": lroe_srv_response_message
                                    if lroe_srv_response_message
                                    else strerror,
                                    "tbai_response_id": tbai_response_obj.id,
                                },
                            )
                        ]
                    }
                )
        return values


class LROEOperationResponseLine(models.Model):
    _name = "lroe.operation.response.line"
    _description = "LROE Operation Response Line"
    _order = "id desc"

    lroe_response_id = fields.Many2one(
        comodel_name="lroe.operation.response", required=True, ondelete="cascade"
    )
    lroe_operation_id = fields.Many2one(
        comodel_name="lroe.operation", related="lroe_response_id.lroe_operation_id"
    )
    tbai_response_id = fields.Many2one(comodel_name="tbai.response", ondelete="cascade")
    tbai_invoice_id = fields.Many2one(
        related="tbai_response_id.tbai_invoice_id",
        comodel_name="tbai.invoice",
        required=True,
        ondelete="cascade",
    )
    state = fields.Selection(
        selection=[
            (LROEOperationResponseLineState.CORRECT.value, "Correct"),
            (
                LROEOperationResponseLineState.CORRECT_WITH_ERRORS.value,
                "Correct with errors",
            ),
            (LROEOperationResponseLineState.INCORRECT.value, "Incorrect"),
        ],
        required=True,
    )
    code = fields.Char()
    description = fields.Char()
    response_message = fields.Char(
        compute="_compute_line_message", string="LROE Response Message"
    )

    @api.depends("code", "description")
    def _compute_line_message(self):
        for response_line in self:
            if response_line.code and response_line.description:
                response_line.response_message = (
                    response_line.code + ":" + response_line.description
                )
            elif response_line.code:
                response_line.response_message = response_line.code
            elif response_line.description:
                response_line.response_message = response_line.description
            else:
                response_line.response_message = ""
