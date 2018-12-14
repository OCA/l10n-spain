# -*- coding: utf-8 -*-
# (c) 2018 Comunitea Servicios Tecnológicos - Javier Colmenero
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    conf_caixabank_type = fields.Selection(
        string='Tipo de pago', default='T',
        selection=[('T', 'Tranferencia'),
                   ('C', 'Cheques')])

    is_conf_caixabank = fields.Boolean(compute="_compute_is_conf_caixabank")
    num_contract = fields.Char('Num Contract')

    @api.multi
    @api.depends('payment_method_id.code')
    def _compute_is_conf_caixabank(self):
        for record in self:
            record.is_conf_caixabank = record.payment_method_id.code == \
                'conf_caixabank'
