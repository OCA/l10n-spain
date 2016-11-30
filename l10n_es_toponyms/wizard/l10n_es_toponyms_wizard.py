# -*- coding: utf-8 -*-
# © 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# © 2013-2016 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, tools
import os


class ConfigEsToponyms(models.TransientModel):
    _name = 'config.es.toponyms'
    _inherit = 'res.config.installer'

    name = fields.Char('Name', size=64)
    state = fields.Selection(
        selection=[
            ('official', 'Official'),
            ('spanish', 'Spanish'),
            ('both', 'Both')
        ],
        required=True, string='State names', default='both')
    city_info = fields.Selection(
        selection=[
            ('yes', 'Yes'),
            ('no', 'No')
        ],
        required=True, string='City information', default='yes')

    @api.model
    def create_states(self, state_type):
        """Import spanish states information through an XML file."""
        file_name = 'l10n_es_toponyms_states_%s.xml' % state_type
        path = os.path.join('l10n_es_toponyms', 'wizard', file_name)
        with tools.file_open(path) as fp:
            tools.convert_xml_import(self.env.cr, 'l10n_es_toponyms', fp, {},
                                     'init', noupdate=True)
        return True

    @api.model
    def create_zipcodes(self):
        """Import spanish zipcodes information through an XML file."""
        file_name = 'l10n_es_toponyms_zipcodes.xml'
        path = os.path.join('l10n_es_toponyms', 'wizard', file_name)
        with tools.file_open(path) as fp:
            tools.convert_xml_import(self.env.cr, 'l10n_es_toponyms', fp, {},
                                     'init', noupdate=True)
        return True

    @api.multi
    def execute(self):
        res = super(ConfigEsToponyms, self).execute()
        # Import spanish states (official, Spanish or both)
        self.create_states(self.state)
        # Import spanish cities and zip codes
        if self.city_info == 'yes':
            wizard_obj = self.env['better.zip.geonames.import']
            country_es = self.env['res.country'].search([('code', '=', 'ES')])
            wizard = wizard_obj.create({'country_id': country_es.id})
            wizard.run_import()
        return res

    @api.multi
    def execute_local(self):
        # Import spanish states (official, Spanish or both)
        self.create_states(self.state)
        # Import spanish cities and zip codes
        if self.city_info == 'yes':
            self.create_zipcodes()
