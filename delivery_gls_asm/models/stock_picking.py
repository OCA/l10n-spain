# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # ASM API has two references for each delivery. This one is needed
    # for some operations like getting the label
    gls_asm_public_tracking_ref = fields.Char(
        string="GLS Barcode", readonly=True, copy=False
    )
    gls_carrier_is_pickup_service = fields.Boolean(
        related="carrier_id.gls_is_pickup_service"
    )
    gls_pickup_state = fields.Selection(
        string="Estado recogida GLS",
        selection=[
            ("recorded", "Solicitada"),
            ("received", "Recibida"),
            ("assigned", "Asignada"),
            ("picked_up_customer", "Recogido en Cliente"),
            ("picked_up_agency", "Recepcionada en Agencia"),
            ("done", "Realizada con éxito"),
            ("not_done", "No Realizada"),
            ("incidence", "Realizada con Incidencia"),
            ("cancel", "Anulada"),
            ("preconfirm", "A preconfirmar"),
            ("pending", "Pendiente Gestión"),
            ("closed", "Cerrado"),
            ("pending_auth", "Pending Autorización"),
            ("closed_final", "Cerrado Definitivo"),
        ],
        copy=False,
    )
    gls_shipment_state = fields.Selection(
        string="Estado envío GLS",
        selection=[
            ("recorded", "Grabado"),
            ("manifested", "Manifestada"),
            ("transit", "En tránsito al destino"),
            ("agency_transit", "En delegación destino"),
            ("closed", "Cerrado por siniestro"),
            ("cancel", "Anualada"),
            ("shipping", "En reparto"),
            ("delivered", "Entregado"),
            ("partially_delivered", "Entrega parcial"),
            ("warehouse", "Almacenado"),
            ("return_agency", "Devuelta"),
            ("pending", "Pendiente datos en delegación"),
            ("held", "Pendiente autorización"),
            ("incidence", "Con incidencia"),
            ("closed_final", "Cerrado definitivo"),
            ("preconfirmed", "Preconfirmada enrega"),
            ("cancel_returned", "Entrega anulada (devuelta)"),
            ("return_customer", "Devuelta al cliente"),
            ("possible_return", "Posible devolución"),
            ("requested_return", "Solicitud de devolución"),
            ("returning", "En devolución"),
            ("origin", "En delegación origen"),
            ("destroyed", "Destruido por orden del cliente"),
            ("held_order", "Retenido por orden de paga"),
            ("in_platform", "En plataforma de destino"),
            ("extinguished", "Recanalizada (A extinguir)"),
            ("parcelshop", "Entregado en ASM PARCELSHOP"),
            ("parcelshop_confirm", "ASM PARCELSHOP CONFIRMA RECEPCIÓN"),
        ],
        copy=False,
    )

    def gls_asm_get_label(self):
        """Get GLS Label for this picking expedition"""
        self.ensure_one()
        if self.delivery_type != "gls_asm" or not self.gls_asm_public_tracking_ref:
            return
        pdf = self.carrier_id.gls_asm_get_label(self.gls_asm_public_tracking_ref)
        label_name = "gls_{}.pdf".format(self.gls_asm_public_tracking_ref)
        self.message_post(
            body=(_("GLS label for %s") % self.gls_asm_public_tracking_ref),
            attachments=[(label_name, pdf)],
        )

    def gls_asm_send_pickup(self):
        self.ensure_one()
        if self.delivery_type != "gls_asm" or not self.carrier_id.gls_is_pickup_service:
            return
        res = self.carrier_id.gls_asm_send_pickup(self)[0]
        if res.get("tracking_number", ""):
            self.carrier_tracking_ref = res["tracking_number"]
        msg = _(
            (
                "Request sent to carrier %(carrier_name)s for pick-up with"
                " tracking number %(ref)s"
            ),
            carrier_name=self.carrier_id.name,
            ref=self.carrier_tracking_ref,
        )
        self.message_post(body=msg)
        self.carrier_id.gls_asm_tracking_state_update(picking=self)
