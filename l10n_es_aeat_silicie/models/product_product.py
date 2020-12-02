# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

PRODUCT_TYPES = [
    ('none', 'None'),
    ('alcohol', 'Alcohol'),
    ('beer', 'Beer'),
    ('intermediate', 'Intermediate'),
    ('intermediate_art', 'Intermediate Art. 32 LIE'),
    ('wine', 'Wine'),
    ('vinegar', 'Vinegar'),
    ('hydrocarbons', 'Hydrocarbons'),
    ('tobacco', 'Tobacco'),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    silicie_product_type = fields.Selection(
        string='SILICIE Product Type',
        selection=PRODUCT_TYPES,
        default='none',
        required=True,
        copy=True,
    )
    nc_code = fields.Char(
        string='NC Code',
        copy=True,
    )
    alcoholic_grade = fields.Float(
        string='Alcoholic Grade',
        copy=True,
    )
    product_key_silicie_id = fields.Many2one(
        string='Product Key SILICIE',
        comodel_name='aeat.product.key.silicie',
        ondelete='restrict',
        copy=True,
    )
    container_type_silicie_id = fields.Many2one(
        string='Container Type SILICIE',
        comodel_name='aeat.container.type.silicie',
        ondelete='restrict',
        copy=True,
    )
    epigraph_silicie_id = fields.Many2one(
        string='Epigraph SILICIE',
        comodel_name='aeat.epigraph.silicie',
        ondelete='restrict',
        copy=True,
    )
    uom_silicie_id = fields.Many2one(
        string='UoM SILICIE',
        comodel_name='aeat.uom.silicie',
        ondelete='restrict',
        copy=True,
    )
    factor_conversion_silicie = fields.Float(
        string='Factor Conversion SILICIE',
        default=1,
        copy=True,
    )
    silicie_qty = fields.Float(
        string='Cantidad SILICIE',
        compute='_compute_silicie_qty',
        store=True,
    )
    product_class = fields.Selection(
        selection=[
            ('final', 'Final'),
            ('raw', 'Raw Material'),
            ('raw_without_extract', 'Raw Material Without Extract'),
            ('manufactured', 'Manufactured'),
        ],
    )

    @api.depends('factor_conversion_silicie', 'qty_available')
    def _compute_silicie_qty(self):
        for product in self:
            product.silicie_qty = \
                product.factor_conversion_silicie * product.qty_available
