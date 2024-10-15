# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models

from .misc import DOCUMENT_TYPES


class ResPartner(models.Model):
    _inherit = "res.partner"

    plastic_document_type = fields.Selection(
        selection=DOCUMENT_TYPES,
        string="Plastic document type",
        help="Supplier/Recipient Document Type Code",
        compute="_compute_plastic_document_type",
        store=True,
    )

    @api.depends("vat", "country_id", "aeat_identification", "aeat_identification_type")
    def _compute_plastic_document_type(self):
        for partner in self:
            idenfier_type = partner._parse_aeat_vat_info()[1]
            if not idenfier_type:
                doc_type = "1"
            elif idenfier_type == "02":
                doc_type = "2"
            else:
                doc_type = "3"
            partner.plastic_document_type = doc_type
