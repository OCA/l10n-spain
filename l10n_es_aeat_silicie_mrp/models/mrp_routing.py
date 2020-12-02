from odoo import api, fields, models


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    silicie_processing_id = fields.Many2one(
        string='Processing SILICIE',
        comodel_name='aeat.processing.silicie',
        ondelete='restrict',
    )
