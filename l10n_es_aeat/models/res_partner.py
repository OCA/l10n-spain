# Copyright 2019 Juanvi Pascual <jvpascual@puntsistemes.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    representative_vat = fields.Char(
        string="L.R. VAT number", size=9,
        help="Legal Representative VAT number.")
