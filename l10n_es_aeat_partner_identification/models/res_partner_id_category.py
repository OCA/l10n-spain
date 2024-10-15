from odoo import fields, models


class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    aeat_identification_type = fields.Selection(
        string="AEAT Identification type equivalent",
        help=(
            "Automatically synchronizes the type of document with the identification"
            "fields of the aeat:"
            'Passport ("03"), Residential cert. ("04") and Another document ("05")'
            "are setted in partner aeat identificacion type."
            'NIF/VAT ("02") and Official document from de original country ("04")'
            "are setted in partner vat field"
        ),
        selection=[
            ("02", "NIF - VAT"),
            ("03", "Passport"),
            ("04", "Official document from the original country"),
            ("05", "Residential certificate"),
            ("06", "Another document"),
            ("07", "Not registered on census"),
        ],
    )
