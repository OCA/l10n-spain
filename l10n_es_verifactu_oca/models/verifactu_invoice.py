from odoo import api, fields, models


class VerifactuInvoice(models.Model):
    _name = "verifactu.invoice"
    _description = "VeriFactu Invoice Entry"
    _rec_name = "document_id"

    document_id = fields.Reference(
        selection="_selection_verifactu_reference_models",
        string="Document",
        required=True,
        readonly=True,
    )

    previous_invoice_entry_id = fields.Many2one(
        "verifactu.invoice",
        string="Previous Invoice Entry",
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
    )

    document_hash = fields.Char(
        required=True,
        readonly=True,
    )

    aeat_json_data = fields.Text(
        string="AEAT JSON Data",
        help="Generated JSON data to send to AEAT",
        readonly=True,
    )

    send_queue_ids = fields.One2many(
        "verifactu.send.queue",
        "verifactu_invoice_id",
        string="Send Queue Records",
    )
    send_response_ids = fields.One2many(
        "verifactu.send.response.line",
        "verifactu_invoice_id",
        string="Send Response Lines",
    )

    @api.model
    def _selection_verifactu_reference_models(self):
        """Define the models that can be used as documents in the verifactu invoice."""
        return [("account.move", "Invoice")]

    def _get_previous_invoice_entry(self, document_model, company_id):
        """Find the last invoice entry for the same document type and company.

        Args:
            document_model (str): The model name (e.g., 'account.move')
            company_id (int): The company ID

        Returns:
            verifactu.invoice: The previous invoice entry or empty recordset
        """
        domain = [
            ("company_id", "=", company_id),
            ("document_id", "like", f"{document_model},%"),
        ]

        return self.search(domain, order="id desc", limit=1)
