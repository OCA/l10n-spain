from odoo import api, fields, models


class NotDeclareSilicieMovesWizard(models.TransientModel):
    _name = "not.declare.silicie.moves.wizard"
    _description = "Wizard Not Declare SILICIE Moves"

    yes_no = fields.Char(
        default='Do you want to proceed?',
    )

    @api.multi
    def not_declare_silicie_moves(self):
        moves = self.env['stock.move'].browse(self._context.get('active_ids'))
        for move in moves:
            if not move.send_silicie:
                move.clear_silicie_fields()
                move.write({'not_declare': True})
        return
