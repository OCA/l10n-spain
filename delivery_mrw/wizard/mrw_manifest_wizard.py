import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError


class DeliveryMRWManifiestoWizard(models.TransientModel):
    _name = "mrw.manifest.wizard"
    _description = "Get the MRW Manifest for the given date"

    date_from = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    carrier_id = fields.Many2one(
        string="MRW Service",
        help="If no service is selected, all MRW type shippment methods will"
        " be printed",
        comodel_name="delivery.carrier",
        domain=[("delivery_type", "=", "mrw")],
    )

    def get_service_selection_value(self, field, picking):
        select_dict = dict(
            self.env["delivery.carrier"].fields_get(allfields=[field])[field][
                "selection"
            ]
        )
        value = select_dict[getattr(picking.carrier_id, field)]
        return value

    def get_manifest(self):
        """List of shippings for the given dates"""
        manifest_data = []
        date_inf = datetime.datetime.combine(self.date_from, datetime.time(0, 0, 0))
        date_sup = datetime.datetime.combine(self.date_from, datetime.time(23, 59, 59))
        pickings = self.env["stock.picking"].search(
            [
                ("scheduled_date", ">=", date_inf),
                ("scheduled_date", "<=", date_sup),
                ("carrier_id.delivery_type", "=", "mrw"),
                ("state", "=", "done"),
                ("company_id", "in", self.env.companies.ids),
            ]
        )
        if self.carrier_id:
            pickings.filtered(lambda x: x.carrier_id == self.carrier_id)
        for picking in pickings:
            manifest_data.append(
                {
                    "carrier_tracking_ref": picking.carrier_tracking_ref,
                    "reference": picking.sudo().sale_id.client_order_ref
                    or picking.sudo().sale_id.name
                    or "",
                    "note": picking.note[:25] + "..." if picking.note else "",
                    "date": picking.scheduled_date.date(),
                    "partner": picking.partner_id.name or "",
                    "zip": picking.partner_id.zip or "",
                    "address": picking.partner_id.street
                    + " "
                    + (picking.partner_id.street2 or ""),
                    "city": picking.partner_id.city or "",
                    "state": picking.partner_id.state_id.name or "",
                    "service": picking.carrier_id.name
                    + ": "
                    + self.get_service_selection_value("mrw_national_service", picking)
                    if not picking.carrier_id.international_shipping
                    else self.get_service_selection_value(
                        "mrw_international_service", picking
                    ),
                    "number_of_packages": picking.number_of_packages,
                    "weight": picking.weight or "0",
                    "refund": picking.sudo().sale_id.amount_total
                    if picking.carrier_id.mrw_reembolso != "N"
                    else "",
                }
            )
        if not manifest_data:
            raise UserError(
                _(
                    "It wasn't possible to get the manifest. Maybe there aren't"
                    "deliveries for the selected date."
                )
            )
        datas = {
            "ids": self.env.context.get("active_ids", []),
            "deliveries": manifest_data,
            "model": "mrw.manifest.wizard",
            "date_from": self.date_from,
            "company_name": self.env.company.name,
        }
        return (
            self.env.ref("delivery_mrw.mrw_manifest_report")
            .with_context(landscape=True)
            .report_action(self, data=datas)
        )
