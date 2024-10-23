# Copyright 2022 Landoo Sistemas de Informacion SL
from odoo import fields, models


class TicketBAITax(models.Model):
    _inherit = "tbai.invoice.tax"

    not_subject_to_cause = fields.Selection(selection_add=[("IE", "IE")])
