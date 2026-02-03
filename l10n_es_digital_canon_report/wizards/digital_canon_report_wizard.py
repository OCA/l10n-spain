# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class DigitalCanonReportWizard(models.TransientModel):
    _name = "digital.canon.report.wizard"
    _description = "Wizard para exportar el Canon Digital SGAE"

    date_start = fields.Date(string="Fecha inicio", required=True)
    date_end = fields.Date(string="Fecha fin", required=True)

    def action_export_xls(self):
        module = __name__.split("addons.")[1].split(".")[0]
        report_name = f"{module}.digital_canon_report"
        quarter = (self.date_start.month - 1) // 3 + 1
        year = self.date_start.year
        report_filename = f"CanonDigital_Q{quarter}_{year}"
        report = {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "report_name": report_name,
            "context": dict(self.env.context, report_file=report_filename),
            "data": {
                "dynamic_report": True,
                "date_start": self.date_start.isoformat(),
                "date_end": self.date_end.isoformat(),
            },
        }
        return report
