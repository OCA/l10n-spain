###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import binascii
import logging

from odoo import _
from odoo.exceptions import UserError

from .viaxpress_master_data import (
    VIAXPRESS_CONFIG,
    ViaxpressTechnicalException,
    ViaxpressUserException,
)

_logger = logging.getLogger(__name__)

try:
    from suds.client import Client
    from suds.xsd.doctor import Import, ImportDoctor
except (OSError, ImportError) as err:
    _logger.debug(err)


def init_request(actual_company):
    VIAXPRESS_CONFIG["client"]["id_cliente"] = actual_company.viaxpress_client_id
    VIAXPRESS_CONFIG["client"]["usuario"] = actual_company.viaxpress_user
    VIAXPRESS_CONFIG["client"]["password"] = actual_company.viaxpress_password

    VIAXPRESS_CONFIG["technical"]["host"] = actual_company.viaxpress_host
    VIAXPRESS_CONFIG["technical"]["port"] = actual_company.viaxpress_port
    VIAXPRESS_CONFIG["technical"]["url"] = actual_company.viaxpress_url
    VIAXPRESS_CONFIG["technical"]["wsdl_url"] = actual_company.viaxpress_wsdl_url

    return ViaxpressRequest(config=VIAXPRESS_CONFIG)


class ViaxpressRequest:
    def __init__(self, config):
        # Prepare the configuration
        self.config = config
        client_conf = config["client"]
        tech_conf = config["technical"]

        # Get the values from the client config
        self.CLIENT_ID, self.USER, self.PASSWORD = (
            client_conf["id_cliente"],
            client_conf["usuario"],
            client_conf["password"],
        )

        # Get the values from the technical config
        self.URL, wsdl_url, xml_schema, xml_schema_location = (
            tech_conf["url"],
            tech_conf["wsdl_url"],
            tech_conf["xml_schema"],
            f'{tech_conf["xml_schema"]}.xsd',
        )

        imp = Import(xml_schema, location=xml_schema_location)
        imp.filter.add(self.URL)

        # Define headers
        headers = {
            "Content-Type": tech_conf["content_type"],
            "POST": tech_conf["post"],
            "Host": tech_conf["host"],
            # 'SOAPAction': '',
        }

        # Set up the client
        self.client = Client(
            wsdl_url,
            doctor=ImportDoctor(imp),
            timeout=90,
        )
        self.client.set_options(headers=headers)

    def _prepare_headers(self, header_type):
        valid_header_types = [
            "PutExpedicionInternacional",
            "GetEtiquetasExpedicionToPdf",
            "GetDatosCliente",
        ]

        if header_type not in valid_header_types:
            raise ViaxpressTechnicalException(
                error_type="InvalidHeaderType",
                type=header_type,
            )

        headers = {
            "SOAPAction": f"{self.URL}/{header_type}",
        }

        self.client.options.headers.update(headers)

    def _request(self, header_type, **kwargs):
        # Check if the provided type is valid
        if hasattr(self.client.service, header_type):
            self._prepare_headers(header_type)
            func = getattr(self.client.service, header_type)
            res = func(**kwargs)
            return res
        else:
            raise ViaxpressTechnicalException(
                error_type="InvalidServiceType", header_type=header_type
            )

    def _prepare_object(self, **kwargs):
        data_class = kwargs.pop("data_class", None)
        request_object = self.client.factory.create(data_class)

        for key, val in kwargs.items():
            request_object[key] = (
                self._prepare_object(**val) if isinstance(val, dict) else val
            )

        return request_object

    def _prepare_method(self, vals):
        return {
            k: self._prepare_object(**v) if isinstance(v, dict) else v
            for k, v in vals.items()
        }

    def _send_shipping(self, vals):
        try:
            request_expedicion = self._prepare_method(
                vals["PutExpedicionInternacional"]
            )
            res_expedicion = self._request(
                "PutExpedicionInternacional", **request_expedicion
            )

            if res_expedicion["Resultado"] == "ERROR":
                error_type = "ResponseError"
                mensaje = res_expedicion["Mensaje"]
                if mensaje == "Usuario o password con errores":
                    error_type = "InvalidCredentials"

                raise ViaxpressUserException(error_type=error_type, response=mensaje)

        except ViaxpressTechnicalException:
            raise
        except ViaxpressUserException as e:
            raise UserError(_("{}").format(e)) from e
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording ViaXpress"
                    "delivery %(ref)s.\nTraceback:\n%(traceback)s"
                )
                % {
                    "ref": vals.get("referencia_c", ""),
                    "traceback": e,
                }
            ) from e

        return res_expedicion

    def _shipping_label(self, vals):
        try:
            request_get_etiquetas = self._prepare_method(
                vals["GetEtiquetasExpedicionToPdf"]
            )
            res_get_etiquetas = self._request(
                "GetEtiquetasExpedicionToPdf", **request_get_etiquetas
            )

        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording ViaXpress "
                    "delivery %(ref)s.\nTraceback:\n%(traceback)s"
                )
                % {
                    "ref": vals.get("referencia_c", ""),
                    "traceback": e,
                }
            ) from e

        if res_get_etiquetas["RespuestaGenerica"] == "ERROR":
            raise UserError(
                _(
                    "Error in response from server recording ViaXpress "
                    "delivery %(ref)s.\nTraceback:\n%(traceback)s"
                )
                % {
                    "ref": vals.get("referencia_c", ""),
                    "traceback": res_get_etiquetas["Descripcion"],
                }
            )

        label = res_get_etiquetas["Body"]

        return label and binascii.a2b_base64(str(label))

    def _get_client_data(self, vals):
        try:
            request_get_client = self._prepare_method(vals["GetDatosCliente"])
            res_get_client = self._request("GetDatosCliente", **request_get_client)

            if "Respuesta" in res_get_client and res_get_client["Respuesta"] == "ERROR":
                raise ViaxpressUserException(
                    error_type="InvalidCredentials", response=""
                )

        except ViaxpressUserException as e:
            raise UserError(_("{}").format(e)) from e
        except Exception as e:
            raise UserError(
                _(
                    "No response from server recording ViaXpress.\n" "Traceback:\n{}"
                ).format(e)
            ) from e

        allow_intraday = res_get_client.Cliente.permiteIntradia

        return {
            "allow_intraday": allow_intraday,
        }
