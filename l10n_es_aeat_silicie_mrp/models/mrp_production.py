from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    silicie_processing_id = fields.Many2one(
        string='Processing SILICIE',
        comodel_name='aeat.processing.silicie',
        ondelete='restrict',
    )
    silicie_loss_id = fields.Many2one(
        string="Loss SILICIE",
        comodel_name="aeat.loss.silicie",
        ondelete="restrict",
        help="SILICIE loss code in raw moves",
    )

    @api.onchange('routing_id')
    def _onchange_routing_id(self):
        if self.routing_id.silicie_processing_id:
            self.silicie_processing_id = self.routing_id.silicie_processing_id

    @api.onchange('silicie_loss_id')
    def _onchange_silicie_loss_id(self):
        if self.silicie_loss_id:
            self.move_raw_ids.write({
                "silicie_loss_id": self.silicie_loss_id.id,
            })
        else:
            self.move_raw_ids.write({
                "silicie_loss_id": False,
            })
