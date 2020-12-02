from odoo import api, exceptions, fields, models, _
import odoo.addons.decimal_precision as dp


class RegenerateSilicieMovesWizard(models.TransientModel):
    _name = "regenerate.silicie.moves.wizard"
    _description = "Wizard Regenerate SILICIE Moves"

    yes_no = fields.Char(default=_('Do you want to proceed?'))

    @api.multi
    def regenerate_silicie_moves(self):
        moves = self.env['stock.move'].browse(self._context.get('active_ids'))
        moves.generate_silicie_fields()
        return
