from odoo import api, models


class SendAeatSilicieMarksWizard(models.TransientModel):
    _name = "send.aeat.silicie.wizard"
    _description = "Wizard Send SILICIE AEAT"

    @api.multi
    def send_aeat_silicie(self):
        stock_moves = self.env['stock.move'].browse(
            self._context.get('active_ids'))
        if stock_moves:
            stock_moves._send_aeat()
        return
