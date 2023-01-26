# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from lxml import etree
from zeep import Client, Plugin, helpers
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport

from odoo.fields import Datetime

_logger = logging.getLogger(__name__)

TRACKING_STATES = {
    "EN TRÁNSITO": "in_transit",
    "MERCANCÍA EN REPARTO": "in_transit",
    "PENDIENTE DE REPARTO": "in_transit",
    "TU PEDIDO SERÁ ENVIADO A UN PUNTO SEUR": "in_transit",
    "EL REPARTIDOR HA DEJADO EL PAQUETE EN LA TIENDA SELECCIONADA": "in_transit",
    "YA PUEDES RECOGER TU ENVÍO EN LA TIENDA SEUR PICKUP SELECCIONADA": "in_transit",
    "ENTREGA EFECTUADA": "customer_delivered",
    "ENTREGADO": "customer_delivered",
    "ENTREGADO EN PUNTO": "customer_delivered",
    "ENTREGADO CAMBIO SIN RETORNO": "customer_delivered",
    "ENTREGA PARCIAL": "customer_delivered",
    "ENTREGADO A CLIENTE EN LA TIENDA SEUR PICKUP SELECCIONADA": "customer_delivered",
    "DOCUMENTACIÓN RECTIFICADA. DOMICILIO": "customer_delivered",
    "DOCUMENTACIÓN RECTIFICADA. DESTINO": "customer_delivered",
    "ENVÍO DEVUELTO": "canceled_shipment",
    "SINIESTRO": "canceled_shipment",
    "ENVIO ANULADO": "canceled_shipment",
}


class RewritePlugin(Plugin):
    def __init__(self, xpath, value):
        self.xpath = xpath
        self.value = value
        super().__init__()

    def egress(self, envelope, http_headers, operation, binding_options):
        node = envelope.xpath(self.xpath)
        if node:
            node[0].text = etree.CDATA(self.value.decode("utf-8"))


class SeurRequest(object):
    def __init__(self, carrier, record):
        self.carrier = carrier
        self.record = record
        self.ws_username = self.carrier.seur_ws_username
        self.ws_password = self.carrier.seur_ws_password
        self.cit_username = self.carrier.seur_cit_username
        self.cit_password = self.carrier.seur_cit_password
        self.franchise_code = self.carrier.seur_franchise_code
        self.vat = self.carrier.seur_vat
        self.accounting_code = self.carrier.seur_accounting_code
        self.printer = self.carrier.seur_printer
        self.label_size = self.carrier.seur_label_size
        self.integration_code = self.carrier.seur_integration_code
        self.service_code = self.carrier.seur_service_code
        self.product_code = self.carrier.seur_product_code
        self.send_sms = self.carrier.seur_send_sms
        self.label_format = self.carrier.seur_label_format
        self.use_packages_from_picking = self.carrier.seur_use_packages_from_picking

    def wsdl_get(self, service):
        if service in ["ImprimirECBWebService", "IntAppletWebService"]:
            return "http://cit.seur.com/CIT-war/services/%s?wsdl" % service
        if service == "WSConsultaExpediciones":
            return "https://ws.seur.com/webseur/services/%s?wsdl" % service
        raise NotImplementedError

    def soap_send(self, service, method, data):
        def create_rewrite_plugin(data):
            key = [k for k, v in data.items() if isinstance(v, dict)]
            if not key:
                return RewritePlugin("//no-dict", "")
            key = key[0]
            if "total_bultos" not in data[key]:
                return RewritePlugin("//missing-key", "")
            xml_root = etree.Element("root")
            xml_exp = etree.SubElement(xml_root, "exp")
            for _index in range(int(data[key].get("total_bultos") or 1)):
                package = etree.SubElement(xml_exp, "bulto")
                for k, v in data[key].items():
                    etree.SubElement(package, k).text = str(v or "")
            xml = etree.tostring(xml_root, encoding="utf8", method="xml")
            data[key] = "-RewritePlugin-"
            return RewritePlugin('//*[text()="-RewritePlugin-"]', xml)

        history = HistoryPlugin()
        client = Client(
            wsdl=self.wsdl_get(service),
            transport=Transport(),
            plugins=[history, create_rewrite_plugin(data)],
        )
        cli = client.bind(service)
        response = cli[method](**data)
        response = helpers.serialize_object(response, dict)
        # Add the history to the response so we are able to use it
        self.carrier.log_xml(history.last_sent, "seur_last_request")
        self.carrier.log_xml(history.last_received, "seur_last_response")
        return response

    def test_connection(self):
        res = self.soap_send(
            "ImprimirECBWebService",
            "impresionIntegracionPDFConECBWS",
            {
                "in0": self.cit_username,
                "in1": self.cit_password,
                "in2": "",
                "in3": "fichero.xml",
                "in4": self.vat,
                "in5": self.franchise_code,
                "in6": self.accounting_code,
                "in7": "odoo",
            },
        )
        return res and res["mensaje"] == "ERROR"

    def _prepare_create_shipping(self):
        partner = self.record.partner_id
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
        company = self.record.company_id
        phone = partner.phone and partner.phone.replace(" ", "") or ""
        mobile = partner.mobile and partner.mobile.replace(" ", "") or ""
        # Para envíos domésticos el código de mercancía mejor no ponerlo
        if partner.country_id.code in ["ES", "PT", "AD"]:
            goods = ""
        else:
            # Para el resto es obligado
            goods = "400"
        # peso
        if self.use_packages_from_picking and self.record.package_ids:
            weight = 0
            for package in self.record.package_ids:
                weight += max(package.shipping_weight, package.weight)
        else:
            weight = self.record.shipping_weight
        return {
            "ci": self.integration_code,
            "nif": self.vat,
            "ccc": self.accounting_code,
            "servicio": self.service_code,
            "producto": self.product_code,
            "cod_centro": "",
            "total_bultos": self.record.number_of_packages or 1,
            # The item pricelists in SEUR begin in a range o >1kg. So any item
            # below that weight will be invoiced with a minimum of 1kg.
            # http://ayuda.seur.com
            # /faq/tamano-peso-de-los-paquetes-a-enviar-a-traves-de-seur-com
            "total_kilos": weight or 1,
            "pesoBulto": ((weight / self.record.number_of_packages or 1) or 1),
            "observaciones": self.record.note,
            "referencia_expedicion": self.record.name,
            "ref_bulto": "",
            "clavePortes": "F",
            "clavePod": "",
            "claveReembolso": "F",
            "valorReembolso": "",
            "libroControl": "",
            "nombre_consignatario": partner_name,
            "direccion_consignatario": " ".join(
                [s for s in [partner.street, partner.street2] if s]
            ),
            "tipoVia_consignatario": "",
            "tNumVia_consignatario": "",
            "numVia_consignatario": "",
            "escalera_consignatario": "",
            "piso_consignatario": "",
            "puerta_consignatario": "",
            "poblacion_consignatario": partner.city,
            "codPostal_consignatario": partner.zip,
            "pais_consignatario": (
                partner.country_id and partner.country_id.code or ""
            ),
            "email_consignatario": partner.email,
            "telefono_consignatario": phone or mobile,
            "sms_consignatario": self.send_sms and mobile or "",
            "atencion_de": partner_att,
            "test_preaviso": "S",
            "test_reparto": "S",
            "test_email": partner.email and "S" or "N",
            "test_sms": mobile and "S" or "N",
            "id_mercancia": goods,
            "nombre_remitente": company.name,
            "direccion_remitente": " ".join(
                [s for s in [company.street, company.street2] if s]
            ),
            "codPostal_remitente": company.zip,
            "poblacion_remitente": company.city,
            "tipoVia_remitente": "",
            "eci": "N",
            "et": "N",
        }

    def create_shipping(self):
        package_info = self._prepare_create_shipping()
        if self.label_format == "txt":
            return self.soap_send(
                "ImprimirECBWebService",
                "impresionIntegracionConECBWS",
                {
                    "in0": self.cit_username,
                    "in1": self.cit_password,
                    "in2": self.printer.split(":")[0],
                    "in3": self.printer.split(":")[1],
                    "in4": self.label_size,
                    "in5": package_info,
                    "in6": "fichero.xml",
                    "in7": self.vat,
                    "in8": self.franchise_code,
                    "in9": self.accounting_code,
                    "in10": "odoo",
                },
            )
        else:
            return self.soap_send(
                "ImprimirECBWebService",
                "impresionIntegracionPDFConECBWS",
                {
                    "in0": self.cit_username,
                    "in1": self.cit_password,
                    "in2": package_info,
                    "in3": "fichero.xml",
                    "in4": self.vat,
                    "in5": self.franchise_code,
                    "in6": self.accounting_code,
                    "in7": "odoo",
                },
            )

    def tracking_state_update(self):
        res = self.soap_send(
            "WSConsultaExpediciones",
            "consultaExpedicionesStr",
            {
                "in0": "S",
                "in1": "",
                "in2": "",
                "in3": self.record.name,
                "in4": "",
                "in5": "",
                "in6": "",
                "in7": "",
                "in8": "",
                "in9": "",
                "in10": "",
                "in11": "0",
                "in12": self.ws_username,
                "in13": self.ws_password,
                "in14": "S",
            },
        )
        xml = etree.fromstring(res)
        if xml.tag == "ERROR":
            res_dict = {item.tag: item.text for item in xml}
            state = "\n{} - {} - {}".format(
                Datetime.to_string(Datetime.now()),
                res_dict.get("CODIGO"),
                res_dict.get("DESCRIPCION"),
            )
            values = {
                "tracking_state_history": "{}{}".format(
                    self.record.tracking_state_history or "", state
                )
            }
            # The reference isn't in the SEUR backend. Avoid further tracking calls when
            # the order isn't a new one.
            if (
                res_dict.get("CODIGO") == "CEXP_0006"
                and self.record.delivery_state != "shipping_recorded_in_carrier"
            ):
                values["delivery_state"] = "no_update"
            return values
        trackings = [{i.tag: i.text for i in sit} for sit in xml.xpath("//SIT")]
        if not trackings:
            return
        return {
            "tracking_state_history": "\n".join(
                [
                    "{} - {}".format(
                        t.get("FECHA_SITUACION", ""), t.get("DESCRIPCION_CLIENTE", "")
                    )
                    for t in trackings
                ]
            ),
            "delivery_state": TRACKING_STATES.get(
                trackings.pop().get("DESCRIPCION_CLIENTE"), "incidence"
            ),
        }

    def cancel_shipment(self):
        return self.soap_send(
            "IntAppletWebService",
            "modificarEnvioCIT",
            {
                "in0": {
                    "usuario": self.cit_username,
                    "password": self.cit_password,
                    "franquicia": self.franchise_code,
                    "nif": self.vat,
                    "ccc": self.accounting_code,
                    "referencia": self.record.name,
                    "accion": "A",
                    "valorReembolso": "",
                    "valorSeguro": "",
                    "pesoTotal": "",
                },
            },
        )
