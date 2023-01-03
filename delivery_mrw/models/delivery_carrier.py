# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import datetime

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .mrw_request import MRWRequest

MRW_NATIONAL_SERVICES = [
    ("0000", "Urgente 10"),
    ("0005", "Urgente Hoy"),
    ("0010", "Promociones"),
    ("0100", "Urgente 12"),
    ("0110", "Urgente 14"),
    ("0120", "Urgente 22"),
    ("0200", "Urgente 19"),
    ("0205", "Urgente 19 Expediciones"),
    ("0210", "Urgente 19 Mas 40 Kilos"),
    ("0220", "48 Horas Portugal"),
    ("0230", "Bag 19"),
    ("0235", "Bag 14"),
    ("0300", "Economico"),
    ("0310", "Economico Mas 40 Kilos"),
    ("0350", "Economico Interinsular"),
    ("0400", "Express Documentos"),
    ("0450", "Express 2 Kilos"),
    ("0480", "Caja Express 3 Kilos"),
    ("0490", "Documentos 14"),
    ("0800", "Ecommerce"),
]

MRW_INTERNATIONAL_SERVICES = [
    ("DOC", "DOCUMENTOS"),
    ("PAC", "PAQUETES"),
    ("SC", "SUPERCITY"),
    ("EUROP", "EUROPAQ"),
    ("BOX25", "ECOBOX25"),
    ("EURO2", "EURO 2KG"),
    ("ECOMM", "ECOMMERCE"),
]


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("mrw", "MRW")], ondelete={"mrw": "set default"}
    )

    mrw_username = fields.Char(string="Username")
    mrw_password = fields.Char(string="Password")
    mrw_client_code = fields.Char(string="Client Code")
    mrw_department_code = fields.Char(string="Department Code")
    mrw_franquicia_code = fields.Char(string="Franquicia Code")
    mrw_label_top_margin = fields.Integer(default=2)
    mrw_label_left_margin = fields.Integer(default=2)

    international_shipping = fields.Boolean(default=False)

    @api.depends("mrw_international_service", "mrw_national_service")
    def _compute_mrw_service(self):
        for item in self:
            item.mrw_service = (
                item.mrw_international_service
                if self.international_shipping
                else item.mrw_national_service
            )

    mrw_service = fields.Char(compute="_compute_mrw_service")

    mrw_international_service = fields.Selection(
        selection=MRW_INTERNATIONAL_SERVICES,
        string="MRW Service",
        help="Set the MRW Service",
        default="PAC",  # Courier
    )
    mrw_national_service = fields.Selection(
        selection=MRW_NATIONAL_SERVICES,
        string="MRW Service",
        help="Set the MRW Service",
        default="0300",  # Courier
    )

    mrw_horario_from = fields.Float()
    mrw_horario_to = fields.Float(default=23.99)

    mrw_en_franquicia = fields.Selection(
        selection=[
            ("N", "Sin recogida ni entrega en franquicia."),
            ("R", "Con recogida en franquicia."),
            ("E", "Con entrega en franquicia."),
            ("A", "Con recogida y entrega en franquicia"),
        ],
        default="N",
        help="Indicador de entrega en franquicia.",
    )

    mrw_notification_channel = fields.Selection(
        string="Notification Channel", selection=[("1", "Email"), ("2", "SMS")]
    )
    mrw_notification_type = fields.Selection(
        string="Notification Type",
        selection=[
            ("1", "Confirmación de entrega (solo SMS)"),
            ("2", "Seguimiento de envío"),
            ("3", "Aviso de entrega en franquicia"),
            ("4", "Preaviso de entrega"),
            ("5", "Confirmación de recogida (solo SMS)"),
        ],
        help="Confirmación de entrega: informa de la entrega del envío en destino."
        "Nota: Solo para SMS.\n"
        "Seguimiento de envío: informa los diferentes estados de tránsito"
        "del envío.\n"
        "Aviso de entrega en franquicia: informa al destinatario del envío"
        "que la mercancía está disponible en la franquicia de destino. Solo"
        "tendrá sentido para entrega en franquicia, y será obligatorio.\n"
        "Preaviso de entrega: informa al destinatario del envío de la fecha"
        "de entrega de la mercancía. Solo tendrá sentido cuando NO sea"
        "entrega en franquicia.\n"
        "Confirmación de recogida: informa al destinatario que el envío ha"
        "sido recogido en origen. Solo tendrá sentido cuando NO sea"
        "entrega en franquicia. Nota: Solo para SMS.\n",
    )

    mrw_reembolso = fields.Selection(
        selection=[
            ("N", "Sin reembolso"),
            ("O", "Con reembolso comisión en origen"),
            ("D", "Con reembolso comisión en destino"),
        ],
        default="N",
        help="Indicador de reembolso. El importe del reembolso será cogido"
        " del pedido de venta.",
    )

    mrw_retorno = fields.Selection(
        selection=[
            ("N", "Sin retorno"),
            ("D", "Retorno de albarán cobro en destino"),
            ("S", "Retorno de mercancia"),
        ],
        default="N",
    )

    mrw_api_language = fields.Char(
        string="Language Code",
        default="3082",
        help="3082 for Spanish; 2070 for Portuguese",
    )
    mrw_api_filter_type = fields.Integer(
        string="Filter Type",
        default=0,
        help="0 for tracking number; 1 for reference; 2 package reference",
    )
    mrw_api_information_type = fields.Integer(
        string="Information Type",
        default=0,
        help="0 for Basic Information; 1 for Detailed",
    )

    @api.constrains("mrw_en_franquicia")
    def check_mrw_en_franquicia(self):
        if self.mrw_en_franquicia in ("R", "A"):
            raise UserError(
                _(
                    "For the moment MRW only supports:\n"
                    "- Sin recogida ni entrega en franquicia.\n"
                    "- Con entrega en franquicia. "
                )
            )

    @api.model
    def _mrw_log_request(self, mrw_request):
        """Helper to write raw request/response to the current picking. If debug
        is active in the carrier, those will be logged in the ir.logging as well"""
        mrw_last_request = mrw_last_response = False
        try:
            mrw_last_request = etree.tostring(
                mrw_request.history.last_sent["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
            mrw_last_response = etree.tostring(
                mrw_request.history.last_received["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
        # Don't fail hard on this. Sometimes zeep could not be able to keep history
        except Exception:
            return
        # Debug must be active in the carrier
        self.log_xml(mrw_last_request, "mrw_request")
        self.log_xml(mrw_last_response, "mrw_response")

    def _mrw_check_response(self, response):
        if not int(response["Estado"]):
            raise UserError(_("MRW Error: %s)" % response["Mensaje"]))
        elif response["Estado"] and response["Mensaje"]:
            return response["Mensaje"]
        return ""

    def remove_found_regex_from_string(self, regex, string):
        limit_inf = regex.span()[0]
        limit_sup = regex.span()[1]
        string = string[:limit_inf] + string[limit_sup:]
        regex = "0" if regex[0] in ("S/N", "s/n") else regex[0]
        return regex, string

    def mrw_address(self, partner, international):
        # Method to get parameters CodigoTipoVia. Via, Numero, Resto from odoo address.
        # If street and number are in the first address line, and floor and door in the
        # second one, it will always work properly.Otherwise, it could assign them wrong

        street = partner.street.replace(",", "") if partner.street else ""
        street2 = partner.street2.replace(",", "") if partner.street2 else ""
        if not street:
            raise UserError(_("Couldn't find partner %s street") % partner.name)
        if international:
            return {
                "Via": street + street2,
                "CodigoPostal": partner.zip or "",
                "Poblacion": partner.city or "",
                "Estado": partner.state_id.name,
                "CodigoPais": partner.country_id.code,
            }
        # we find s/n or any number that is not d-d, dºor dª in street
        numero = re.search(
            r"(?!(\d+[ºª]?-))(?!(\d+[ºª]))(?<![-\d])\d+", street
        ) or re.search(r"S\/N|s\/n", street)
        if not numero:
            if re.search(r"\d+-\d+", street):
                # there are street numbers in an interval like 1-3 that indicate
                # the same building/house. But MRW API doesn't accept them.
                raise UserError(
                    _(
                        "Solamente se permiten caracteres numéricos en el campo número"
                        " de la dirección. Número: %s"
                    )
                    % re.search(r"\d+-\d+", street)[0]
                )
            # we search in street 2
            numero2 = re.search(
                r"(?!(\d+[ºª]?-))(?!(\d+[ºª]))(?<![-\d])\d+", street2
            ) or re.search(r"S\/N|s\/n", street2)
            if numero2:
                numero2, street2 = self.remove_found_regex_from_string(numero2, street2)
        if numero:
            numero, street = self.remove_found_regex_from_string(numero, street)
            piso_puerta = re.search(r"(\d+[ºª]?[- ]?)(\d+[ºª]?)", street)
            if piso_puerta:
                piso_puerta, street = self.remove_found_regex_from_string(
                    piso_puerta, street
                )
                street2 = piso_puerta + " " + street2
        # check if in the beggining of the street we have something like cl/ cl. ...
        street_type = re.search(r"^[a-zA-Z]{1,4}[\/|\.]", street)
        if street_type:
            limit = street_type.span()[1]
            street_type = street[:limit]
            street = street[limit:]

        return {
            "CodigoTipoVia": street_type or "",
            "Via": street,
            "Numero": numero or numero2 or "",
            "Resto": street2 or "",
            "CodigoPostal": partner.zip or "",
            "Poblacion": partner.city or "",
        }

    def get_notificaciones(self, partner):
        notificaciones = {}
        channel = self.mrw_notification_channel
        if channel:
            notificaciones["NotificacionRequest"] = {}
            notificaciones["NotificacionRequest"]["CanalNotificacion"] = channel
            notificaciones["NotificacionRequest"][
                "TipoNotificacion"
            ] = self.mrw_notification_type
            notificaciones["NotificacionRequest"]["MailSMS"] = (
                partner.email if channel == "1" else partner.mobile
            )

        return notificaciones

    def _prepare_mrw_shipping(self, picking):
        """Convert picking values for mrw api
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        receiving_partner = picking.partner_id
        today = datetime.today()
        vals = {
            # Nodo opcional que contendrá información sobre los datos de recogida u
            # origen del envío solicitado.
            # De momento no esta implementada la funcionalidad, así que se le pasen
            # datos o no, siempre se cogerá la información del abonado.
            "DatosRecogida": "",
            "DatosEntrega": {
                "Direccion": self.mrw_address(
                    receiving_partner, self.international_shipping
                ),
                "Nif": receiving_partner.vat or "",
                "Nombre": receiving_partner.name,
                "Telefono": receiving_partner.phone or "",
                "ALaAtencionDe": "",
                "Observaciones": picking.note or "",
            },
            # nodo opcional
            "DatosServicio": {
                # fecha de servicio del envío. Si no se indica, internamente se cogerá
                # la fecha actual del sistema.
                "Fecha": picking.scheduled_date
                if picking.scheduled_date > today
                else today,
                # número opcional de referencia del envío del cliente
                "Referencia": picking.name,
                "CodigoServicio": self.mrw_service,
                "Bultos": "",
                # Será obligatorio informar en caso que no haya desglose de bultos.
                "NumeroBultos": picking.number_of_packages,
                # El separador decimal debe de ser la coma (,).
                "Peso": str(picking.shipping_weight).replace(".", ","),
                "Notificaciones": self.get_notificaciones(receiving_partner)
                # Hay más campos no obligatorios no puestos aqui
            },
        }

        if not self.international_shipping:
            # Campos específicos de envío nacional en DatosEntrega
            vals["DatosEntrega"]["Contacto"] = ""
            # Lista opcional de rangos horarios. Contendrá una lista de nodos con
            # los siguientes elementos:
            #  -Desde: Rango inferior del horario en formato HH:MM
            #  -Hasta: Rango superior del horario en formato HH:MM
            if self.mrw_horario_from == 0.0 and self.mrw_horario_to == 23.99:
                horario = []
            else:
                horario = {
                    "Rangos": {
                        "HorarioRangoRequest": {
                            "Desde": str(self.mrw_horario_from),
                            "Hasta": str(self.mrw_horario_to),
                        }
                    }
                }
            vals["DatosEntrega"]["Horario"] = horario

            # Campos específicos de envío nacional en DatosServicio
            # Indicador de recogida/entrega en franquicia. De momento la única
            # que esta implementada es la entrega en franquicia.
            vals["DatosServicio"]["EnFranquicia"] = self.mrw_en_franquicia
            # En caso de servicio URGENTE HOY hay que indicar en que frecuencia
            # saldrá el servicio. Valores posibles: Frecuencia 1, Frecuencia 2
            vals["DatosServicio"]["Frecuencia"] = (
                "Frecuencia 1" if self.mrw_service == "0005" else ""
            )
            # Número sobre para servicios prepagados.
            vals["DatosServicio"]["NumeroSobre"] = ""
            vals["DatosServicio"]["Reembolso"] = self.mrw_reembolso
            vals["DatosServicio"]["ImporteReembolso"] = (
                str(picking.sale_id.amount_total).replace(".", ",")
                if self.mrw_reembolso != "N"
                else ""
            )
            vals["DatosServicio"]["Retorno"] = self.mrw_retorno
        else:
            # Codigo de moneda asociado a ValorEstadistico
            vals["DatosServicio"]["CodigoMoneda"] = ""
            # Valor estadístico del envío interpretado con la moneda indicada
            # en CodigoMoneda.
            vals["DatosServicio"]["ValorEstadistico"] = ""
            vals["DatosServicio"]["ValorEstadisticoEuros"] = ""
        return vals

    def mrw_send_shipping(self, pickings):
        return [self.mrw_create_shipping(p) for p in pickings]

    def mrw_create_shipping(self, picking):
        """Send the package to mrw
        :param picking: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        mrw_request = MRWRequest(self)
        vals = self._prepare_mrw_shipping(picking)
        response = mrw_request._send_shipping(vals)
        vals.update({"tracking_number": False, "exact_price": 0})
        response_message = self._mrw_check_response(response)
        self._mrw_log_request(mrw_request)
        mrw_tracking_ref = response["NumeroEnvio"]
        vals["tracking_number"] = mrw_tracking_ref or ""
        label = self.mrw_get_label(mrw_tracking_ref, picking)
        # We post an extra message in the chatter with the barcode and the
        # label because there's clean way to override the one sent by core.
        body = _(response_message + "<br> MRW Shipping Label:")
        attachment = []
        if label["EtiquetaFile"]:
            attachment = [
                (
                    "mrw_label_{}.pdf".format(mrw_tracking_ref),
                    label["EtiquetaFile"],
                )
            ]
        picking.message_post(body=body, attachments=attachment)
        return vals

    def mrw_rate_shipment(self, order):
        """There's no public API so another price method should be used."""
        return {
            "success": True,
            "price": self.product_id.lst_price,
            "error_message": _(
                "MRW API doesn't provide methods to compute delivery rates so you"
                " should rely on another price method instead or override this one in"
                " your custom code.\n"
                " Zero price can also be set in order to invoice it later to the"
                " customer: check the field 'Free if order amount is above' and put"
                " Import=0."
            ),
            "warning_message": _(
                "MRW API doesn't provide methods to compute delivery rates so you"
                " should rely on another price method instead or override this one in"
                " your custom code.\n"
                " Zero price can also be set in order to invoice it later to the"
                " customer: check the field 'Free if order amount is above' and put"
                " Import=0."
            ),
        }

    def mrw_cancel_shipment(self, pickings):
        """ "Cancel the expedition
        :param pickings - stock.picking recordset
        :returns tracking_number of shippig cancelled
        """

        for picking in pickings.filtered("carrier_tracking_ref"):
            mrw_request = MRWRequest(self)
            response = mrw_request._cancel_shipment(picking.carrier_tracking_ref)
            self._mrw_check_response(response)
            self._mrw_log_request(mrw_request)
        return True

    def _prepare_label(self, mrw_tracking_ref):
        return {
            "NumeroEnvio": mrw_tracking_ref,
            "ReportTopMargin": self.mrw_label_top_margin,
            "ReportLeftMargin": self.mrw_label_left_margin,
        }

    def mrw_get_label(self, mrw_tracking_ref, picking):
        """Generate label for picking
        :param picking - stock.picking record
        :returns pdf file
        """
        self.ensure_one()
        if not mrw_tracking_ref:
            return False
        vals = self._prepare_label(mrw_tracking_ref)
        mrw_request = MRWRequest(self)
        label = mrw_request._get_label(vals)
        self._mrw_check_response(label)
        return label

    def mrw_get_tracking_link(self, picking):
        """Provide tracking link for the customer"""
        tracking_url = (
            "https://www.mrw.es/seguimiento_envios/MRW_resultados_consultas.asp?"
            "modo={}&envio={}"
        )
        modo = "internacional" if self.international_shipping else "nacional"
        return tracking_url.format(modo, picking.carrier_tracking_ref)

    def action_get_manifest(self):
        """Action to launch the manifest wizard"""
        self.ensure_one()
        wizard = self.env["mrw.manifest.wizard"].create({"carrier_id": self.id})
        view_id = self.env.ref("delivery_mrw.delivery_mrw_manifest_wizard_form").id
        return {
            "name": _("MRW Manifest"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mrw.manifest.wizard",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "target": "new",
            "res_id": wizard.id,
            "context": self.env.context,
        }

    def _prepare_mrw_tracking(self, picking):
        self.ensure_one()
        return {
            "login": self.mrw_username,
            "pass": self.mrw_password,
            "codigoIdioma": self.mrw_api_language,
            "tipoFiltro": self.mrw_api_filter_type,
            "valorFiltroDesde": picking.carrier_tracking_ref,
            "valorFiltroHasta": picking.carrier_tracking_ref,
            "fechaDesde": "",
            "fechaHasta": "",
            "tipoInformacion": self.mrw_api_information_type,
            "codigoAbonado": self.mrw_client_code,
            "codigoFranquicia": self.mrw_franquicia_code,
        }

    def mrw_tracking_state_update(self, picking):
        """Tracking state update"""
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        mrw_request = MRWRequest(self)
        vals = self._prepare_mrw_tracking(picking)
        response = mrw_request._get_tracking_states(vals)
        if response["MensajeSeguimiento"] != "Busqueda correcta por Número de Albarán.":
            raise UserError(_(response["MensajeSeguimiento"]))
        tracking_states = mrw_request._process_mrw_tracking_response(response)
        if not tracking_states:
            return
        date_format = "%d/%m/%Y %H:%M"
        tracking_lines = []
        for t in tracking_states:
            date_str = t.get("delivery_date").strftime(date_format)
            tracking_lines.append(
                "%s - [%s] %s" % (date_str, t.get("state_code"), t.get("description"))
            )
        picking.tracking_state_history = "\n".join(tracking_lines)
        tracking = tracking_states.pop()
        picking.tracking_state = "[{}] {}".format(
            tracking.get("state_code"), tracking.get("description")
        )
        if tracking.get("state_code") == "00":
            picking.write({"date_delivered": tracking.get("delivery_date")})
