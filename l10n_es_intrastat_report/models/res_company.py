# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    intrastat_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Default Intrastat State',
        help="This value will be used if the State cannot be "
             "determined from the invoice or the warehouse.")
