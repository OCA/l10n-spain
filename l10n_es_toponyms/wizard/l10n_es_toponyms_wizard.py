# -*- coding: utf-8 -*-
# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, tools
import os


class ConfigEsToponyms(models.TransientModel):
    _name = 'config.es.toponyms'
    _inherit = 'res.config.installer'

    name = fields.Char('Name', size=64)

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
        wizard_obj = self.env['better.zip.geonames.import']
        country_es = self.env['res.country'].search([('code', '=', 'ES')])
        wizard = wizard_obj.create({'country_id': country_es.id})
        wizard.run_import()
        return res

    @api.multi
    def execute_local(self):  # pragma: no cover
        self.create_zipcodes()
