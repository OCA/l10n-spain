# Copyright 2009 Spanish Localization Team
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    es_libro = fields.Char(string="Book")
    es_registro_mercantil = fields.Char(string="Commercial Registry")
    es_hoja = fields.Char(string="Sheet")
    es_folio = fields.Char(string="Page")
    es_seccion = fields.Char(string="Section")
    es_tomo = fields.Char(string="Volume")
