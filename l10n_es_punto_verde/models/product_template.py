from odoo import models , fields , _


class product_template(models.Model):
    _inherit="product.template"

    punto_verde = fields.Float(string="Punto verde por Ud",digits=(15,6))
