# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_non_resident = fields.Boolean(string='Is non-resident',
                                     oldname='is_resident')
