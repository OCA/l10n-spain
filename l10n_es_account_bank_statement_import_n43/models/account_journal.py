# -*- coding: utf-8 -*-
# See README file for full copyright and licensing details.

from openerp import models, fields


class account_journal(models.Model):
    _inherit = "account.journal"

    date_type = fields.Selection(string='Date type for N43 Import',
                                 selection=[('fecha_valor', 'Value Date'),
                                            ('fecha_oper', 'Operation Date')],
                                 required=True, default='fecha_valor')
