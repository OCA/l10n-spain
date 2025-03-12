# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from dateutil.parser import isoparse

from odoo import _, api, fields, models

from .seur_master_data import PRODUCT_CODES, SERVICE_CODES, TRACKING_STATES_MAP
from .seur_request_atlas import SeurAtlasRequest

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("seur_atlas", "Seur Atlas")],
        ondelete={"seur_atlas": "set default"},
    )
    seur_atlas_vat = fields.Char(
        string="Account VAT",
        default=lambda self: self.env.company.vat,
    )
    seur_atlas_account_code = fields.Char(
        string="Account code (CCC)",
    )
    seur_atlas_username = fields.Char()
    seur_atlas_password = fields.Char()
    seur_atlas_secret = fields.Char()
    seur_atlas_client = fields.Char()
    seur_atlas_service_code = fields.Selection(
        selection=SERVICE_CODES,
        string="Service code",
    )
    seur_atlas_product_code = fields.Selection(
        selection=PRODUCT_CODES,
        string="Product code",
    )
    seur_atlas_label_format = fields.Selection(
        selection=[("PDF", "PDF"), ("ZPL", "ZPL"), ("A4_3", "Die-cut A4")],
        default="PDF",
    )
    seur_atlas_label_template = fields.Selection(
        selection=[
            ("NORMAL", "NORMAL"),
            ("CUSTOM_REFERENCE", "CUSTOM_REFERENCE"),
            ("Z4_ONE_BODY", "Z4_ONE_BODY"),
            ("Z4_TWO_BODIES", "Z4_TWO_BODIES"),
            ("GEOLABEL", "GEOLABEL"),
        ],
        default="NORMAL",
        help="Type of generated label",
    )
    seur_atlas_label_output_type = fields.Selection(
        selection=[
            ("LABEL", "Label"),
            ("LINK", "Link"),
            ("LABEL_AND_LINK", "Label and link"),
        ],
        default="LABEL",
        help="Return the file, a link to download the file or both",
    )
    seur_atlas_qr = fields.Boolean(
        help="Generate an AZTEC QR code. Only valid for ECB pickups"
    )

    def _seur_atlas_request(self) -> SeurAtlasRequest:
        """Get the credentials for SEUR ATLAS API"""
        return SeurAtlasRequest(
            user=self.seur_atlas_username,
            password=self.seur_atlas_password,
            secret=self.seur_atlas_secret,
            client_id=self.seur_atlas_client,
            acc_number=self.seur_atlas_account_code,
            id_number=self.seur_atlas_vat,
            prod=self.prod_environment,
            # We can modify the general request timeout if needed
            timeout=self.env["ir.config_parameter"]
            .sudo()
            .get_param("seur_atlas_timeout", default=5),
        )

    @api.model
    def _seur_atlas_log_request(self, seur_atlas_request: SeurAtlasRequest) -> None:
        """When debug is active requests/responses will be logged in ir.logging"""
        self.log_xml(seur_atlas_request.last_request, "seur_request")
        self.log_xml(seur_atlas_request.last_response, "seur_response")

    def seur_atlas_send_shipping(self, pickings) -> list:
        return [self.seur_atlas_create_shipping(p) for p in pickings]

    def _seur_atlas_zebra_label_custom(self, label: str) -> str:
        """Some printers might have special configurations so we could need
        to tweak the label in advance. For example, we could need to adjust
        initial position:
        label.replace("^LH105,40", "^LH50,0")
        """
        return label

    def _prepare_seur_atlas_shipping(self, picking):
        """The payload isn't compatible with the legacy API so a brand new method
        has to be made"""
        partner = picking.partner_id
        partner_country_code = partner.country_id.code or ""
        # SEUR oddity: Andorra is treated as domestic delivery
        if partner_country_code == "AD":
            partner_country_code = "ES"
        partner_name = partner.display_name
        # When we get a specific delivery address we want to prioritize its
        # name over the commercial one
        if partner.parent_id and partner.type == "delivery" and partner.name:
            partner_name = f"{partner.name} ({partner.commercial_partner_id.name})"
        partner_att = (
            partner.name if partner.parent_id and partner.type == "contact" else ""
        )
        company = picking.company_id
        phone = partner.phone and partner.phone.replace(" ", "") or ""
        mobile = partner.mobile and partner.mobile.replace(" ", "") or ""
        weight_by_parcel = picking.shipping_weight / (picking.number_of_packages or 1)
        return {
            "serviceCode": int(self.seur_atlas_service_code),
            "productCode": int(self.seur_atlas_product_code),
            # P: paid by the company, D: paid by the customer. There's no mechanism
            # to select this, but the most common scenario is that the company pays
            # for the delivery charging the customer in the invoice directly.
            "charges": "P",
            "reference": picking.name,
            "receiver": {
                "name": partner_name,
                "email": partner.email or "",
                "phone": phone or mobile,
                "contactName": partner_att,
                "address": {
                    "streetName": " ".join(
                        [s for s in [partner.street, partner.street2] if s]
                    ),
                    "cityName": partner.city,
                    "postalCode": partner.zip,
                    "country": partner_country_code,
                },
            },
            "sender": {
                "name": company.name,
                "email": company.email,
                "phone": company.phone,
                "accountNumber": self.seur_atlas_account_code,
                "contactName": company.name,
                "address": {
                    "streetName": " ".join(
                        [s for s in [company.street, company.street2] if s]
                    ),
                    "cityName": company.city,
                    "postalCode": company.zip,
                    "country": "ES",
                },
            },
            "comments": picking.note,
            # TODO: Implement packagings better
            "parcels": [
                {"weight": weight_by_parcel, "width": 1, "height": 1, "length": 1}
                for _ in range(picking.number_of_packages)
            ],
        }

    def seur_atlas_labels(self, code, seur_request: SeurAtlasRequest = None) -> bin:
        """Generate labels for the shipping code"""
        # Allow to reuse the request, like when we create the shipping
        if not seur_request:
            seur_request = self._seur_atlas_request()
        response = {}
        try:
            response = seur_request.labels(
                code=code,
                type=self.seur_atlas_label_format,
                entity="EXPEDITIONS",
                templateType=self.seur_atlas_label_template,
                outputType=self.seur_atlas_label_output_type,
                qr=self.seur_atlas_qr,
            )
        except Exception as e:
            raise (e)
        finally:
            self._seur_atlas_log_request(seur_request)
        return response

    def _seur_atlas_attach_labels(self, picking, datas: list):
        seur_label_format = "txt" if self.seur_atlas_label_format == "ZPL" else "pdf"
        for label_data in datas:
            label_content = label_data.get("label", label_data.get("pdf"))
            if seur_label_format == "txt":
                label_content = self._seur_atlas_zebra_label_custom(label_content)
                # SEUR sends the label in spanish format (^CI10) so we need
                # to encode the file in such ISO as well so special characters
                # print fine
                label_content = label_content.encode("iso-8859-15")
                label_content = base64.b64encode(label_content)
            filename = f"seur_{label_data['ecb']}.{seur_label_format}"
            self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "datas": label_content,
                    "store_fname": filename,
                    "res_model": picking._name,
                    "res_id": picking.id,
                    "mimetype": (
                        "text/plain"
                        if seur_label_format == "txt"
                        else "application/pdf"
                    ),
                }
            )

    def seur_atlas_create_shipping(self, picking):
        """Create a new shipping and download the proper labels"""
        self.ensure_one()
        payload = self._prepare_seur_atlas_shipping(picking)
        seur_request = self._seur_atlas_request()
        response = {}
        try:
            response = seur_request.shipments(payload=payload)
        except Exception as e:
            raise (e)
        finally:
            self._seur_atlas_log_request(seur_request)
        picking.carrier_tracking_ref = response["shipmentCode"]
        labels = self.seur_atlas_labels(picking.carrier_tracking_ref, seur_request)
        self._seur_atlas_attach_labels(picking, labels)
        response["tracking_number"] = picking.carrier_tracking_ref
        response["exact_price"] = 0
        return response

    @api.model
    def _seur_atlas_format_tracking(self, tracking):
        """Helper to forma tracking history strings

        :param dict tracking: SEUR tracking values
        :return str: Tracking line
        """
        return "{} - [{}] {}".format(
            fields.Datetime.to_string(isoparse(tracking["situationDate"])),
            tracking["eventCode"],
            tracking["description"],
        )

    def seur_atlas_tracking_state_update(self, picking):
        self.ensure_one()
        seur_request = self._seur_atlas_request()
        try:
            account_number, business_unit = self.seur_atlas_account_code.split("-")
            trackings = seur_request.tracking_services__extended(
                **{
                    "refType": "REFERENCE",
                    "ref": picking.name,
                    "idNumber": self.seur_atlas_vat,
                    "accountNumber": int(account_number),
                    "businessUnit": int(business_unit),
                }
            )
        except Exception as e:
            raise (e)
        finally:
            self._seur_atlas_log_request(seur_request)
        # We won't have tracking states when the shipping is just created
        if not trackings:
            return
        picking.tracking_state_history = "\n".join(
            [self._seur_atlas_format_tracking(tracking) for tracking in trackings]
        )
        current_tracking = trackings.pop()
        picking.tracking_state = self._seur_atlas_format_tracking(current_tracking)
        picking.delivery_state = TRACKING_STATES_MAP.get(
            current_tracking["eventCode"], "incidence"
        )

    def seur_atlas_cancel_shipment(self, pickings):
        """Cancel shippings for the picking"""
        seur_request = self._seur_atlas_request()
        for picking in pickings:
            seur_request.shipments__cancel(
                payload={"codes": [picking.carrier_tracking_ref]}
            )
        return True

    def seur_atlas_get_tracking_link(self, picking):
        return (
            f"https://www.seur.com/livetracking/"
            f"?segOnlineIdentificador={picking.carrier_tracking_ref}"
        )

    def seur_atlas_rate_shipment(self, order):
        """TODO: Implement rate shipments with ATLAS API"""
        raise NotImplementedError(_("To be implemented"))
