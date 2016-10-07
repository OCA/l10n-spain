# -*- coding: utf-8 -*-
# (c) 2016 Soluntec Proyectos y Soluciones TIC S.L. - Rubén Frances, Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api

class PaymentMode(models.Model):
    _inherit = "payment.mode"

    conf_bankia_type = fields.Selection(
        string='Tipo de pago', default='T',
        selection=[('T', 'Tranferencia'),
                   ('P', 'Pago domiciliado'),
                   ('C', 'Cheque bancario')])

    is_conf_bankia = fields.Boolean(compute="_compute_is_conf_bankia")


    @api.multi
    @api.depends('type')
    def _compute_is_conf_bankia(self):
        conf_bankia_type = self.env.ref(
            'l10n_es_payment_order_confirming_bankia.export_bankia')
        for record in self:
            record.is_conf_bankia = record.type == conf_bankia_type

