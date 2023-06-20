# Copyright 2020-2022 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import os

import xlrd

from odoo import _, exceptions, models, tools
from odoo.modules.module import get_resource_path

UOM_MAPPING = {
    "p/st": "intrastat_unit_pce",
    "100 p/st": "intrastat_unit_100pce",
    "1000 p/st": "intrastat_unit_1000pce",
    "l alc. 100%": "intrastat_unit_l_alc_100_pct",
    "kg 90% sdt": "intrastat_unit_kg_90_pct_sdt",
    "m²": "intrastat_unit_m2",
    "m³": "intrastat_unit_m3",
    "1000 m³": "intrastat_unit_1000m3",
}


class L10nEsPartnerImportWizard(models.TransientModel):
    _name = "l10n.es.intrastat.code.import"
    _inherit = "res.config.installer"
    _description = "Intrastat HS Code Import for Spain"

    @tools.ormcache("name")
    def _get_intrastat_unit(self, name):
        return self.env["intrastat.unit"].search([("name", "=", name)]).id

    def _import_hs_codes(self):
        code_obj = self.env["hs.code"].with_context(active_test=False)
        path = os.path.join(
            get_resource_path("l10n_es_intrastat_report"), "data", "Estruc_NC2023.xlsx"
        )
        workbook = xlrd.open_workbook(path)
        sheet = workbook.sheet_by_index(0)
        vals_list = []
        parents = []
        prev_level = 0
        for nrow in range(1, sheet.nrows):
            code = sheet.cell_value(nrow, 2).replace(" ", "")
            description = sheet.cell_value(nrow, 6).lstrip("-")
            level = int(sheet.cell_value(nrow, 3))
            temp = prev_level
            while temp > level and parents:
                del parents[-1]
                temp -= 1
            if len(code) < 8 and description != description.upper():
                parents.append(description)
            prev_level = level
            if len(code) != 8:  # bypass parent lines
                continue
            vals = {
                "local_code": code,
                "description": " /".join(parents + [description]),
            }
            if not code_obj.search([("local_code", "=", code)]):
                iu = sheet.cell_value(nrow, 5).replace("\xa0", " ")
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
                vals_list.append(vals)
        if vals_list:
            code_obj.create(vals_list)

    def execute(self):
        company = self.env.company
        if (company.country_id.code or "").lower() != "es":
            raise exceptions.UserError(
                _("Current company is not Spanish, so it can't be configured.")
            )
        self._import_hs_codes()
