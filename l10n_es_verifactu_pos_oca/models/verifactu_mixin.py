from odoo import api, models


class VerifactuMixin(models.AbstractModel):
    _inherit = "verifactu.mixin"

    @api.model
    def _get_verifactu_reference_models(self):
        """Add pos.order to the list of models that can be used as
        reference documents in VERI*FACTU.
        """
        models = super()._get_verifactu_reference_models()
        if "pos.order" not in models:
            models.append("pos.order")
        return models


class VerifactuInvoiceEntry(models.Model):
    _inherit = "verifactu.invoice.entry"

    def _create_response_lines(
        self, response=False, header=False, verifactu_response=False
    ):
        """Override to properly search for pos.order documents by serial number"""
        create_response_activity = False
        # the returned object doesn't have `get` method, so use this form
        verifactu_response_lines = (
            "RespuestaLinea" in verifactu_response
            and verifactu_response["RespuestaLinea"]
            or []
        )
        VERIFACTU_STATE_MAPPING = {
            "Correcto": "correct",
            "Incorrecto": "incorrect",
            "AceptadoConErrores": "accepted_with_errors",
        }
        models = self.env["verifactu.mixin"]._get_verifactu_reference_models()
        for verifactu_response_line in verifactu_response_lines:
            invoice_num = verifactu_response_line["IDFactura"]["NumSerieFactura"]
            document = False
            for model in models:
                # First try to find by name (works for account.move)
                document = self.env[model].search(
                    [
                        ("name", "=", invoice_num),
                        ("id", "in", self.mapped("document_id")),
                    ],
                    limit=1,
                )
                if not document and model == "pos.order":
                    document = self.env[model].search(
                        [
                            ("l10n_es_unique_id", "=", invoice_num),
                            ("id", "in", self.mapped("document_id")),
                        ],
                        limit=1,
                    )
                    if not document:
                        for entry in self:
                            if (
                                entry.model == "pos.order"
                                and entry.document
                                and entry.document.pos_reference
                            ):
                                serial = (
                                    entry.document.l10n_es_unique_id
                                    or entry.document.pos_reference
                                )[0:60]
                                if serial == invoice_num:
                                    document = entry.document
                                    break
                if document:
                    break

            if not document:
                # If still not found, skip this response line
                continue

            # Find the verifactu.invoice entry for this document
            verifactu_invoice_entry = document.last_verifactu_invoice_entry_id
            previous_response_line = document.last_verifactu_response_line_id
            send_state = VERIFACTU_STATE_MAPPING[
                verifactu_response_line["EstadoRegistro"]
            ]
            vals = {
                "entry_id": verifactu_invoice_entry.id,
                "model": verifactu_invoice_entry.model,
                "document_id": verifactu_invoice_entry.document_id,
                "response": verifactu_response_line,
                "entry_response_id": response.id,
                "send_state": send_state,
                "error_code": "CodigoErrorRegistro" in verifactu_response_line
                and str(verifactu_response_line["CodigoErrorRegistro"])
                or "",
            }
            response_line = (
                self.env["verifactu.invoice.entry.response.line"].sudo().create(vals)
            )
            document.last_verifactu_response_line_id = response_line
            verifactu_invoice_entry.last_response_line_id = response_line
            self._process_response_line_doc_vals(
                verifactu_response=verifactu_response,
                verifactu_response_line=verifactu_response_line,
                response_line=response_line,
                previous_response_line=previous_response_line,
                header_sent=header,
            )
            if send_state != "correct":
                create_response_activity = True
        return create_response_activity
