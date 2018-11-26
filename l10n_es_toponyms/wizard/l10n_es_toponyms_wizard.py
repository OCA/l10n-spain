# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013-2017 Tecnativa - Pedro M. Baeza
# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ConfigEsToponyms(models.TransientModel):
    _name = 'config.es.toponyms'
    _inherit = 'res.config.installer'

    name = fields.Char('Name', size=64)

    @api.multi
    def execute(self):
        res = super(ConfigEsToponyms, self).execute()
        wizard_obj = self.env['city.zip.geonames.import']
        country_es = self.env['res.country'].search([('code', '=', 'ES')])
        wizard = wizard_obj.create({'country_id': country_es.id})
        wizard.run_import()
        return res
