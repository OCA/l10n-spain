# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import _, exceptions, fields, models

from .seur_request import SeurRequest

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("seur", "Seur")],)
    seur_vat = fields.Char(
        string="VAT", default=lambda self: self.env.user.company_id.vat,
    )
    seur_franchise_code = fields.Char(string="Franchise Code",)
    seur_accounting_code = fields.Char(string="Accounting Code (CCC)",)
    seur_integration_code = fields.Char(string="Integration Code (CI)",)
    seur_cit_username = fields.Char(
        string="Username CIT",
        help="Used for cit.seur.com webservice (generate labels)",
    )
    seur_cit_password = fields.Char(
        sting="Password CIT", help="Used for cit.seur.com webservice (generate labels)",
    )
    seur_ws_username = fields.Char(
        string="Username WS", help="Used for ws.seur.com webservice (pickup services)",
    )
    seur_ws_password = fields.Char(
        string="Password WS", help="Used for ws.seur.com webservice (pickup services)",
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
        string="Send SMS to customer", help="This feature has delivery cost",
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
    seur_use_packages_from_picking = fields.Boolean(string="Use packages from picking")

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

    def seur_create_shipping(self, picking):
        self.ensure_one()
        seur_request = SeurRequest(self, picking)
        res = seur_request.create_shipping()
        # The error message could be more complex than a simple 'ERROR' sting.
        # For example, if there's wrong address info, it will return an
        # xml with the API error.
        error = res["mensaje"] == "ERROR" or not res.get("ECB", {}).get("string", [])
        if error:
            raise exceptions.UserError(_("SEUR exception: %s") % res["mensaje"])
        picking.carrier_tracking_ref = res["ECB"]["string"][0]
        if self.seur_label_format == "txt":
            label_content = self._zebra_label_custom(res["traza"])
            # SEUR sends the label in spanish format (^CI10) so we need
            # to encode the file in such ISO as well so special characters
            # print fine
            label_content = label_content.encode("iso-8859-15")
            label_content = base64.b64encode(label_content)
        else:
            label_content = res["PDF"]
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

    def seur_tracking_state_update(self, picking):
        self.ensure_one()
        if not self.seur_ws_username:
            picking.tracking_state_history = _(
                "Status cannot be checked, enter webservice carrier credentials"
            )
            return

        seur_request = SeurRequest(self, picking)
        res = seur_request.tracking_state_update()
        # We won't have tracking states when the shipping is just created
        if not res:
            return
        picking.tracking_state_history = res["tracking_state_history"]
        if "delivery_state" in res:
            picking.delivery_state = res["delivery_state"]

    def seur_cancel_shipment(self, pickings):
        for picking in pickings:
            seur_request = SeurRequest(self, picking)
            res = seur_request.cancel_shipment()
            if res["estado"] == "KO":
                raise UserWarning(
                    _("Cancel SEUR shipment (%s): %s")
                    % (picking.carrier_tracking_ref, res["mensaje"])
                )
        return True

    def seur_get_tracking_link(self, picking):
        return "https://www.seur.com/livetracking/?segOnlineIdentificador=%s" % (
            picking.carrier_tracking_ref
        )

    def seur_rate_shipment(self, order):
        """There's no public API so another price method should be used"""
        raise NotImplementedError(
            _(
                """
            SEUR API doesn't provide methods to compute delivery rates, so
            you should relay on another price method instead or override this
            one in your custom code.
        """
            )
        )
