# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from dateutil.parser import isoparse

from odoo import _, api, exceptions, fields, models

from .seur_master_data import TRACKING_STATES_MAP
from .seur_request import SeurRequest
from .seur_request_atlas import SeurAtlasRequest

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("seur", "Seur")], ondelete={"seur": "set default"}
    )
    seur_api = fields.Selection(
        selection=[("atlas", "Atlas"), ("legacy", "Legacy")],
        default="atlas",
    )
    seur_vat = fields.Char(
        string="VAT",
        default=lambda self: self.env.user.company_id.vat,
    )
    seur_franchise_code = fields.Char(
        string="Franchise Code",
    )
    seur_accounting_code = fields.Char(
        string="Accounting Code (CCC)",
    )
    seur_integration_code = fields.Char(
        string="Integration Code (CI)",
    )
    seur_cit_username = fields.Char(
        string="Username CIT",
        help="Used for cit.seur.com webservice (generate labels)",
    )
    seur_cit_password = fields.Char(
        string="Password CIT",
        help="Used for cit.seur.com webservice (generate labels)",
    )
    seur_ws_username = fields.Char(
        string="Username WS",
        help="Used for ws.seur.com webservice (pickup services)",
    )
    seur_ws_password = fields.Char(
        string="Password WS",
        help="Used for ws.seur.com webservice (pickup services)",
    )
    seur_service_code = fields.Selection(
        selection=[
            ("001", "SEUR - 24"),
            ("003", "SEUR - 10"),
            ("005", "MISMO DIA"),
            ("007", "COURIER"),
            ("009", "SEUR 13:30"),
            ("013", "SEUR - 72"),
            ("015", "S-48"),
            ("017", "MARITIMO"),
            ("019", "NETEXPRESS"),
            ("031", "ENTREGA PARTIC"),
            ("077", "CLASSIC"),
            ("083", "SEUR 8:30"),
        ],
        default="031",
        string="Service code",
    )
    seur_atlas_username = fields.Char()
    seur_atlas_password = fields.Char()
    seur_atlas_secret = fields.Char()
    seur_atlas_client = fields.Char()
    seur_product_code = fields.Selection(
        selection=[
            ("002", "ESTANDAR"),
            ("004", "MULTIPACK"),
            ("006", "MULTI BOX"),
            ("018", "FRIO"),
            ("048", "SEUR 24 PICKUP"),
            ("052", "MULTI DOC"),
            ("054", "DOCUMENTOS"),
            ("070", "INTERNACIONAL ´T"),
            ("072", "INTERNACIONAL A"),
            ("076", "CLASSIC"),
            ("086", "ECCOMMERCE RETURN 2HOME"),
            ("088", "ECCOMMERCE RETURN 2SHOP"),
            ("104", "CROSSBORDER NETEXPRES INTERNACIONAL"),
            ("108", "COURIER MUESTRAS"),
            ("116", "CLASSIC MULTIPARCEL"),
            ("118", "VINO"),
            ("122", "NEUMATICOS B2B"),
            ("124", "NEUMATICOS B2C"),
        ],
        default="002",
        string="Product code",
    )
    seur_send_sms = fields.Boolean(
        string="Send SMS to customer",
        help="This feature has delivery cost",
    )
    seur_label_format = fields.Selection(
        selection=[("pdf", "PDF"), ("txt", "TXT")],
        default="pdf",
        string="Label format",
    )
    seur_label_size = fields.Selection(
        selection=[("1D", "1D"), ("2D", "2D"), ("2C", "2C")],
        default="2C",
        string="Label size",
    )
    seur_atlas_label_format = fields.Selection(
        selection=[("PDF", "PDF"), ("ZPL", "ZPL"), ("A4_3", "Die-cut A4")],
        default="PDF",
    )
    seur_printer = fields.Selection(
        selection=[
            ("DATAMAX:E CLASS 4203", "DATAMAX E CLASS 4203"),
            ("HP:LASERJET II", "HP LASERJET II"),
            ("INTERMEC:C4", "INTERMEC C4"),
            ("TEC:B430", "TEC B430"),
            ("ZEBRA:LP2844-Z", "ZEBRA LP2844-Z"),
            ("ZEBRA:S600", "ZEBRA S600"),
            ("ZEBRA:Z4M PLUS", "ZEBRA Z4M PLUS"),
        ],
        string="Printer",
        default="ZEBRA:LP2844-Z",
    )

    def _seur_atlas_request(self):
        """Get the credentials for SEUR ATLAS API

        :return SeurAtlasRequest: SEUR Atlas Request object
        """
        return SeurAtlasRequest(
            user=self.seur_atlas_username,
            password=self.seur_atlas_password,
            secret=self.seur_atlas_secret,
            client_id=self.seur_atlas_client,
            acc_number=self.seur_accounting_code,
            id_number=self.seur_vat,
        )

    @api.model
    def _seur_atlas_log_request(self, seur_atlas_request):
        """When debug is active requests/responses will be logged in ir.logging

        :param seur_atlas_request seur_atlas_request: ATLAS Express request object
        """
        self.log_xml(seur_atlas_request.last_request, "seur_request")
        self.log_xml(seur_atlas_request.last_response, "seur_response")

    def seur_test_connection(self):
        self.ensure_one()
        seur_request = SeurRequest(self, self)
        res = seur_request.test_connection()
        return res and res["mensaje"] == "ERROR"

    def seur_send_shipping(self, pickings):
        return [self.seur_create_shipping(p) for p in pickings]

    def _zebra_label_custom(self, label):
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
        partner_name = partner.display_name
        # When we get a specific delivery address we want to prioritize its
        # name over the commercial one
        if partner.parent_id and partner.type == "delivery" and partner.name:
            partner_name = "{} ({})".format(
                partner.name, partner.commercial_partner_id.name
            )
        partner_att = (
            partner.name if partner.parent_id and partner.type == "contact" else ""
        )
        company = picking.company_id
        phone = partner.phone and partner.phone.replace(" ", "") or ""
        mobile = partner.mobile and partner.mobile.replace(" ", "") or ""
        weight = picking.shipping_weight
        return {
            "serviceCode": int(self.seur_service_code),
            "productCode": int(self.seur_product_code),
            "charges": "P",  # ??
            "reference": f"picking.name-{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}",
            "receiver": {
                "name": partner_name,
                "email": partner.email,
                "phone": phone or mobile,
                "contactName": partner_att,
                "address": {
                    "streetName": " ".join(
                        [s for s in [partner.street, partner.street2] if s]
                    ),
                    "cityName": partner.city,
                    "postalCode": partner.zip,
                    "country": (partner.country_id and partner.country_id.code or ""),
                },
            },
            "sender": {
                "name": company.name,
                "email": company.email,
                "phone": company.phone,
                "accountNumber": self.seur_accounting_code,
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
            "parcels": [{"weight": weight, "width": 1, "height": 1, "length": 1}],
        }

    def seur_atlas_labels(self, code, seur_request=None):
        """"""
        # Allow to reuse the request, like when we create the shipping
        if not seur_request:
            seur_request = self._seur_atlas_request()
        response = {}
        try:
            response = seur_request.labels(code=code)
        except Exception as e:
            raise (e)
        finally:
            self._seur_atlas_log_request(seur_request)
        return response

    def seur_atlas_create_shipping(self, picking):
        """"""
        payload = self._prepare_seur_atlas_shipping(picking)
        seur_request = self._seur_atlas_request()
        response = {}
        try:
            response = seur_request.shipments(payload=payload)
        except Exception as e:
            raise (e)
        finally:
            self._seur_atlas_log_request(seur_request)
        return response

    def seur_legacy_create_shipping(self, picking):
        """Use legacy"""
        seur_request = SeurRequest(self, picking)
        res = seur_request.create_shipping()
        # The error message could be more complex than a simple 'ERROR' string.
        # For example, if there's wrong address info, it will return an
        # xml with the API error.
        error = res["mensaje"] == "ERROR" or not res.get("ECB", {}).get("string", [])
        if error:
            raise exceptions.UserError(_("SEUR exception: %s") % res["mensaje"])
        return {
            "shipmentCode": res["ECB"]["string"][0],
            "label": (
                res.get("traza") if self.seur_label_format == "txt" else res.get("PDF")
            ),
        }

    def seur_create_shipping(self, picking):
        self.ensure_one()
        res = getattr(self, f"seur_{self.seur_api}_create_shipping")(picking)
        picking.carrier_tracking_ref = res["shipmentCode"]
        if self.seur_label_format == "txt":
            label_content = self._zebra_label_custom(res["zebra_label"])
            # SEUR sends the label in spanish format (^CI10) so we need
            # to encode the file in such ISO as well so special characters
            # print fine
            label_content = label_content.encode("iso-8859-15")
            label_content = base64.b64encode(label_content)
        else:
            label_content = res["pdf_label"]
        filename = "seur_{}.{}".format(
            picking.carrier_tracking_ref, self.seur_label_format
        )
        self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": label_content,
                "store_fname": filename,
                "res_model": "stock.picking",
                "res_id": picking.id,
                "mimetype": (
                    "application/pdf"
                    if self.seur_label_format == "pdf"
                    else "text/plain"
                ),
            }
        )
        res["tracking_number"] = picking.carrier_tracking_ref
        res["exact_price"] = 0
        return res

    @api.model
    def _seur_format_tracking(self, tracking):
        """Helper to forma tracking history strings

        :param dict tracking: SEUR tracking values
        :return str: Tracking line
        """
        return "{} - [{}] {}".format(
            fields.Datetime.to_string(isoparse(tracking["situationDate"])),
            tracking["eventCode"],
            tracking["description"],
        )

    def seur_tracking_state_update(self, picking):
        self.ensure_one()
        if self.seur_api == "legacy":
            picking.tracking_state_history = _(
                "Status cannot be checked, enter webservice carrier credentials"
            )
            return
        seur_request = self._seur_atlas_request()
        try:
            trackings = seur_request.tracking_services__extended(
                **{"refType": "REFERENCE", "ref": picking.name}
            )
        except Exception as e:
            raise (e)
        finally:
            self._seur_atlas_log_request(seur_request)
        # We won't have tracking states when the shipping is just created
        if not trackings:
            return
        picking.tracking_state_history = "\n".join(
            [self._seur_format_tracking(tracking) for tracking in trackings]
        )
        current_tracking = trackings.pop()
        picking.tracking_state = self._seur_format_tracking(current_tracking)
        picking.delivery_state = TRACKING_STATES_MAP.get(
            current_tracking["eventCode"], "incidence"
        )

    def seur_cancel_shipment(self, pickings):
        for picking in pickings:
            seur_request = SeurRequest(self, picking)
            res = seur_request.cancel_shipment()
            if res["estado"] == "KO":
                raise UserWarning(
                    _("Cancel SEUR shipment (%(ref)s): %(message)s")
                    % ({"ref": picking.carrier_tracking_ref, "message": res["mensaje"]})
                )
        return True

    def seur_get_tracking_link(self, picking):
        return "https://www.seur.com/livetracking/?segOnlineIdentificador=%s" % (
            picking.carrier_tracking_ref
        )

    def seur_rate_shipment(self, order):
        """TODO: Implement rate shipments with ATLAS API"""
        raise NotImplementedError(
            _(
                """
            SEUR API doesn't provide methods to compute delivery rates, so
            you should relay on another price method instead or override this
            one in your custom code.
        """
            )
        )
