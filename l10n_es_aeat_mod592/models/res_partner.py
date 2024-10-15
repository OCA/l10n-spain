# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# Copyright 2023 Javier Colmenero - (https://javier@comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _


class ResPartner(models.Model):

    _description = "ResPartner"
    _inherit = "res.partner"

    product_plastic_document_type = fields.Selection(
        [
            ("1", _("(1) NIF or Spanish NIE")),
            ("2", _("(2) Intra-Community VAT NIF")),
            ("3", _("(3) Others")),
        ],
        string=_("Product plastic document type"),
        help=_("Supplier/Recipient Document Type Code"),
        compute="_compute_product_plastic_document_type",
        store=True,
    )

    @api.depends(
        "vat", "country_id", "aeat_identification", "aeat_identification_type")
    def _compute_product_plastic_document_type(self):
        for partner in self:
            idenfier_type = partner._parse_aeat_vat_info()[1]
            doc_type = "3"
            if not idenfier_type:
                doc_type = "1"
            elif idenfier_type == "02":
                doc_type = "2"
            partner.product_plastic_document_type = doc_type
