from odoo import fields, models


class ResPartnerIdCategory(models.Model):
    _inherit = "res.partner.id_category"

    aeat_identification_type = fields.Selection(
        string="AEAT Identification type equivalent",
        help=(
            "Used to specify an identification type to send to SII. Normally for "
            "sending national and export invoices to SII where the customer country "
            "is not Spain, it would calculate an identification type of 04 if the VAT "
            "field is filled and 06 if it was not. This field is to specify "
            "types of 03 through 05, in the event that the customer doesn't identify "
            "with a foreign VAT and instead with their passport "
            "or residential certificate. If there is no value it will work as before."
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
