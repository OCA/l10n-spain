from odoo import api, fields, models


class VerifactuChain(models.Model):
    _name = "verifactu.chain"
    _description = "VeriFactu Chain Entry"
    _rec_name = "document_id"

    document_id = fields.Reference(
        selection="_selection_verifactu_reference_models",
        string="Document",
        required=True,
        readonly=True,
    )

    previous_chain_entry_id = fields.Many2one(
        "verifactu.chain",
        string="Previous Chain Entry",
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

    chain_context_id = fields.Reference(
        selection="_selection_chain_context_models",
        string="Chain Context",
        help="Reference to the context that owns this chain (e.g., pos.config). "
        "Leave empty for company-wide chains like invoices.",
        index=True,
        readonly=True,
    )

    @api.model
    def _selection_verifactu_reference_models(self):
        """Define the models that can be used as documents in the verifactu chain.

        This method can be inherited to add other models like pos.order.
        """
        return [("account.move", "Invoice")]

    @api.model
    def _selection_chain_context_models(self):
        """Define the models that can be used as chain contexts.

        This method can be inherited to add other models like pos.config.
        """
        return [("res.company", "Company")]

    def _get_previous_chain_entry(self, document_model, company_id, **kwargs):
        """Find the last chain entry for the same document type and context.

        Args:
            document_model (str): The model name (e.g., 'account.move')
            company_id (int): The company ID
            **kwargs: Additional context fields for filtering (e.g., pos_config_id)

        Returns:
            verifactu.chain: The previous chain entry or empty recordset
        """
        domain = [
            ("company_id", "=", company_id),
            ("document_id", "like", f"{document_model},%"),
        ]

        # Add any additional context filters
        for field, value in kwargs.items():
            if hasattr(self, field) and value:
                domain.append((field, "=", value))

        return self.search(domain, order="id desc", limit=1)
