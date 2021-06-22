# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo.addons.component.core import Component


class EdiInputProcessL10nEsFacturaeEfactUpdate(Component):
    _name = "edi.input.process.l10n_es_facturae.l10n_es_facturae_efact_update"
    _usage = "input.process"
    _backend_type = "l10n_es_facturae"
    _exchange_type = "l10n_es_facturae_efact_update"

    _inherit = "edi.component.input.mixin"

    def process(self):
        hub_list = self.exchange_record.exchange_filename.rsplit("@", 1)
        hub_message_id = hub_list[1]
        datas = self.exchange_record._get_file_content(binary=False)
        delivery_feedback = etree.fromstring(base64.b64decode(datas))
        for status_feedback in delivery_feedback.findall("StatusFeedback"):
            hub_feedback = status_feedback.find("HubFeedback")
            if hub_feedback is None:
                continue
            invoice_feedback = status_feedback.find("InvoiceFeedback")
            hub_id = hub_feedback.find("HubId").text
            if invoice_feedback is not None:
                parent_record = self.env["edi.exchange.record"].search(
                    [
                        ("external_identifier", "=", hub_id),
                        ("backend_id", "=", self.backend.id),
                    ],
                    limit=1,
                )
                if not parent_record:
                    parent_record = self.env["edi.exchange.record"].search(
                        [
                            ("external_identifier", "=", False),
                            ("backend_id", "=", self.backend.id),
                            (
                                "exchange_filename",
                                "=",
                                hub_feedback.find("HubFilename").text,
                            ),
                        ],
                        limit=1,
                    )
                    parent_record.ensure_one()
                    parent_record.external_identifier = hub_id
                for feedback in invoice_feedback.findall("Feedback"):
                    # register = feedback.find("RegisterNumber")
                    # if register is not None and not parent_record.register_number:
                    #    integration.register_number = register.text
                    process_code = "efact-" + feedback.find("Status").text.upper()
                    motive = False
                    if feedback.find("Reason") is not None:
                        motive = feedback.find("Reason").find("Description").text
                    parent_record.write(
                        {
                            "l10n_es_facturae_status": process_code,
                            "l10n_es_facturae_motive": motive,
                        }
                    )
                    parent_record.record.write(
                        {"l10n_es_facturae_status": process_code}
                    )
                    for annex in feedback.findall("ElectronicAcknowledgment"):
                        annex_name = "{!a}.{}".format(
                            parent_record.external_identifier,
                            annex.find("formatType").text,
                        )
                        self.env["ir.attachment"].create(
                            {
                                "name": annex_name,
                                "datas": annex.find("document").text,
                                "res_model": parent_record.model,
                                "res_id": parent_record.res_id,
                            }
                        )
            else:
                parent_record = self.env["edi.exchange.record"].search(
                    [
                        ("external_identifier", "=", False),
                        ("backend_id", "=", self.backend.id),
                        (
                            "exchange_filename",
                            "=",
                            hub_feedback.find("HubFilename").text,
                        ),
                    ],
                    limit=1,
                )
                if not parent_record:
                    continue
                process_code = "efact-" + hub_feedback.find("HubStatus").text.upper()
                parent_record.write(
                    {
                        "external_identifier": hub_id,
                        "exchange_error": "%s - %s"
                        % (
                            hub_feedback.find("HubStatus").text,
                            hub_feedback.find("HubErrorCode").text,
                        ),
                        "l10n_es_facturae_status": process_code,
                        "l10n_es_facturae_motive": hub_feedback.find(
                            "HubErrorCode"
                        ).text,
                    }
                )
                parent_record.record.write({"l10n_es_facturae_status": process_code})
            self.exchange_record.write(
                {
                    "parent_id": parent_record.id,
                    "model": parent_record.model,
                    "res_id": parent_record.res_id,
                    "external_identifier": hub_message_id,
                }
            )
