# Copyright 2020-2022 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).


import openpyxl

from odoo import exceptions, models, tools
from odoo.tools.misc import file_path

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
    _description = "Intrastat HS Code Import for Spain"

    @tools.ormcache("name")
    def _get_intrastat_unit(self, name):
        return self.env["intrastat.unit"].search([("name", "=", name)]).id

    def _import_hs_codes(self):
        code_obj = self.env["hs.code"].with_context(active_test=False)
        path = file_path("l10n_es_intrastat_report/data/CN2026_Structure.xlsx")
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet_rows = list(wb.worksheets[0].iter_rows(min_row=2, values_only=True))
        vals_list = []
        parents = []
        prev_level = 0
        for row in sheet_rows:
            code = str(row[1] or "").replace(" ", "")
            description = str(row[4] or "")
            nbdash = row[2]
            if nbdash is None:
                level = 2 if str(row[1] or "").strip().isdigit() else 1
            else:
                level = int(nbdash) + 3
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
                iu = str(row[5] or "").replace("\xa0", " ").strip()
                if iu and iu != "-":  # specific unit
                    if iu in UOM_MAPPING:
                        iu_unit_id = self.env.ref(
                            f"intrastat_product.{UOM_MAPPING[iu]}"
                        ).id
                    else:
                        iu_unit_id = self._get_intrastat_unit(iu)
                    if iu_unit_id:
                        vals["intrastat_unit_id"] = iu_unit_id
                    else:
                        raise exceptions.UserError(
                            self.env._("Unit not found: '%s'", iu)
                        )
                vals_list.append(vals)
        if vals_list:
            code_obj.create(vals_list)

    def action_import_hs_codes(self):
        company = self.env.company
        if (company.country_id.code or "").lower() != "es":
            raise exceptions.UserError(
                self.env._("Current company is not Spanish, so it can't be configured.")
            )
        self._import_hs_codes()
