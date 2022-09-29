# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .cttexpress_request import CTTExpressRequest
from .cttexpress_master_data import (
    CTTEXPRESS_DELIVERY_STATES_STATIC,
    CTTEXPRESS_SERVICES
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("cttexpress", "CTT Express")])
    cttexpress_user = fields.Char(string="User")
    cttexpress_password = fields.Char(string="Password")
    cttexpress_customer = fields.Char(string="Customer code")
    cttexpress_agency = fields.Char(string="Agency code")
    cttexpress_contract = fields.Char(string="Contract code")
    cttexpress_shipping_type = fields.Selection(
        selection=CTTEXPRESS_SERVICES,
        string="Shipping type",
    )
    cttexpress_document_model_code = fields.Selection(
        selection=[
            ("SINGLE", "Single"),
            ("MULTI1", "Multi 1"),
            ("MULTI3", "Multi 3"),
            ("MULTI4", "Multi 4")
        ],
        default="SINGLE",
        string="Document model",
    )
    cttexpress_document_format = fields.Selection(
        selection=[
            ("PDF", "PDF"),
            ("PNG", "PNG"),
            ("BMP", "BMP")
        ],
        default="PDF",
        string="Document format",
    )
    cttexpress_document_offset = fields.Integer(string="Document Offset")

    def _ctt_request(self):
        """Get CTT Request object

        :return CTTExpressRequest: CTT Express Request object
        """
        return CTTExpressRequest(
            user=self.cttexpress_user,
            password=self.cttexpress_password,
            agency=self.cttexpress_agency,
            customer=self.cttexpress_customer,
            contract=self.cttexpress_contract,
            prod=self.prod_environment
        )

    @api.model
    def _ctt_log_request(self, ctt_request):
        """When debug is active requests/responses will be logged in ir.logging

        :param ctt_request ctt_request: CTT Express request object
        """
        self.log_xml(ctt_request.ctt_last_request, "ctt_request")
        self.log_xml(ctt_request.ctt_last_response, "ctt_response")

    def _ctt_check_error(self, error):
        """Common error checking. We stop the program when an error is returned.

        :param list error: List of tuples in the form of (code, description)
        :raises UserError: Prompt the error to the user
        """
        if error:
            error_msg = "CTT Express Error:\n\n"
            error_msg += "\n".join(
                ["{} - {}".format(code, msg) for code, msg in error]
            )
            raise UserError(error_msg)

    @api.model
    def _cttexpress_format_tracking(self, tracking):
        """Helper to forma tracking history strings

        :param OrderedDict tracking: CTT tracking values
        :return str: Tracking line
        """
        status = "{} - [{}] {}".format(
            fields.Datetime.to_string(tracking["StatusDateTime"]),
            tracking["StatusCode"],
            tracking["StatusDescription"]
        )
        if tracking["IncidentCode"]:
            status += " ({}) - {}".format(
                tracking["IncidentCode"], tracking["IncidentDescription"]
            )
        return status

    def action_ctt_validate_user(self):
        """Maps to API's ValidateUser method

        :raises UserError: If the user credentials aren't valid
        """
        self.ensure_one()
        ctt_request = self._ctt_request()
        error = ctt_request.validate_user()
        self._ctt_log_request(ctt_request)
        # For user validation success there's an error return as well.
        # We better ignore it.
        if error[0]:
            self._ctt_check_error(error)

    def _prepare_cttexpress_shipping(self, picking):
        """Convert picking values for CTT Express API

        :param record picking: `stock.picking` record
        :return dict: Values prepared for the CTT connector
        """
        self.ensure_one()
        # A picking can be delivered from any warehouse
        sender_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        recipient = picking.partner_id
        recipient_entity = picking.partner_id.commercial_partner_id
        if picking.package_ids:
            weight = sum([p.shipping_weight or p.weight for p in picking.package_ids])
        else:
            weight = picking.shipping_weight
        return {
            "ClientReference": recipient.ref or recipient_entity.ref or "",  # Optional
            "ClientDepartmentCode": None,  # Optional (no core field matches)
            "ItemsCount": picking.number_of_packages,
            "IsClientPodScanRequired": None,  # Optional
            "RecipientAddress": recipient.street,
            "RecipientCountry": recipient.country_id.code,
            "RecipientEmail": recipient.email or recipient_entity.email,  # Optional
            "RecipientSMS": None,  # Optional
            "RecipientMobile": recipient.mobile or recipient_entity.mobile,  # Optional
            "RecipientName": recipient.name or recipient_entity.name,
            "RecipientPhone": recipient.phone or recipient_entity.phone,
            "RecipientPostalCode": recipient.zip,
            "RecipientTown": recipient.city,
            "RefundValue": None,  # Optional
            "HasReturn": None,  # Optional
            "IsSaturdayDelivery": None,  # Optional
            "SenderAddress": sender_partner.street,
            "SenderName": sender_partner.name,
            "SenderPhone": sender_partner.phone or "",
            "SenderPostalCode": sender_partner.zip,
            "SenderTown": sender_partner.city,
            "ShippingComments": None,  # Optional
            "ShippingTypeCode": self.cttexpress_shipping_type,
            "Weight": int(weight * 1000) or 1,  # Weight in grams
            "PodScanInstructions": None,  # Optional
            "IsFragile": None,  # Optional
            "RefundTypeCode": None,  # Optional
            "CreatedProcessCode": None,  # Optional
            "HasControl": None,  # Optional
            "HasFinalManagement": None,  # Optional
        }

    def cttexpress_send_shipping(self, pickings):
        """CTT Express wildcard method called when a picking is confirmed

        :param record pickings: `stock.picking` recordset
        :raises UserError: On any API error
        :return dict: With tracking number and delivery price (always 0)
        """
        ctt_request = self._ctt_request()
        result = []
        for picking in pickings:
            vals = self._prepare_cttexpress_shipping(picking)
            try:
                error, documents, tracking = ctt_request.manifest_shipping(vals)
                self._ctt_check_error(error)
            except Exception as e:
                raise(e)
            finally:
                self._ctt_log_request(ctt_request)
            vals.update({"tracking_number": tracking, "exact_price": 0})
            # The default shipping method doesn't allow to configure the label
            # format, so once we get the tracking, we ask for it again.
            documents = self.cttexpress_get_label(tracking)
            # We post an extra message in the chatter with the barcode and the
            # label because there's clean way to override the one sent by core.
            body = _("CTT Shipping Documents")
            picking.message_post(body=body, attachments=documents)
            result.append(vals)
        return result

    def cttexpress_cancel_shipment(self, pickings):
        """Cancel the expedition

        :param recordset: pickings `stock.picking` recordset
        :returns boolean: True if success
        """
        ctt_request = self._ctt_request()
        for picking in pickings.filtered("carrier_tracking_ref"):
            try:
                error = ctt_request.cancel_shipping(
                    picking.carrier_tracking_ref
                )
                self._ctt_check_error(error)
            except Exception as e:
                raise (e)
            finally:
                self._ctt_log_request(ctt_request)
        return True

    def cttexpress_get_label(self, reference):
        """Generate label for picking

        :param str reference: shipping reference
        :returns tuple: (file_content, file_name)
        """
        self.ensure_one()
        if not reference:
            return False
        ctt_request = self._ctt_request()
        try:
            error, label = ctt_request.get_documents_multi(
                reference,
                model_code=self.cttexpress_document_model_code,
                kind_code=self.cttexpress_document_format,
                offset=self.cttexpress_document_offset
            )
            self._ctt_check_error(error)
        except Exception as e:
            raise (e)
        finally:
            self._ctt_log_request(ctt_request)
        if not label:
            return False
        return label

    def cttexpress_tracking_state_update(self, picking):
        """Wildcard method for CTT Express tracking followup

        :param recod picking: `stock.picking` record
        """
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        ctt_request = self._ctt_request()
        try:
            error, trackings = (
                ctt_request.get_tracking(picking.carrier_tracking_ref)
            )
            self._ctt_check_error(error)
        except Exception as e:
            raise (e)
        finally:
            self._ctt_log_request(ctt_request)
        picking.tracking_state_history = "\n".join(
            [
                self._cttexpress_format_tracking(tracking)
                for tracking in trackings
            ]
        )
        current_tracking = trackings.pop()
        picking.tracking_state = (
            self._cttexpress_format_tracking(current_tracking)
        )
        picking.delivery_state = CTTEXPRESS_DELIVERY_STATES_STATIC.get(
            current_tracking["StatusCode"], "incidence"
        )

    def cttexpress_get_tracking_link(self, picking):
        """Wildcard method for CTT Express tracking link.

        :param record picking: `stock.picking` record
        :return str: tracking url
        """
        tracking_url = (
            "https://app.cttexpress.com/AreaClientes/Views/"
            "Destinatarios.aspx?s={}"
        )
        return tracking_url.format(picking.carrier_tracking_ref)
