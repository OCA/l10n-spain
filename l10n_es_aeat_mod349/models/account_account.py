# -*- coding: utf-8 -*-
##############################################################################

from openerp import models, fields


class ccountAccount(models.Model):

    _inherit = 'account.account'

    not_in_mod349 = fields.Boolean(string='Not in mod349')
