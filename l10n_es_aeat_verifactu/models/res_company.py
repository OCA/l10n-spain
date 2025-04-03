# Copyright 2024 Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    verifactu_enabled = fields.Boolean(string="Enable veri*FACTU")
    verifactu_test = fields.Boolean(string="Is it the veri*FACTU test environment?")
    verifactu_description = fields.Text(
        default="/",
        size=500,
        help="The description for Verifactu invoices if not set",
    )
    verifactu_last_document_id = fields.Reference(
        string="Last Verifactu Document",
        selection="_selection_verifactu_reference_models",
        readonly=True,
    )

    @api.model
    def _selection_verifactu_reference_models(self):
        return self.env["verifactu.mixin"]._selection_verifactu_reference_models()
