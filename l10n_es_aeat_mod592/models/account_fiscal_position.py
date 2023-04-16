# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    product_plastic_document_type = fields.Selection(
        [
            ("1", _("(1) NIF or Spanish NIE")),
            ("2", _("(2) Intra-Community VAT NIF")),
            ("3", _("(3) Others")),
        ],
        string=_("Product plastic document type"),
        help=_("Supplier/Recipient Document Type Code"),
    )
