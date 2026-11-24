# Copyright 2020 Tecnativa - David Vidal
# Copyright 2026 PYMING - Extreme Micro S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import binascii
import logging
import unicodedata
from xml.sax.saxutils import escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .gls_asm_master_data import (
    GLS_ASM_SERVICES,
    GLS_DELIVERY_STATES_STATIC,
    GLS_PICKUP_STATES_STATIC,
    GLS_PICKUP_TYPE_STATES,
    GLS_POSTAGE_TYPE,
    GLS_SHIPMENT_TYPE_STATES,
    GLS_SHIPPING_TIMES,
    GLS_TRACKING_LINKS,
)
from .gls_asm_request import GlsAsmApiError, GlsAsmRequest

_logger = logging.getLogger(__name__)

# GrabaServicios codes meaning that our customer reference is already recorded.
GLS_DUPLICATE_REFERENCE_CODES = (-70, -118)
# GetExpCli states of a cancelled expedition. "borrado" is NOT a cancellation.
GLS_CANCELLED_STATES = ("5", "51")
# Degree and ordinal indicators that GLS drops from addresses ("5°A" -> "5A").
GLS_NUMBER_MARKERS = str.maketrans("", "", "\u00b0\u00ba\u00aa")


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("gls_asm", "GLS ASM")], ondelete={"gls_asm": "set default"}
    )
    gls_asm_uid = fields.Char(string="GLS UID")
    gls_asm_service = fields.Selection(
        selection=GLS_ASM_SERVICES,
        string="GLS Service",
        help="Set the contracted GLS Service",
        default="1",  # Courier
    )
    gls_asm_shiptime = fields.Selection(
        selection=GLS_SHIPPING_TIMES,
        string="Shipping Time",
        help="Set the desired GLS shipping time for this carrier",
        default="0",  # 10h
    )
    gls_asm_postage_type = fields.Selection(
        selection=GLS_POSTAGE_TYPE,
        string="Postage Type",
        help="Postage type, usually 'Prepaid'",
        default="P",
    )
    gls_is_pickup_service = fields.Boolean(
        string="Pick-up service",
        help="Checked if this service is used for pickups",
        compute="_compute_gls_pickup_service",
    )
    gls_asm_cash_on_delivery = fields.Boolean(
        string="Cash on delivery",
        help=(
            "If checked, it means that the carrier is paid with cash. It assumes "
            "there is a sale order linked and it will use that "
            "total amount as the value to be paid"
        ),
    )
    gls_asm_with_return = fields.Boolean(
        string="GLS/ASM With return",
        help=(
            "Check this field to mark the delivery as 'With return'. This means that "
            "the customer receiving the delivery also has a package to return."
        ),
    )

    @api.depends("gls_asm_service")
    def _compute_gls_pickup_service(self):
        for carrier in self:
            carrier.gls_is_pickup_service = carrier.gls_asm_service in [
                "7",  # RECOGIDA
                "8",  # RECOGIDA CRUZADA
                "17",  # RECOGIDA SIN MERCANCIA
                "39",  # REC. INT
                "45",  # RECOGIDA MEN. MOTO
                "46",  # RECOGIDA MEN. FURGONETA
                "47",  # RECOGIDA MEN. F. GRANDE
                "48",  # RECGOIDA CAMIÓN
                "49",  # RECOGIDA MENSAJERO
                "51",  # REC. INT WW
                "56",  # RECOGIDA ECONOMY
                "57",  # REC. INTERCIUDAD ECONOMY
            ]

    def _gls_asm_uid(self):
        """The carrier can be put in test mode. The tests user must be set.
        A default given by GLS is put in the config parameter data"""
        self.ensure_one()
        uid = (
            self.gls_asm_uid
            if self.prod_environment
            else self.env["ir.config_parameter"]
            .sudo()
            .get_param("delivery_gls_asm.api_user_demo", "")
        )
        return uid

    def gls_asm_get_tracking_link(self, picking):
        """Provide tracking link for the customer"""
        # International
        if picking.gls_asm_picking_ref:
            if picking.partner_id.country_id.code == "PT":
                base_link = GLS_TRACKING_LINKS.get("INT_PT")
            else:
                base_link = GLS_TRACKING_LINKS.get("INT")
            tracking_url = base_link.format(picking.gls_asm_picking_ref)
        else:
            tracking_url = GLS_TRACKING_LINKS.get("ASM").format(
                picking.carrier_tracking_ref, picking.partner_id.zip
            )
        return tracking_url

    def _prepare_gls_asm_shipping(self, picking):
        """Convert picking values for asm api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        # A picking can be delivered from any warehouse
        sender_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        consignee = picking.partner_id
        consignee_entity = picking.partner_id.commercial_partner_id
        if not sender_partner.street:
            raise UserError(_("Couldn't find the sender street"))
        cash_amount = 0
        if self.gls_asm_cash_on_delivery:
            cash_amount = picking.sale_id.amount_total
        return {
            "fecha": fields.Date.today().strftime("%d/%m/%Y"),
            "portes": self.gls_asm_postage_type,
            "servicio": self.gls_asm_service,
            "horario": self.gls_asm_shiptime,
            "bultos": picking.number_of_packages,
            "peso": round(picking.shipping_weight, 3),
            "volumen": "",  # [optional] Volume, in m3
            "declarado": "",  # [optional]
            "dninomb": "0",  # [optional]
            "fechaentrega": "",  # [optional]
            "retorno": "1" if self.gls_asm_with_return else "0",  # [optional]
            "pod": "N",  # [optional]
            "podobligatorio": "N",  # [deprecated]
            "remite_plaza": "",  # [optional] Origin agency
            "remite_nombre": escape(
                sender_partner.name or sender_partner.parent_id.name
            ),
            "remite_direccion": escape(sender_partner.street or ""),
            "remite_poblacion": escape(sender_partner.city or ""),
            "remite_provincia": escape(sender_partner.state_id.name or ""),
            "remite_pais": "34",  # [mandatory] always 34=Spain
            "remite_cp": sender_partner.zip or "",
            "remite_telefono": sender_partner.phone or "",
            "remite_movil": sender_partner.mobile or "",
            "remite_email": escape(sender_partner.email or ""),
            "remite_departamento": "",
            "remite_nif": sender_partner.vat or "",
            "remite_observaciones": "",
            "destinatario_codigo": "",
            "destinatario_plaza": "",
            "destinatario_nombre": (
                escape(consignee.name or consignee.commercial_partner_id.name or "")
            ),
            "destinatario_direccion": escape(consignee.street or ""),
            "destinatario_poblacion": escape(consignee.city or ""),
            "destinatario_provincia": escape(consignee.state_id.name or ""),
            "destinatario_pais": consignee.country_id.code or "",
            "destinatario_cp": consignee.zip,
            # For certain destinations the consignee mobile and email are required to
            # make the expedition. Try to fallback to the commercial entity one
            "destinatario_telefono": consignee.phone or consignee_entity.phone or "",
            "destinatario_movil": consignee.mobile or consignee_entity.mobile or "",
            "destinatario_email": escape(
                consignee.email or consignee_entity.email or ""
            ),
            "destinatario_observaciones": picking.gls_shipping_notes or "",
            "destinatario_att": "",
            "destinatario_departamento": "",
            "destinatario_nif": "",
            "referencia_c": escape(
                picking.name.replace("\\", "/")  # It errors with \ characters
            ),  # Our unique reference
            "referencia_0": "",  # Not used if the above is set
            "importes_debido": "0",  # The customer pays the shipping
            "importes_reembolso": cash_amount or "",
            "seguro": "0",  # [optional]
            "seguro_descripcion": "",  # [optional]
            "seguro_importe": "",  # [optional]
            "etiqueta": "PDF",  # Get Label in response
            "etiqueta_devolucion": "PDF",
            # [optional] GLS Customer Code
            # (when customer have several codes in GLS)
            "cliente_codigo": "",
            "cliente_plaza": "",
            "cliente_agente": "",
        }

    def _prepare_gls_asm_pickup(self, picking):
        """Convert picking values for asm api pickup
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        sender_partner = picking.partner_id
        receiving_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        if not sender_partner.street:
            raise UserError(_("Couldn't find the sender street"))
        if not receiving_partner.street:
            raise UserError(_("Couldn't find the consignee street"))
        return {
            "fecha": fields.Date.today().strftime("%d/%m/%Y"),
            "portes": self.gls_asm_postage_type,
            "servicio": self.gls_asm_service,
            "horario": self.gls_asm_shiptime,
            "bultos": picking.number_of_packages,
            "peso": round(picking.shipping_weight, 3),
            "fechaentrega": "",  # [optional]
            "observaciones": "",  # [optional]
            "remite_nombre": escape(
                sender_partner.name or sender_partner.parent_id.name
            ),
            "remite_direccion": escape(sender_partner.street) or "",
            "remite_poblacion": sender_partner.city or "",
            "remite_provincia": sender_partner.state_id.name or "",
            "remite_pais": (sender_partner.country_id.phone_code or ""),
            "remite_cp": sender_partner.zip or "",
            "remite_telefono": (
                sender_partner.phone or sender_partner.parent_id.phone or ""
            ),
            "remite_movil": (
                sender_partner.mobile or sender_partner.parent_id.mobile or ""
            ),
            "remite_email": (
                sender_partner.email or sender_partner.parent_id.email or ""
            ),
            "destinatario_nombre": escape(
                receiving_partner.name or receiving_partner.parent_id.name
            ),
            "destinatario_direccion": escape(receiving_partner.street) or "",
            "destinatario_poblacion": receiving_partner.city or "",
            "destinatario_provincia": receiving_partner.state_id.name or "",
            "destinatario_pais": (receiving_partner.country_id.code or ""),
            "destinatario_cp": receiving_partner.zip or "",
            "destinatario_telefono": (
                receiving_partner.phone or receiving_partner.parent_id.phone or ""
            ),
            "destinatario_movil": (
                receiving_partner.mobile or receiving_partner.parent_id.mobile or ""
            ),
            "destinatario_email": (
                receiving_partner.email or receiving_partner.parent_id.email or ""
            ),
            "referencia_c": escape(picking.name),  # Our unique reference
            "referencia_a": "",  # Not used if the above is set
        }

    def gls_asm_send_shipping(self, pickings):
        """Send the package to GLS
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        gls_request = GlsAsmRequest(self._gls_asm_uid())
        result = []
        for picking in pickings:
            if picking.carrier_id.gls_is_pickup_service:
                continue
            vals = self._prepare_gls_asm_shipping(picking)
            if len(vals.get("referencia_c", "")) > 15:
                raise UserError(
                    _(
                        "GLS-ASM API doesn't admit a reference number higher than "
                        "15 characters. In order to handle it, they trim the"
                        "reference and as the reference is unique to every "
                        "customer we soon would have duplicated reference "
                        "collisions. To prevent this, you should edit your picking "
                        "sequence to a max of 15 characters."
                    )
                )
            vals.update({"tracking_number": False, "exact_price": 0})
            # Surface pending database conflicts before the external write.
            self.env.flush_all()
            try:
                response = gls_request._send_shipping(vals)
            except GlsAsmApiError as error:
                if error.code not in GLS_DUPLICATE_REFERENCE_CODES:
                    raise
                # GLS bookings survive Odoo rollbacks. Recover only when GLS
                # explicitly rejects this booking as a duplicate reference.
                response = self._gls_asm_recover_shipping(gls_request, picking, vals)
                if not response:
                    raise
            self.log_xml(
                response and response.get("gls_sent_xml", ""),
                "GLS ASM Shipping Request",
            )
            self.log_xml(response or "", "GLS ASM Shipping Response")
            if not response or response.get("_return", -1) < 0:
                result.append(vals)
                continue
            # For compatibility we provide this number although we get
            # two more codes: codbarras and uid
            vals["tracking_number"] = response.get("_codexp")
            gls_asm_picking_ref = ""
            try:
                references = response.get("Referencias", {}).get("Referencia", [])
                for ref in references:
                    if ref.get("_tipo", "") == "N":
                        gls_asm_picking_ref = ref.get("value", "")
                        break
            except Exception as e:
                _logger.warning(e)
            picking.write(
                {
                    "gls_asm_public_tracking_ref": response.get("_codbarras"),
                    "gls_asm_picking_ref": gls_asm_picking_ref,
                }
            )
            # We post an extra message in the chatter with the barcode and the
            # label because there's clean way to override the one sent by core.
            body = _("GLS Shipping extra info:\n" "barcode: %s") % response.get(
                "_codbarras"
            )
            if response.get("gls_recovered"):
                body += "\n" + _(
                    "Recovered existing GLS shipment %(exp)s recorded for "
                    "reference %(ref)s: no new shipment was recorded.",
                    exp=response.get("_codexp"),
                    ref=response.get("gls_reference"),
                )
            attachment = []
            if response.get("gls_label"):
                attachment = [
                    (
                        "gls_label_{}.pdf".format(response.get("_codbarras")),
                        response.get("gls_label"),
                    )
                ]
            picking.message_post(body=body, attachments=attachment)
            result.append(vals)
        return result

    @api.model
    def _gls_asm_normalize_text(self, value):
        """Compare GLS texts ignoring case, accents, punctuation and spacing.

        GLS rewrites some characters (e.g. ``'`` becomes ``´``) and drops
        number markers (``5°A`` becomes ``5A``). Number markers are removed
        before NFKD, which would turn ``º``/``ª`` into letters. Any other
        character that is not a letter or digit becomes a separator, so words
        and numbers never merge (``12-14`` differs from ``1214``).
        """
        text = str(value or "").translate(GLS_NUMBER_MARKERS)
        text = unicodedata.normalize("NFKD", text)
        text = "".join(
            char if char.isalnum() else " "
            for char in text
            if not unicodedata.combining(char)
        )
        return " ".join(text.casefold().split())

    def _gls_asm_shipment_mismatches(self, picking, vals, expedition):
        """Return the reasons why an existing GLS expedition is not ours."""
        self.ensure_one()
        consignee = picking.partner_id
        reference = picking.name.replace("\\", "/")
        required = (
            "refC",
            "codexp",
            "codbar",
            "codestado",
            "codServicio",
            "codHorario",
            "tipo_portes",
            "bultos",
            "cp_dst",
            "codpais_dst",
            "nombre_dst",
            "calle_dst",
            "localidad_dst",
        )
        if any(
            not isinstance(expedition.get(key), str | int)
            or isinstance(expedition.get(key), bool)
            for key in required
        ):
            return [_("missing or malformed shipment details")]

        def value(key):
            return str(expedition.get(key) or "").strip()

        mismatches = []
        # GetExpCli's international-reference mapping has not been verified.
        # Without it native tracking would incorrectly use the domestic link.
        if consignee.country_id.code != "ES":
            mismatches.append(_("international tracking cannot be verified"))
        if value("refC") != reference:
            mismatches.append(_("reference %s", value("refC")))
        if not value("codexp") or not value("codbar"):
            mismatches.append(_("missing expedition number or barcode"))
        if value("codestado") not in GLS_SHIPMENT_TYPE_STATES:
            mismatches.append(_("missing or unknown shipment state"))
        for key, ours, label in (
            ("codServicio", vals["servicio"], _("service")),
            ("codHorario", vals["horario"], _("shipping time")),
            ("tipo_portes", vals["portes"], _("postage type")),
            ("cp_dst", vals["destinatario_cp"], _("destination zip")),
            ("codpais_dst", consignee.country_id.phone_code, _("destination country")),
        ):
            if value(key) != str(ours or "").strip():
                mismatches.append(f"{label} {value(key)}")
        try:
            parcels = int(value("bultos"))
        except ValueError:
            parcels = None
        if parcels != int(vals["bultos"] or 0):
            mismatches.append(_("parcels %s", value("bultos")))
        for key, ours, label in (
            (
                "nombre_dst",
                consignee.name or consignee.commercial_partner_id.name,
                _("consignee"),
            ),
            ("calle_dst", consignee.street, _("destination street")),
            ("localidad_dst", consignee.city, _("destination city")),
        ):
            theirs = value(key)
            if not theirs or self._gls_asm_normalize_text(ours) != (
                self._gls_asm_normalize_text(theirs)
            ):
                mismatches.append(f"{label} {theirs}")
        # GetExpCli's verified schema does not expose these booking options:
        # never invent field names or assume a match for an existing shipment.
        if self.gls_asm_cash_on_delivery:
            mismatches.append(_("cash on delivery cannot be verified"))
        if vals.get("retorno") == "1" or self.gls_asm_service == "58":
            mismatches.append(_("return service cannot be verified"))
        if self.gls_asm_shiptime == "19" or vals.get("destinatario_codigo"):
            mismatches.append(_("ParcelShop code cannot be verified"))
        return mismatches

    def _gls_asm_recover_shipping(self, gls_request, picking, vals):
        """Recover this picking after GLS rejects a booking as a duplicate.

        :returns: a GrabaServicios-like response dict, or ``False`` when GLS
            explicitly reports that the reference does not exist, leaving the
            caller to propagate the original duplicate error (never to rebook)
        :raises UserError: when the lookup is inconclusive or the existing
            expedition cannot be safely reused
        """
        self.ensure_one()
        reference = picking.name.replace("\\", "/")
        expeditions = gls_request._find_shipments(reference)
        if not expeditions:
            # The rejected booking is still unresolved, with or without local
            # links. Preserve them and let the caller re-raise the duplicate.
            return False
        if len(expeditions) > 1:
            raise UserError(
                _(
                    "GLS already has %(count)s shipments for reference %(ref)s. "
                    "Link the right one manually; no new shipment was recorded.",
                    count=len(expeditions),
                    ref=reference,
                )
            )
        expedition = expeditions[0]
        if str(expedition.get("codestado") or "").strip() in GLS_CANCELLED_STATES:
            raise UserError(
                _(
                    "The existing GLS shipment for %(ref)s is cancelled. "
                    "Review the cancellation with GLS before arranging a replacement "
                    "using a new picking; no new shipment was recorded.",
                    ref=reference,
                )
            )
        # Never replace local links with a different expedition, append a new
        # tracking number, or clear an international reference we cannot verify.
        for local, remote, field in (
            (
                picking.carrier_tracking_ref,
                str(expedition.get("codexp") or "").strip(),
                _("local tracking number"),
            ),
            (
                picking.gls_asm_public_tracking_ref,
                str(expedition.get("codbar") or "").strip(),
                _("local GLS barcode"),
            ),
        ):
            if local and local != remote:
                raise UserError(
                    _(
                        "The %(field)s conflicts with the existing GLS shipment "
                        "for %(ref)s. Review it with GLS; local references were "
                        "not changed and no new shipment was recorded.",
                        field=field,
                        ref=reference,
                    )
                )
        if picking.gls_asm_picking_ref:
            raise UserError(
                _(
                    "The existing local international reference for %(ref)s "
                    "cannot be verified. Review it with GLS; local references "
                    "were not changed and no new shipment was recorded.",
                    ref=reference,
                )
            )
        mismatches = self._gls_asm_shipment_mismatches(picking, vals, expedition)
        if mismatches:
            raise UserError(
                _(
                    "GLS already has shipment %(exp)s for reference %(ref)s, but "
                    "it does not match this picking (%(reasons)s). Review it in "
                    "GLS; no new shipment was recorded.",
                    exp=expedition.get("codexp") or "",
                    ref=reference,
                    reasons=", ".join(mismatches),
                )
            )
        barcode = str(expedition["codbar"]).strip()
        try:
            label = gls_request._shipping_label(barcode)
        except (binascii.Error, ValueError):
            # Invalid base64 is a recoverable label error, never a reason to book.
            label = False
        if not label or not label.startswith(b"%PDF-"):
            raise UserError(
                _(
                    "GLS returned a missing or invalid PDF for existing shipment "
                    "%(exp)s. "
                    "Retry label recovery; no new shipment was recorded.",
                    exp=expedition["codexp"],
                )
            )
        _logger.info(
            "Recovered existing GLS shipment %s for picking %s",
            expedition["codexp"],
            picking.id,
        )
        return {
            "_return": 0,
            "_codexp": str(expedition["codexp"]).strip(),
            "_codbarras": barcode,
            "Referencias": {"Referencia": []},
            "gls_label": label,
            "gls_recovered": True,
            "gls_reference": reference,
            "gls_sent_xml": "",
        }

    def gls_asm_send_pickup(self, pickings):
        """Send the request to GLS to pick a package up
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        gls_request = GlsAsmRequest(self._gls_asm_uid())
        result = []
        for picking in pickings:
            if not picking.carrier_id.gls_is_pickup_service:
                continue
            vals = self._prepare_gls_asm_pickup(picking)
            vals.update({"tracking_number": False, "exact_price": 0})
            response = gls_request._send_pickup(vals)
            self.log_xml(
                response and response.get("gls_sent_xml", ""), "GLS ASM Pick-up Request"
            )
            self.log_xml(response or "", "GLS ASM Pick-up Response")
            if not response or response.get("_return", -1) < 0:
                result.append(vals)
                continue
            # For compatibility we provide this number although we get
            # two more codes: codbarras and uid
            vals["tracking_number"] = response.get("_codigo")
            picking.gls_asm_public_tracking_ref = response.get("_codigo")
            # We post an extra message in the chatter with the barcode and the
            # label because there's clean way to override the one sent by core.
            body = _(
                "GLS Pickup extra info:<br/> "
                "Tracking number: %(codigo)s<br/> Bultos: %(bultos)s",
            ) % {"codigo": response.get("_codigo"), "bultos": vals["bultos"]}
            picking.message_post(body=body)
            result.append(vals)
        return result

    def gls_asm_tracking_state_update(self, picking):
        """Tracking state update"""
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        gls_request = GlsAsmRequest(self._gls_asm_uid())
        tracking_info = {}
        if not picking.carrier_id.gls_is_pickup_service:
            tracking_info = gls_request._get_tracking_states(
                picking.carrier_tracking_ref
            )
            tracking_states = tracking_info.get("tracking_list", {}).get("tracking", [])
            # If there's just one state, we'll get a single dict, otherwise we
            # get a list of dicts
            if isinstance(tracking_states, dict):
                tracking_states = [tracking_states]
        else:
            tracking_states = gls_request._get_pickup_tracking_states(
                picking.carrier_tracking_ref
            )
        if not tracking_states:
            return
        self.log_xml(tracking_states or "", "GLS ASM Tracking Response")
        picking.tracking_state_history = "\n".join(
            [
                "{} - [{}] {}".format(
                    t.get("fecha") or "{} {}".format(t.get("Fecha"), t.get("Hora")),
                    t.get("codigo") or t.get("Codigo"),
                    t.get("evento") or t.get("Descripcion"),
                )
                for t in tracking_states
            ]
        )
        tracking = tracking_states.pop()
        picking.tracking_state = "[{}] {}".format(
            tracking_info.get("codestado") or tracking.get("Codigo"),
            tracking_info.get("estado") or tracking.get("Descripcion"),
        )
        if not picking.carrier_id.gls_is_pickup_service:
            states_to_check = GLS_DELIVERY_STATES_STATIC
            picking.gls_shipment_state = GLS_SHIPMENT_TYPE_STATES.get(
                tracking_info.get("codestado"), "incidence"
            )
        else:
            states_to_check = GLS_PICKUP_STATES_STATIC
            # Portuguese pick-ups use the 0 code for extra states that aren't "Canceled"
            # In order to not incorrectly mark as canceled, we take the most recent
            # non-0 code (that isn't "Cancel") as the current state
            if (
                picking.partner_id.country_id.code == "PT"
                and "Anulada" not in tracking.get("Descripcion")
            ):
                tracking = list(
                    filter(lambda t: t["Codigo"] != "0", tracking_states)
                ).pop()
            picking.gls_pickup_state = GLS_PICKUP_TYPE_STATES.get(
                tracking.get("Codigo"), "incidence"
            )
        delivery_state = states_to_check.get(
            tracking_info.get("codestado") or tracking.get("Codigo"), "incidence"
        )
        if delivery_state == "incidence":
            delivery_state = "incident"
        picking.delivery_state = delivery_state

    def gls_asm_cancel_shipment(self, pickings):
        """Cancel the expedition"""
        gls_request = GlsAsmRequest(self._gls_asm_uid())
        for picking in pickings.filtered("carrier_tracking_ref"):
            self.gls_asm_tracking_state_update(picking=picking)
            if picking.delivery_state != "shipping_recorded_in_carrier":
                raise UserError(
                    _(
                        "Unable to cancel GLS Expedition with reference "
                        "%(ref)s as it is in state %(state)s.\n"
                        "Please manage the cancellation of this "
                        "shipment/pickup with GLS via email."
                    )
                    % {
                        "ref": picking.carrier_tracking_ref,
                        "state": picking.tracking_state,
                    }
                )
            if picking.carrier_id.gls_is_pickup_service:
                response = gls_request._cancel_pickup(picking.carrier_tracking_ref)
            else:
                response = gls_request._cancel_shipment(picking.carrier_tracking_ref)
            self.log_xml(
                response and response.get("gls_sent_xml", ""), "GLS ASM Cancel Request"
            )
            self.log_xml(response or "", "GLS ASM Cancel Response")
            if not response or response.get("_return") < 0:
                msg = _("GLS Cancellation failed with reason: %s") % response.get(
                    "value", "Connection Error"
                )
                picking.message_post(body=msg)
                continue
            picking.write(
                {"gls_asm_public_tracking_ref": False, "gls_asm_picking_ref": False}
            )
            self.gls_asm_tracking_state_update(picking=picking)

    def gls_asm_rate_shipment(self, order):
        """There's no public API so another price method should be used
        Not implemented with GLS-ASM, these values are so it works with websites"""
        return {
            "success": True,
            "price": self.product_id.lst_price,
            "error_message": _(
                """GLS ASM API doesn't provide methods to compute delivery rates, so
                you should relay on another price method instead or override this
                one in your custom code."""
            ),
            "warning_message": _(
                """GLS ASM API doesn't provide methods to compute delivery rates, so
                you should relay on another price method instead or override this
                one in your custom code."""
            ),
        }

    def gls_asm_get_label(self, gls_asm_public_tracking_ref):
        """Generate label for picking
        :param picking - stock.picking record
        :returns pdf file
        """
        self.ensure_one()
        if not gls_asm_public_tracking_ref:
            return False
        gls_request = GlsAsmRequest(self._gls_asm_uid())
        label = gls_request._shipping_label(gls_asm_public_tracking_ref)
        if not label:
            return False
        return label

    def action_get_manifest(self):
        """Action to launch the manifest wizard"""
        self.ensure_one()
        wizard = self.env["gls.asm.minifest.wizard"].create({"carrier_id": self.id})
        view_id = self.env.ref("delivery_gls_asm.delivery_manifest_wizard_form").id
        return {
            "name": _("GLS Manifest"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "gls.asm.minifest.wizard",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "target": "new",
            "res_id": wizard.id,
            "context": self.env.context,
        }
