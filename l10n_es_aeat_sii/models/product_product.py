# -*- coding: utf-8 -*-
# Copyright 2017 MINORISA (http://www.minorisa.net)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sii_exempt_cause = fields.Selection(
        string="SII Exempt Cause",
        selection=[('none', 'None'),
                   ('E1', 'E1'),
                   ('E2', 'E2'),
                   ('E3', 'E3'),
                   ('E4', 'E4'),
                   ('E5', 'E5'),
                   ('E6', 'E6')],
        default='none')
