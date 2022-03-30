# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class L10nEsAeatMapTaxLine(models.Model):
    _inherit = "l10n.es.aeat.map.tax.line"

    outside_spain = fields.Boolean(string="Outside of Spain")
    service_type = fields.Selection(
        string="Service type", selection=[("goods", "Goods"), ("services", "Services")]
    )
