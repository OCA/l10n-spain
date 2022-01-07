# 2021 Obertix - Cubells <vicent@vcubells.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SilicieMoveEditor(models.TransientModel):
    _inherit = "silicie.move.editor"

    extract = fields.Float(
        string="Extracto SILICIE",
    )

    @api.multi
    def _prepare_silicie_values(self):
        self.ensure_one()
        values = super()._prepare_silicie_values()
        values.update({
            'extract': self.extract,
        })
        return values

