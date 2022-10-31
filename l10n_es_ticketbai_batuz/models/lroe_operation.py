# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, exceptions, fields, models, _

from odoo.addons.l10n_es_ticketbai_api_batuz.models.lroe_operation import (
    LROEOperationStateEnum,
    LROEOperationEnum,
)
from odoo.addons.l10n_es_ticketbai_api_batuz.lroe.lroe_xml_schema import (
    LROEXMLSchemaModeNotSupported,
)
from odoo.addons.l10n_es_ticketbai_api_batuz.models.lroe_operation_response import (
    LROEOperationResponseState,
)
from odoo.addons.l10n_es_ticketbai_api_batuz.lroe.lroe_api import LROETicketBaiApi

from odoo.modules.registry import Registry

import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug("Can not `import queue_job`.")
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial

    job = empty_decorator_factory


class LROEOperation(models.Model):
    _inherit = "lroe.operation"

    @api.model
    def create(self, vals):
        # Establecemos los valores por defecto para ser compatibles
        # con l10n_es_ticketbai_batuz
        if not vals.get("lroe_chapter_id", False) and vals.get("model", False):
            model = vals.get("model")
            if model == "140":
                vals["lroe_chapter_id"] = self.env.ref(
                    "l10n_es_batuz.lroe_chapter_pf_140_1"
                )
                vals["lroe_subchapter_id"] = self.env.ref(
                    "l10n_es_batuz.lroe_subchapter_pf_140_1_1"
                )
            else:
                vals["lroe_chapter_id"] = self.env.ref(
                    "l10n_es_batuz.lroe_chapter_pj_240_1"
                )
                vals["lroe_subchapter_id"] = self.env.ref(
                    "l10n_es_batuz.lroe_subchapter_pj_240_1_1"
                )
        return super().create(vals)

    @api.multi
    def get_lroe_api(self, **kwargs):
        self.ensure_one()
        cert = self.company_id.tbai_certificate_get_public_key()
        key = self.company_id.tbai_certificate_get_private_key()
        return LROETicketBaiApi(self.api_url, cert=cert, key=key, **kwargs)

    @api.multi
    def send(self, **kwargs):
        self.ensure_one()
        error_msg = ""
        try:
            self.build_xml_file()
            lroe_tbai_api = self.get_lroe_api()
        except exceptions.ValidationError as ve:
            _logger.exception(ve)
            lroe_tbai_api = None
            error_msg = ve.name
        if lroe_tbai_api is not None:
            request_headers = LROETicketBaiApi.get_request_headers(self)
            data_length, data_content = self.set_trx_gzip_file()
            request_headers["Content-Length"] = data_length
            lroe_response = lroe_tbai_api.requests_post(request_headers, data_content)
            values = self.env["lroe.operation.response"].prepare_lroe_response_values(
                lroe_response, self, **kwargs
            )
        else:
            values = self.env["lroe.operation.response"].prepare_lroe_error_values(
                self, error_msg, **kwargs
            )
        if values:
            return self.env["lroe.operation.response"].create(values)

    @api.multi
    def send_one_operation(self):
        lroe_response = self.send()
        if lroe_response.state == LROEOperationResponseState.CORRECT.value:
            self.mark_as_recorded()
        elif lroe_response.state == LROEOperationResponseState.PARTIALLY_CORRECT.value:
            self.mark_as_warning()
        elif lroe_response.state in (
            LROEOperationResponseState.BUILD_ERROR.value,
            LROEOperationResponseState.INCORRECT.value,
        ):
            self.mark_as_error()

    @job(default_channel="root.invoice_send_lroe")
    @api.multi
    def send_one_operation_job(self):
        self.send_one_operation()

    @api.multi
    def process(self):
        self.ensure_one()
        # Decide when/how to send lroe_operation
        queue_obj = self.env["queue.job"].sudo()
        company = self.company_id
        if not company.use_connector:
            try:
                lroe_response = self.send()
                if lroe_response.state == LROEOperationResponseState.CORRECT.value:
                    self.mark_as_recorded()
                elif (
                    lroe_response.state
                    == LROEOperationResponseState.PARTIALLY_CORRECT.value
                ):
                    self.mark_as_warning()
                elif lroe_response.state in (
                    LROEOperationResponseState.BUILD_ERROR.value,
                    LROEOperationResponseState.INCORRECT.value,
                ):
                    self.mark_as_error()
            except Exception:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                lroe_operation = env["lroe.operation"].browse(self.id)
                lroe_operation.write({"state": LROEOperationStateEnum.ERROR.value})
                # If an operation has been sent successfully to the Tax Agency we need
                # to make sure that the current state is saved in case an exception
                # occurs in the following invoices.
                new_cr.commit()
                new_cr.close()
                raise
        else:
            eta = company._get_lroe_eta(
                self.invoice_ids.sorted(key=lambda i: i.date_invoice)
            )
            new_delay = (
                self.sudo()
                .with_context(company_id=company.id)
                .with_delay(eta=eta)
                .send_one_operation_job()
            )
            job = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
            self.sudo().jobs_ids |= job

    invoice_ids = fields.Many2many(
        comodel_name="account.invoice",
        relation="account_invoice_lroe_operation_rel",
        column1="lroe_operation_id",
        column2="invoice_id",
        string="Invoices",
    )
    api_url = fields.Char("LROE API URL", compute="_compute_api_url")
    jobs_ids = fields.Many2many(
        comodel_name="queue.job",
        column1="lroe_operation_id",
        column2="job_id",
        string="Connector Jobs",
        copy=False,
    )

    @api.multi
    @api.depends(
        "company_id",
        "company_id.tbai_tax_agency_id",
        "company_id.tbai_tax_agency_id.rest_url_invoice",
        "company_id.tbai_tax_agency_id.test_rest_url_invoice",
        "company_id.tbai_tax_agency_id.rest_url_cancellation",
        "company_id.tbai_tax_agency_id.test_rest_url_cancellation",
    )
    def _compute_api_url(self):
        for record in self:
            # Alta, modificación
            if record.type in (
                LROEOperationEnum.create.value,
                LROEOperationEnum.update.value,
            ):
                if record.company_id.tbai_test_enabled:
                    url = record.company_id.tbai_tax_agency_id.test_rest_url_invoice
                else:
                    url = record.company_id.tbai_tax_agency_id.rest_url_invoice
            # anulación
            elif record.type == LROEOperationEnum.cancel.value:
                if record.company_id.tbai_test_enabled:
                    url = (
                        record.company_id.tbai_tax_agency_id.test_rest_url_cancellation
                    )
                else:
                    url = record.company_id.tbai_tax_agency_id.rest_url_cancellation
            else:
                raise LROEXMLSchemaModeNotSupported(
                    _("LROE Operation %s: XML schema not supported!") % record.name
                )
            record.api_url = url

    @api.multi
    def _cancel_jobs(self):
        for queue in self.sudo().mapped("jobs_ids"):
            if queue.state == "started":
                return False
            elif queue.state in ("pending", "enqueued", "failed"):
                queue.unlink()
        return True

    @api.multi
    def mark_as_error(self):
        self.invoice_ids.set_lroe_state_error()
        self.write({"state": LROEOperationStateEnum.ERROR.value})

    @api.multi
    def mark_as_warning(self):
        self.invoice_ids.set_lroe_state_recorded_warning()
        self.write({"state": LROEOperationStateEnum.RECORDED_WARNING.value})

    @api.multi
    def mark_as_recorded(self):
        self.invoice_ids.set_lroe_state_recorded()
        self.write({"state": LROEOperationStateEnum.RECORDED.value})
