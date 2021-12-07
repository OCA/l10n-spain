# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013-2017 Tecnativa - Pedro M. Baeza
# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ConfigEsToponyms(models.TransientModel):
    _name = "config.es.toponyms"
    _inherit = "res.config.installer"
    _description = "Config ES Toponyms"

    name = fields.Char(size=64)

    def execute(self):
        res = super().execute()
        wizard_obj = self.env["city.zip.geonames.import"]
        country_es = self.env["res.country"].search([("code", "=", "ES")])
        wizard = wizard_obj.create({"country_ids": [(4, country_es.id)]})
        wizard.run_import()
        return res
