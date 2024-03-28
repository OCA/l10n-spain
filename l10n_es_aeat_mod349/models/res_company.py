# Copyright 2024 Sygel - <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_tax_ids_from_xmlids(self, tax_templates):
        taxes_ids = []
        for tax_template in tax_templates:
            tax_id = self._get_tax_id_from_xmlid(tax_template.name)
            if tax_id:
                taxes_ids.append(tax_id)
        return taxes_ids
