# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import os
try:
    import xlrd
except ImportError:
    xlrd = None

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
    _name = 'l10n.es.intrastat.code.import'
    _inherit = 'res.config.installer'

    @tools.ormcache("name")
    def _get_intrastat_unit(self, name):
        return self.env['intrastat.unit'].search([('name', '=', name)]).id

    def _import_hs_codes(self):
        if not xlrd:  # pragma: no cover
            raise exceptions.UserError(_("xlrd library not found."))
        code_obj = self.env['hs.code']
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

    def _set_defaults(self, company):
        module = __name__.split('addons.')[1].split('.')[0]
        transaction = self.env.ref(
            '%s.intrastat_transaction_11' % module)
        for field in [
            "intrastat_transaction_out_invoice",
            "intrastat_transaction_out_refund",
            "intrastat_transaction_in_invoice",
            "intrastat_transaction_in_refund",
        ]:
            if not company[field]:
                company[field] = transaction

    def execute(self):
        company = self.env.user.company_id
        if company.country_id.code.lower() != 'es':
            raise exceptions.UserError(_(
                "Current company is not Spanish, so it can't be configured."
            ))
        self._set_defaults(company)
        self._import_hs_codes()
