###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models

from .viaxpress_request import init_request


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("viaxpress", "VIAXPRESS")],
        ondelete={
            "viaxpress": lambda recs: recs.write(
                {"delivery_type": "fixed", "fixed_price": 0}
            )
        },
    )

    def _prepare_viaxpress_shipping(self, picking):
        self.ensure_one()

        client, user, password = self._get_login()

        sender_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )

        receiver_partner = (
            picking.partner_id or picking.partner_id.commercial_partner_id
        )

        con_retorno = False
        reembolso = picking.sale_id.amount_total if con_retorno else 0.0

        request_data = {
            "PutExpedicionInternacional": {
                "ObjetoEnvio": {
                    "data_class": "ClaseExpedicionInternacional",
                    "Peso": picking.shipping_weight,
                    "Bultos": picking.number_of_packages,
                    "Reembolso": reembolso,
                    "Fecha": fields.Date.today().strftime("%Y-%m-%dT%H:%M:%S"),
                    "ConRetorno": con_retorno,
                    "Tipo": "E",
                    "Debidos": False,
                    "Asegurado": False,
                    "Imprimir": False,
                    "ConDevolucionAlbaran": False,
                    "Intradia": picking.is_intraday,
                    "Observaciones": picking.note or "",
                    "AlbaranRemitente": picking.name,
                    "Modo": "A",
                    "TextoAgencia": "",
                    "Terminal": "",
                    "ObjetoLogin": {
                        "data_class": "LoginVX",
                        "IdCliente": client,
                        "Usuario": user,
                        "Password": password,
                    },
                    "ObjetoDestinatario": {
                        "data_class": "DestinatarioVXInternacional",
                        "RazonSocial": receiver_partner.name,
                        "Domicilio": receiver_partner.street,
                        "Cpostal": receiver_partner.zip,
                        "Poblacion": receiver_partner.city,
                        "Municipio": receiver_partner.city,
                        "Provincia": receiver_partner.state_id.name,
                        "Contacto": "",
                        "Telefono": receiver_partner.phone,
                        "Email": receiver_partner.email,
                        "Pais": receiver_partner.country_id.code,
                    },
                    "ObjetoRemitente": {
                        "data_class": "Remitente",
                        "RazonSocial": sender_partner.name,
                        "Domicilio": sender_partner.street,
                        "Cpostal": sender_partner.zip,
                        "Poblacion": sender_partner.city,
                        "Provincia": sender_partner.state_id.name,
                        "Contacto": "",
                        "Telefono": sender_partner.phone,
                        "Email": sender_partner.email,
                    },
                },
                "bultosRetorno": 1,
                "tipoMenor": None,
            },
            "picking": picking,
        }

        return request_data

    def _prepare_viaxpress_label(self, picking, reference=False):
        client, user, password = self._get_login()

        request_data = {
            "GetEtiquetasExpedicionToPdf": {
                "login": {
                    "data_class": "Login",
                    "ClientId": client,
                    "UserId": user,
                    "Password": password,
                },
                "expedicion": reference,
            },
            "picking": picking,
        }

        return request_data

    def viaxpress_send_shipping(self, pickings):
        actual_company = self.env["res.company"].search(
            [("id", "=", self.env.user.company_id.id)]
        )

        viaxpress_request = init_request(actual_company)

        result = []
        for picking in pickings:
            vals = self._prepare_viaxpress_shipping(picking)
            response = viaxpress_request._send_shipping(vals)

            vals["tracking_number"] = getattr(response, "ReferenciaVx", False)
            vals["exact_price"] = 0.0

            picking.viaxpress_public_tracking_ref = vals["tracking_number"]

            result.append(vals)
        return result

    def viaxpress_get_label(self, reference):
        if not reference:
            return False

        actual_company = self.env["res.company"].search(
            [("id", "=", self.env.user.company_id.id)]
        )

        viaxpress_request = init_request(actual_company)
        picking = self.env["stock.picking"].search(
            [("viaxpress_public_tracking_ref", "=", reference)]
        )

        vals = self._prepare_viaxpress_label(picking, reference=reference)
        label = viaxpress_request._shipping_label(vals)

        if not label:
            return False
        return label

    def _get_login(self):
        actual_company = self.env["res.company"].search(
            [("id", "=", self.env.user.company_id.id)]
        )

        return [
            actual_company.viaxpress_client_id,
            actual_company.viaxpress_user,
            actual_company.viaxpress_password,
        ]
