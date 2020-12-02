# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WebServiceBackend(models.Model):

    _inherit = "webservice.backend"

    protocol = fields.Selection(selection_add=[("face", "FACe")])
