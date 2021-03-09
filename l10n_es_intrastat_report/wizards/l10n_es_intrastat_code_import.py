# Copyright 2020 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import os

from odoo import _, exceptions, models, tools

try:
    import xlrd
except ImportError:
    xlrd = None


UOM_MAPPING = {
    "p/st": "intrastat_unit_pce",
    "100 p/st": "intrastat_unit_100pce",
    "1000 p/st": "intrastat_unit_1000pce",
    "l alc. 100%": "intrastat_unit_l_alc_100_pct",
    "kg 90% sdt": "intrastat_unit_kg_90_pct_sdt",
}


class L10nEsPartnerImportWizard(models.TransientModel):
    _name = "l10n.es.intrastat.code.import"
    _description = "Intrastat Code Import"
    _inherit = "res.config.installer"

    @tools.ormcache("name")
    def _get_intrastat_unit(self, name):
        return self.env["intrastat.unit"].search([("name", "=", name)]).id

    def _import_hs_codes(self):
        if not xlrd:  # pragma: no cover
            raise exceptions.UserError(_("xlrd library not found."))
        code_obj = self.env["hs.code"]
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "NC_20.xlsx"
        )
        workbook = xlrd.open_workbook(path)
        sheet = workbook.sheet_by_index(0)
        vals_list = []
        parents = []
        prev_level = ""
        for nrow in range(1, sheet.nrows):
            code = sheet.cell_value(nrow, 1).replace(" ", "")
            description = sheet.cell_value(nrow, 5).lstrip("-")
            level = sheet.cell_value(nrow, 4)
            temp = prev_level
            while temp > level and parents:
                del parents[-1]
                temp = temp[:-1]
            if len(code) < 8 and description != description.upper():
                parents.append(description)
            prev_level = level
            if len(code) != 8:  # bypass parent lines
                continue
            vals = {
                "local_code": code,
                "description": " /".join(parents + [description]),
            }
            iu = sheet.cell_value(nrow, 6)
            if iu and iu != "-":  # specific unit
                if iu in UOM_MAPPING:
                    iu_unit_id = self.env.ref(
                        "intrastat_product.%s" % UOM_MAPPING[iu]
                    ).id
                else:
                    iu_unit_id = self._get_intrastat_unit(iu)
                if iu_unit_id:
                    vals["intrastat_unit_id"] = iu_unit_id
                else:
                    raise exceptions.UserError(_("Unit not found: '%s'") % iu)
            if not code_obj.search([("local_code", "=", code)]):
                vals_list.append(vals)
        if vals_list:
            code_obj.create(vals_list)

    def _set_defaults(self, company):
        module = __name__.split("addons.")[1].split(".")[0]
        transaction = self.env.ref("%s.intrastat_transaction_11" % module)
        for field in [
            "intrastat_transaction_out_invoice",
            "intrastat_transaction_out_refund",
            "intrastat_transaction_in_invoice",
            "intrastat_transaction_in_refund",
        ]:
            if not company[field]:
                company[field] = transaction

    def execute(self):
        company = self.env.company
        if company.country_id.code.lower() != "es":
            raise exceptions.UserError(
                _("Current company is not Spanish, so it can't be configured.")
            )
        self._set_defaults(company)
        self._import_hs_codes()
