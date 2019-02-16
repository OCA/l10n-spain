# Copyright 2018 PESOL - Angel Moya <info@pesol.es>
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        help="If you mark this field, this invoice will not be included in "
             "any AEAT 347 model report.",
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    # TODO: Añadir fecha para declaración 347

    def action_move_create(self):
        """Propagate `not_in_347` field to the account move."""
        res = super().action_move_create()
        self.filtered('not_in_mod347').mapped('move_id').write({
            'not_in_mod347': True,
        })
        return res
