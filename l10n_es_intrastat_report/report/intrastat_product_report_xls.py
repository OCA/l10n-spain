# Copyright 2009-2018 Noviat
# Copyright 2020 Manuel Calero - Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class IntrastatProductDeclarationXlsx(models.AbstractModel):
    _inherit = "report.intrastat_product.product_declaration_xls"

    def _get_template(self, declaration):
        res = super()._get_template(declaration)
        aux_dict = {}
        if (
            self.env.context.get("declaration_type", False) == "dispatches"
            and int(self.env.context.get("declaration_year", 0)) >= 2022
        ):
            aux_dict["partner_vat"] = {
                "header": {"type": "string", "value": self._("VAT")},
                "line": {"type": "string", "value": self._render("line.partner_vat")},
                "width": 18,
            }
        res.update(aux_dict)
        return res
