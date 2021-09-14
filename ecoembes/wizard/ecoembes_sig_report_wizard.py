# Copyright 2017 FactorLibre - Janire Olagibel
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import datetime
from io import BytesIO

import xlwt

from odoo import _, fields, models

FIELDS = {
    "period": {"title": "PERIOD_ID", "format": "int"},
    "product_name": {"title": "FORMA_ID", "format": "int"},
    "default_code": {"title": "default_code", "format": "general"},
    "billing": {"title": "Facturacion", "format": "money"},
    "quantity": {"title": "VENTA_QT", "format": "int"},
}
FIELDS_ORDER = ["period", "product_name", "default_code", "billing", "quantity"]


class EcoembesSigReportWizard(models.TransientModel):
    _name = "ecoembes.sig.report.wizard"
    _description = "Ecoembes Sig Report Wizard"

    date_start = fields.Date(string="Date start", required=True)
    date_end = fields.Date(string="Date end", required=True)
    name = fields.Char(string="File name", readonly=True)
    datas = fields.Binary(string="File", readonly=True)
    state = fields.Selection(
        selection=[("start", _("Start")), ("end", _("End"))],
        string="State",
        default="start",
    )

    def get_formats(self):
        borders = xlwt.Borders()
        borders.left = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.top = xlwt.Borders.THIN
        borders.bottom = xlwt.Borders.THIN
        styles = {
            "title": xlwt.easyxf("font: bold on;"),
            "general": xlwt.easyxf(
                "borders: left thin, right thin, top thin, bottom thin;"
            ),
        }
        style_default = xlwt.XFStyle()
        style_default.borders = borders
        # int
        style = style_default
        style.num_format_str = "0"
        styles.update({"int": style})
        # float
        style = style_default
        style.num_format_str = "#,##0.00"
        styles.update({"float": style})
        # money
        style = style_default
        style.num_format_str = "#,##0.00 [$€-C0A];-#,##0.00 [$€-C0A]"
        styles.update({"money": style})
        # percentage
        style = style_default
        style.num_format_str = "0.00%"
        styles.update({"percentage": style})
        # date
        style = xlwt.XFStyle()
        style.num_format_str = "D-MMM-YY"
        styles.update({"date": style})
        # datetime
        style = style_default
        style.num_format_str = "D-MMM-YY h:mm"
        styles.update({"datetime": style})
        return styles

    def get_report_items(self):
        return self.env["account.move.line.ecoembes.report"].search(
            [
                ("invoice_date", ">=", self.date_start),
                ("invoice_date", "<=", self.date_end),
            ]
        )

    def confirm(self):
        self.ensure_one()
        items = self.get_report_items()
        w = xlwt.Workbook()
        ws = w.add_sheet("SIG data", cell_overwrite_ok=True)
        styles = self.get_formats()
        # Set headers
        for col, field in enumerate(FIELDS_ORDER):
            value = FIELDS[field]["title"]
            ws.write(0, col, value, style=styles[FIELDS[field]["format"]])
        # Set records
        x = 1
        for record in items:
            for y, field in enumerate(FIELDS_ORDER):
                style = styles[FIELDS[field]["format"]]
                ws.write(x, y, record[field], style=style)
            x += 1
        excel_temp = BytesIO()
        w.save(excel_temp)
        out = base64.encodestring(excel_temp.getvalue())
        excel_temp.close()
        self.write(
            {"datas": out, "name": _("SIG-%s.xls") % (datetime.now()), "state": "end"}
        )
        data_obj = self.env.ref("ecoembes.ecoembes_sig_report_wizard_form")
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_id": [data_obj.id],
            "res_id": self.id,
            "target": "new",
        }
