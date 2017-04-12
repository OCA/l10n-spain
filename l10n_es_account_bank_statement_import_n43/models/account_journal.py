# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    n43_date_type = fields.Selection(string='Date type for N43 Import',
                                     selection=[('fecha_valor', 'Value Date'),
                                     ('fecha_oper', 'Operation Date')],
                                     required=True, default='fecha_valor')
