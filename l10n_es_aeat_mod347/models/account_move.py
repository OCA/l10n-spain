from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    force_not_in_mod347 = fields.Boolean(
        "Force not included in 347 report",
        help="If you mark this field, this invoice will not be included in "
             "any AEAT 347 model report.", default=False,
    )
    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        compute='_compute_not_in_mod347'
    )
    invoice_not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        compute='_compute_not_in_mod347'
    )

    @api.multi
    @api.depends('line_ids.invoice_id.not_in_mod347', 'force_not_in_mod347')
    def _compute_not_in_mod347(self):
        for move in self:
            invoice_not_in_mod347 = self.line_ids and \
                self.line_ids[0].invoice_id and \
                self.line_ids[0].invoice_id.not_in_mod347
            self.invoice_not_in_mod347 = invoice_not_in_mod347
            self.not_in_mod347 = invoice_not_in_mod347 or \
                self.force_not_in_mod347
