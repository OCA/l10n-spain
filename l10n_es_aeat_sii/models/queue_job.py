# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, models


class QueueJob(models.Model):
    _inherit = 'queue.job'

    @api.multi
    def do_now(self):
        self.write({'eta': 0})
