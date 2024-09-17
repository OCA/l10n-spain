# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo import _, fields, models
from odoo.tools import float_compare

from .dhl_parcel_request import (
    DHL_PARCEL_DELIVERY_STATES_STATIC,
    DHL_PARCEL_INCOTERMS_STATIC,
    DhlParcelRequest,
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _compute_can_generate_return(self):
        res = super()._compute_can_generate_return()
        for carrier in self:
            if carrier.delivery_type == "dhl_parcel":
                carrier.can_generate_return = True
        return res

    delivery_type = fields.Selection(
        selection_add=[("dhl_parcel", "DHL Parcel")],
        ondelete={"dhl_parcel": "set default"},
    )
    dhl_parcel_customer_code = fields.Char(string="DHL Parcel customer code")
    dhl_parcel_incoterm = fields.Selection(
        string="DHL Parcel incoterms", selection=DHL_PARCEL_INCOTERMS_STATIC
    )
    dhl_parcel_product = fields.Selection(
        string="DHL Product",
        selection=[("B2B", "B2B Product"), ("B2C", "B2C Product")],
        help="If the product is not specified, it is considered B2B",
    )
    dhl_parcel_uid = fields.Char(string="DHL Parcel UID")
    dhl_parcel_password = fields.Char(string="DHL Parcel Password")
    dhl_parcel_last_end_day_report = fields.Binary(
        string="DHL Parcel last manual end day report"
    )
    dhl_parcel_last_end_day_report_name = fields.Char(string="Filename")
    dhl_parcel_label_format = fields.Selection(
        selection=[("PDF", "PDF"), ("ZPL", "ZPL"), ("EPL", "EPL")],
        default="PDF",
        string="Label format",
    )
    dhl_parcel_cash_on_delivery = fields.Boolean(
        string="Cash on delivery",
        help=(
            "If checked, it means that the carrier is paid with cash. It assumes "
            "there is a sale order linked and it will use that "
            "total amount as the value to be paid. "
            "It will also exclude this carrier from the e-commerce checkout."
        ),
    )

    def dhl_parcel_get_tracking_link(self, picking):
        """Provide tracking link for the customer"""
        tracking_url = (
            "https://clientesparcel.dhl.es/seguimientoenvios/integra/"
            "SeguimientoDocumentos.aspx?codigo={}&anno={}&lang=sp"
        )
        return tracking_url.format(
            picking.carrier_tracking_ref, fields.Date.today().year
        )

    def _prepare_dhl_parcel_address_info(self, partner):
        phone = partner.phone and partner.phone.replace(" ", "") or ""
        mobile = partner.mobile and partner.mobile.replace(" ", "") or ""
        address = partner.street or ""
        if partner.street2:
            address += " " + partner.street2
        partner_name = partner.name
        # We have a limit of 40 chars, so we'll try to allocate as much space possible
        # for both parent an contact name, trying to use all the available space if
        # possible and otherwise, cutting it to 19 chars max (letting 2 chars for
        # the separation of both names)
        if partner.parent_id:
            max_parent_length = min(
                len(partner.parent_id.name), 19 + max(19 - len(partner_name), 0)
            )
            partner_name = (
                f"{partner.parent_id.name[:max_parent_length]}, {partner_name}"
            )
        return {
            "Name": partner_name[:40],
            "Address": address[:40],
            "City": partner.city or "",
            "PostalCode": partner.zip or "",
            "Country": partner.country_id.code or "",
            "Phone": phone or mobile,
            "Email": partner.email or "",
        }

    def _get_dhl_parcel_receiver_info(self, picking):
        return self._prepare_dhl_parcel_address_info(picking.partner_id)

    def _get_dhl_parcel_sender_info(self, picking):
        """Optional, if the sender information is not
        sent, they will be fetched from DHL web Service B2B.
        """
        return self._prepare_dhl_parcel_address_info(
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )

    def _get_dhl_parcel_product(self, picking):
        product = self.dhl_parcel_product
        if product == "B2C" and picking.is_return_picking:
            product = "R2C"
        return product or "B2B"

    def _prepare_dhl_parcel_shipping(self, picking):
        """Convert picking values for dhl parcel api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        # El peso debe tener 2 decimales para evitar errores en el cierre del día
        weight = round(picking.shipping_weight, 2)
        # El peso del envío tiene que ser como mínimo 1 kilo o como máximo 99999 kilos
        if float_compare(weight, 1, precision_digits=2) == -1:
            weight = 1
        vals = {
            "Customer": self.dhl_parcel_customer_code,
            "Receiver": self._get_dhl_parcel_receiver_info(picking),
            "Sender": self._get_dhl_parcel_sender_info(picking),  # [optional]
            "Reference": picking.name,  # [optional]
            "Quantity": picking.number_of_packages,  # 1-999
            "Weight": weight,  # in kg, 1-99999
            "WeightVolume": "",  # [optional] Volume, in kg
            "CODAmount": "",  # [optional]
            "CODExpenses": "",  # [optional], mandatory if CODAmount filled
            "CODCurrency": "",  # [optional], mandatory if CODAmount filled
            "InsuranceAmount": "",  # [optional]
            "InsuranceExpenses": "",  # [optional], mandatory if InsuranceAmount filled
            "InsuranceCurrency": "",  # [optional], mandatory if InsuranceAmount filled
            "DeliveryNote": "",  # [optional]
            "ServiceType": "",  # [optional]
            "Remarks1": "",  # [optional]
            "Remarks2": "",  # [optional]
            "Incoterms": self.dhl_parcel_incoterm,  # CPT paid, EXW owed
            "Product": self._get_dhl_parcel_product(picking),
            "ContactName": "",  # [optional]
            "GoodsDescription": "",  # [optional]
            "CustomsValue": "",  # [optional]
            "CustomsCurrency": "",  # [optional]
            "Format": self.dhl_parcel_label_format,  # [optional]
            "tracking_number": False,
            "exact_price": 0,
        }
        if self.dhl_parcel_cash_on_delivery and picking.sale_id:
            sale = picking.sale_id
            mapped_expenses = {"CPT": "P", "EXW": "D"}
            vals.update(
                {
                    "CODAmount": sale.amount_total,
                    "CODExpenses": mapped_expenses.get(self.dhl_parcel_incoterm, "P"),
                    "CODCurrency": sale.currency_id.name,
                }
            )
        return vals

    def dhl_parcel_send_shipping(self, pickings):
        """Send the package to DHL Parcel
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        dhl_parcel_request = DhlParcelRequest(self)
        result = []
        for picking in pickings:
            vals = self._prepare_dhl_parcel_shipping(picking)
            response = dhl_parcel_request.create_shipment(vals)
            if not response:
                result.append(vals)
                continue
            vals["tracking_number"] = response.get("Tracking", "")
            # We post an extra message in the chatter with the rest of the response
            body = _(
                "DHL Parcel Shipping extra info:\n"
                "Origin: %(origin)s, Customer: %(customer)s, AWB: %(awb)s, LP: %(lp)s"
            ) % {
                       "origin": response.get("Origin", "N/A"),
                       "customer": response.get("Customer", "N/A"),
                       "awb": response.get("AWB", "N/A"),
                       "lp": response.get("LP", "N/A"),
                   }
            attachment = []
            if response.get("Label"):
                label_format = picking.carrier_id.dhl_parcel_label_format.lower()
                attachment = [
                    (
                        "dhl_parcel_{}.{}".format(
                            response.get("Tracking", ""),
                            "pdf" if label_format == "pdf" else "txt",
                        ),
                        base64.b64decode(response.get("Label")),
                    )
                ]
            picking.message_post(body=body, attachments=attachment)
            result.append(vals)
        return result

    def dhl_parcel_tracking_state_update(self, picking):
        """Tracking state update"""
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        dhl_parcel_request = DhlParcelRequest(self)
        tracking_events = dhl_parcel_request.track_shipment(
            picking.carrier_tracking_ref, "events"
        )
        if not tracking_events:
            return
        picking.tracking_state_history = "\n".join(
            [
                "{} {} - [{}] {}".format(
                    t.get("DateTime"),
                    t.get("Ubication"),
                    t.get("Code"),
                    t.get("Status"),
                )
                for t in tracking_events
            ]
        )
        tracking = tracking_events.pop()
        picking.tracking_state = "[{}] {}".format(
            tracking.get("Code"), tracking.get("Status")
        )
        picking.delivery_state = DHL_PARCEL_DELIVERY_STATES_STATIC.get(
            tracking.get("Code"), "incident"
        )

    def dhl_parcel_cancel_shipment(self, pickings):
        """Cancel the expedition"""
        dhl_parcel_request = DhlParcelRequest(self)
        for picking in pickings.filtered("carrier_tracking_ref"):
            response = dhl_parcel_request.cancel_shipment(picking.carrier_tracking_ref)
            if not response:
                msg = _(
                    "DHL Parcel Cancellation failed with reason: %s"
                ) % response.get("Message", "Connection Error")
                picking.message_post(body=msg)
                continue
            picking.carrier_tracking_ref = False
            picking.message_post(
                body=_("DHL Parcel Expedition with reference %s cancelled")
                     % picking.carrier_tracking_ref
            )

    def dhl_parcel_get_label(self, carrier_tracking_ref):
        """Generate label for picking
        :param str carrier_tracking_ref - tracking reference
        :returns base64 encoded label
        """
        self.ensure_one()
        if not carrier_tracking_ref:
            return False
        dhl_parcel_request = DhlParcelRequest(self)
        label = dhl_parcel_request.print_shipment(carrier_tracking_ref)
        return label or False

    def dhl_parcel_hold_shipment(self, carrier_tracking_ref):
        """Hold shipment
        :param str carrier_tracking_ref - tracking reference
        :returns boolean
        """
        self.ensure_one()
        if not carrier_tracking_ref:
            return False
        dhl_parcel_request = DhlParcelRequest(self)
        return dhl_parcel_request.hold_shipment(carrier_tracking_ref)

    def dhl_parcel_release_shipment(self, carrier_tracking_ref):
        """Release shipment
        :param str carrier_tracking_ref - tracking reference
        :returns boolean
        """
        self.ensure_one()
        if not carrier_tracking_ref:
            return False
        dhl_parcel_request = DhlParcelRequest(self)
        return dhl_parcel_request.release_shipment(carrier_tracking_ref)

    def dhl_parcel_rate_shipment(self, order):
        """Not implemented with DHL, these values are so it works with websites"""
        return {
            "success": True,
            "price": self.product_id.lst_price,
            "error_message": _(
                """DHL Parcel API doesn't provide methods to compute delivery rates, so
                you should rely on another price method instead or override this
                one in your custom code."""
            ),
            "warning_message": _(
                """DHL Parcel API doesn't provide methods to compute delivery rates, so
                you should rely on another price method instead or override this
                one in your custom code."""
            ),
        }

    def action_open_end_day(self):
        """Action to launch the end day wizard"""
        self.ensure_one()
        wizard = self.env["dhl.parcel.endday.wizard"].create(
            {"carrier_id": self.id, "customer_accounts": self.dhl_parcel_customer_code}
        )
        view_id = self.env.ref("delivery_dhl_parcel.delivery_endday_wizard_form").id
        return {
            "name": _("DHL Parcel End Day"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "dhl.parcel.endday.wizard",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "target": "new",
            "res_id": wizard.id,
            "context": self.env.context,
        }
