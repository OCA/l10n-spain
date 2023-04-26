# (c) 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés , Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class PaymentMode(models.Model):
    _inherit = 'account.payment.mode'
    """
    conf_abanca_type = fields.Selection(
        string='Tipo de pago', default='56',
        selection=[('56', 'Tranferencia'),
                   ('57', 'Cheques')])
    """
    is_conf_abanca = fields.Boolean(compute="_compute_is_conf_abanca")
    num_contract = fields.Char('Nº Contrato confirming')

    """
    En las especificaciones del fichero no veo ninguna mención al sufijo
    sufix = fields.Char('Sufijo ordenante', default='000')
    """
    @api.multi
    @api.depends('payment_method_id.code')
    def _compute_is_conf_abanca(self):
        for record in self:
            record.is_conf_abanca = record.payment_method_id.code == \
                'conf_abanca'
