# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    confirminet_type = fields.Selection(
        string='Type of payment', default='56',
        selection=[('56', 'Transfer'),
                   ('57', 'Cheques')])
    is_confirminet = fields.Boolean(compute="_compute_is_confirminet")

    @api.multi
    @api.depends('type')
    def _compute_is_confirminet(self):
        confirminet_type = self.env.ref(
            'l10n_es_payment_order_confirminet.export_confirminet')
        for record in self:
            record.is_confirminet = record.type == confirminet_type
