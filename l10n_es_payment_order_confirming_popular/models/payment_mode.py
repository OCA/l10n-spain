# -*- coding: utf-8 -*-
# (c) 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés , Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    conf_popular_type = fields.Selection(
        string='Tipo de pago', default='60',
        selection=[('60', 'Tranferencia'),
                   ('61', 'Cheques'),
                   ('70', 'Pagos confirmados')])
    is_conf_popular = fields.Boolean(compute="_compute_is_conf_popular")

    gastos = fields.Selection(
        string='Gastos de la operación a cuenta de', default='ordenante',
        selection=[('ordenante', 'Ordenante'),
                   ('beneficiario', 'Beneficiario')])

    forma_pago = fields.Selection(
        string='Forma de pago', default='C',
        selection=[('C', 'Cheque'),
                   ('T', 'Transferencia')])

    @api.multi
    @api.depends('type')
    def _compute_is_conf_popular(self):
        conf_popular_type = self.env.ref(
            'l10n_es_payment_order_confirming_popular.export_popular')
        for record in self:
            record.is_conf_popular = record.type == conf_popular_type
