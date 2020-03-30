# (c) 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés , Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class PaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    is_conf_sabadell = fields.Boolean(compute="_compute_is_conf_sabadell")

    num_contract = fields.Char('Código activo de contrato:')
    tipo_lote = fields.Char('Tipo de Lote:' , default='65')
    forma_envio = fields.Char('Forma envío:', default='B')
    codigo_fichero = fields.Char('Forma envío:', default='KF01')

    """
    sufix = fields.Char('Sufijo ordenante', default='000')
    """
    @api.multi
    @api.depends('payment_method_id.code')
    def _compute_is_conf_sabadell(self):
        for record in self:
            record.is_conf_sabadell = record.payment_method_id.code == \
                'conf_sabadell'
