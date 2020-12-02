from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    silicie_processing_id = fields.Many2one(
        string='Processing SILICIE',
        comodel_name='aeat.processing.silicie',
        ondelete='restrict',
    )

    @api.onchange('routing_id')
    def _onchange_routing_id(self):
        if self.routing_id.silicie_processing_id:
            self.silicie_processing_id = self.routing_id.silicie_processing_id
