# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# Copyright 2022 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models

from ..models.dhl_parcel_request import DhlParcelRequest


class DhlParcelEndDayWizard(models.TransientModel):
    _name = "dhl.parcel.endday.wizard"
    _description = "Manually end the day"

    customer_accounts = fields.Char(
        string="Customer codes to end day for",
        help=(
            "If doing multiple, input them separated by commas without spaces.\n"
            "i.e. '001-000001,002-000002'\n"
            "You can also use 'ALL' to end all of them"
        ),
    )
    all_customer_accounts = fields.Boolean(string="All customer accounts")
    carrier_id = fields.Many2one(
        string="DHL Parcel Service",
        comodel_name="delivery.carrier",
        domain=[("delivery_type", "=", "dhl_parcel")],
        required=True,
    )

    def button_end_day(self):
        dhl_parcel_request = DhlParcelRequest(self.carrier_id)
        customer_accounts = (
            "ALL" if self.all_customer_accounts else self.customer_accounts
        )
        res = dhl_parcel_request.end_day(customer_accounts, "PDF")
        self.carrier_id.write(
            {
                "dhl_parcel_last_end_day_report": (res.get("Report", False)),
                "dhl_parcel_last_end_day_report_name": "dhl_endday_{}.pdf".format(
                    fields.Datetime.today()
                ),
            }
        )
