# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os

from zeep import Client
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport as ZeepTransport

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


MRW_API_URL = {
    "test": "https://sagec-test.mrw.es/MRWEnvio.asmx?WSDL",
    "prod": "https://sagec.mrw.es/MRWEnvio.asmx?WSDL",
}


class MRWRequest:
    """Interface between MRW SOAP API and Odoo recordset
    Abstract MRW API Operations to connect them with Odoo

    Not all the features are implemented, but could be easily extended with
    the provided API. We leave the operations empty for future.
    """

    def __init__(
        self,
        username=None,
        password=None,
        client_code=None,
        department_code=None,
        franquicia_code=None,
        prod=False,
    ):
        api_env = "prod" if prod else "test"
        self.client = Client(wsdl=MRW_API_URL[api_env])
        self.username = username or ""
        self.pasword = password or ""
        self.client_code = client_code or ""
        self.department_code = department_code or ""
        self.franquicia_code = franquicia_code or ""
        self._set_soapheaders()
        self.history = HistoryPlugin(maxlen=10)

    def _set_soapheaders(self):

        credentials = self.client.get_element("ns0:AuthInfo")(
            UserName=self.username,
            Password=self.pasword,
            CodigoAbonado=self.client_code,
            CodigoDepartamento=self.department_code,
            CodigoFranquicia=self.franquicia_code,
        )

        self.client.set_default_soapheaders([credentials])

    def _process_reply(self, service, request=None):
        try:
            response = service(request=request)
        except Fault as e:
            raise UserError(e)
        return response

    def _cancel_shipment(self, reference=False):
        """Cancel shipment for the given ref
        :param str reference -- shipment reference string
        :returns: bool True if success
        """
        response = self._process_reply(
            self.client.service.CancelarEnvio,
            request={"CancelaEnvio": {"NumeroEnvioOriginal": reference}},
        )
        return response

    def _send_shipping(self, picking_vals):
        """Create new shipment
        :params vals dict of needed values
        :returns dict with MRW response containing the shipping code and label
        """
        method = "TransmEnvio"
        response = self._process_reply(
            self.client.service[method], request=picking_vals
        )
        return response

    def _get_label(self, vals, international=False):
        """Get shipping label for the given ref
        :param list reference -- shipping reference list
        :returns: base64 with pdf labels
        """
        method = "EtiquetaEnvioInternacional" if international else "EtiquetaEnvio"
        label = self._process_reply(self.client.service[method], request=vals)
        return label

    def _get_mrw_wsdl_tracking_file(self):
        wsdl_file = "mrw-api-tracking-prod.wsdl"
        return wsdl_file

    def _get_tracking_states(self, vals):
        """Get just tracking states from MRW info for the given reference"""
        transport = ZeepTransport(timeout=10)
        wsdl_file = self._get_mrw_wsdl_tracking_file()
        wsdl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../api/%s" % wsdl_file
        )
        zeep_client = Client(wsdl_path, transport=transport)
        response = zeep_client.service.GetEnvios(**vals)
        return response
