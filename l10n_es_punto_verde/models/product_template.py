# -*- coding: utf-8 -*-
# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models , fields , _


class product_template(models.Model):
    _inherit="product.template"

    punto_verde = fields.Float(string="Punto verde por Ud",digits=(15,6))
