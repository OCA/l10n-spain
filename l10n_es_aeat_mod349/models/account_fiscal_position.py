# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class AccountFiscalPosition(models.Model):
    """Inheritance of Account fiscal position to add field 'include_in_mod349'.
    This fields let us map fiscal position, taxes and accounts to create an
    AEAT 349 Report
    """
    _inherit = 'account.fiscal.position'

    intracommunity_operations = fields.Boolean('Intra-Community operations')
