# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    @api.onchange('use_connector')
    def _check_connector_installed(self):
        module = self.env['ir.module.module'].search(
            [('name', '=', 'connector'), ('state', '=', 'installed')])
        if not module:
            raise Warning(
                _('The module "Connector" is not installed. You have '
                  'to install it to activate this option'))

    sii_enabled = fields.Boolean(string='Enable SII')
    sii_test = fields.Boolean(string='Test Enviroment')
    chart_template_id = fields.Many2one(
        comodel_name='account.chart.template', string='Chart Template')
    use_connector = fields.Boolean(
        string='Use connector',
        help='Check it to use connector instead to send the invoice '
        'when it is validated')
