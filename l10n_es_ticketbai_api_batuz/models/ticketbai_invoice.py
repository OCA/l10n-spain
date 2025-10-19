# Copyright (2021) Binovo IT Human Project SL
# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import exceptions, fields, models

from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema

from ..lroe.lroe_api import LROETicketBaiApi
from .lroe_operation import LROEModelEnum, LROEOperationEnum, LROEOperationStateEnum
from .lroe_operation_response import LROEOperationResponseState

_logger = logging.getLogger(__name__)


class TicketBAIInvoice(models.Model):
    _inherit = "tbai.invoice"

    lroe_operation_id = fields.Many2one(
        comodel_name="lroe.operation", string="TicketBAI-Batuz LROE Operation"
    )

    def get_lroe_ticketbai_api(self, **kwargs):
        self.ensure_one()
        p12_buffer = self.company_id.tbai_certificate_get_p12_buffer()
        password = self.company_id.tbai_certificate_get_p12_password()
        return LROETicketBaiApi(
            self.api_url, p12_buffer=p12_buffer, password=password, **kwargs
        )

    def create_tbai_lroe_operation(self):
        def lroe_operation_company():
            return self.company_id

        def lroe_operation_type():
            if self.schema == TicketBaiSchema.TicketBai.value:
                return LROEOperationEnum.create.value
            if self.schema == TicketBaiSchema.AnulaTicketBai.value:
                return LROEOperationEnum.cancel.value

        def lroe_customer_invoices():
            return [self.id]

        self.ensure_one()
        lroe_op_db_model = self.env["lroe.operation"]
        company = lroe_operation_company()
        if company.lroe_model == LROEModelEnum.model_pf_140.value:
            lroe_chapter_id = self.env.ref(
                "l10n_es_ticketbai_api_batuz.lroe_chapter_pf_140_1"
            )
            lroe_subchapter_id = self.env.ref(
                "l10n_es_ticketbai_api_batuz.lroe_subchapter_pf_140_1_1"
            )
        else:
            lroe_chapter_id = self.env.ref(
                "l10n_es_ticketbai_api_batuz.lroe_chapter_pj_240_1"
            )
            lroe_subchapter_id = self.env.ref(
                "l10n_es_ticketbai_api_batuz.lroe_subchapter_pj_240_1_1"
            )
        lroe_operation_dict = {
            "company_id": company.id,
            "type": lroe_operation_type(),
            "tbai_invoice_ids": [(6, 0, lroe_customer_invoices())],
            "lroe_chapter_id": lroe_chapter_id.id,
            "lroe_subchapter_id": lroe_subchapter_id.id,
        }
        lroe_operation = lroe_op_db_model.create(lroe_operation_dict)
        if lroe_operation:
            lroe_operation.build_xml_file()
        return lroe_operation

    def send(self, **kwargs):
        tbai_tax_agency_id = self.company_id.tbai_tax_agency_id
        if (
            tbai_tax_agency_id
            and tbai_tax_agency_id.id
            == self.env.ref("l10n_es_ticketbai_api_batuz.tbai_tax_agency_bizkaia").id
        ):
            return self.send_lroe_ticketbai(**kwargs)
        else:
            return super().send(**kwargs)

    def send_lroe_ticketbai(self, **kwargs):
        self.ensure_one()
        error_msg = ""
        try:
            lroe_tbai_api = self.get_lroe_ticketbai_api()
            lroe_operation = self.create_tbai_lroe_operation()
        except exceptions.ValidationError as ve:
            _logger.exception(ve)
            lroe_tbai_api = None
            lroe_operation = None
            error_msg = ve.name
        if lroe_tbai_api is not None and lroe_operation is not None:
            request_headers = LROETicketBaiApi.get_request_headers(lroe_operation)
            data_length, data_content = lroe_operation.set_trx_gzip_file()
            request_headers["Content-Length"] = data_length
            lroe_response = lroe_tbai_api.requests_post(request_headers, data_content)
            values = self.env["lroe.operation.response"].prepare_lroe_response_values(
                lroe_response, lroe_operation, **kwargs
            )
        else:
            values = self.env["lroe.operation.response"].prepare_lroe_error_values(
                lroe_operation, error_msg, **kwargs
            )
        if values:
            lroe_response_obj = self.env["lroe.operation.response"].create(values)
            if lroe_response_obj:
                operation_state = None
                if (
                    lroe_response_obj.state
                    == LROEOperationResponseState.BUILD_ERROR.value
                    or lroe_response_obj.state
                    == LROEOperationResponseState.REQUEST_ERROR.value
                    or lroe_response_obj.state
                    == LROEOperationResponseState.INCORRECT.value
                ):
                    operation_state = LROEOperationStateEnum.ERROR.value
                if lroe_response_obj.state == LROEOperationResponseState.CORRECT.value:
                    operation_state = LROEOperationStateEnum.RECORDED.value
                if (
                    lroe_response_obj.state
                    == LROEOperationResponseState.PARTIALLY_CORRECT.value
                ):
                    operation_state = LROEOperationStateEnum.RECORDED_WARNING.value
                if lroe_operation and operation_state:
                    lroe_operation.state = operation_state
                return lroe_response_obj.response_line_ids.tbai_response_id
