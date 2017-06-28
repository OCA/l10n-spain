# -*- coding: utf-8 -*-
# Copyright 2017 - Aselcis Consulting (http://www.aselcis.com)
#                - Miguel Paraíso <miguel.paraiso@aselcis.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.model
    def _uncheck_group_by(self):
        # Uncheck all pos configurations 'group_by' field
        for pos_config in self.env['pos.config'].search(
                [('group_by', '=', True)]):
            pos_config.write({'group_by': False})
