# -*- coding: utf-8 -*-
# (c) 2016 Soluntec Proyectos y Soluciones TIC S.L. - Rubén Frances, Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    conf_sabadell_type = fields.Selection(
        string='Tipo de pago', default='56',
        selection=[('56', 'Tranferencia'),
                   ('57', 'Cheques'),
                   ('58', 'Tranferencia extranjero')])

    is_conf_sabadell = fields.Boolean(compute="_compute_is_conf_sabadell")

    tipo_envio_info = fields.Selection(
        string='Tipo envío información', default='1',
        selection=[('1', 'Correo'),
                   ('2', 'Fax'),
                   ('3', 'Email')])

    contrato_bsconfirming = fields.Char(string="Contrato BSConfirming (12 dígitos)")

    codigo_estadistico = fields.Char(string="Codigo Estadistico para Transferencia Internacional (6 carácteres)", default="000000")

    @api.multi
    @api.depends('type')
    def _compute_is_conf_sabadell(self):
        conf_sabadell_type = self.env.ref(
            'l10n_es_payment_order_confirming_sabadell.export_sabadell')
        for record in self:
            record.is_conf_sabadell = record.type == conf_sabadell_type

