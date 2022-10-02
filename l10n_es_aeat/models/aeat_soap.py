# (c) 2019 Acysos S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging

from requests import Session

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from zeep import Client, Settings
    from zeep.plugins import HistoryPlugin
    from zeep.transports import Transport
except (ImportError, IOError) as err:
    _logger.debug(err)


class L10nEsAeatSoap(models.TransientModel):
    _name = "l10n.es.aeat.soap"
    _description = "AEAT SOAP"

    def connect_soap(self, wsdl, model, settings=None):
        if "company_id" in model._fields:
            public_crt, private_key = self.env[
                "l10n.es.aeat.certificate"
            ].get_certificates(model.company_id)
        else:
            public_crt, private_key = self.env[
                "l10n.es.aeat.certificate"
            ].get_certificates()

        session = Session()
        session.cert = (public_crt, private_key)
        transport = Transport(session=session)

        history = HistoryPlugin()
        settings = Settings(**settings or {})
        client = Client(
            wsdl=wsdl, transport=transport, settings=settings, plugins=[history]
        )
        return client

    def get_test_mode(self, port_name, model):
        port_name = model.get_test_mode(port_name)
        return port_name

    def connect_wsdl(self, service, wsdl, port_name, model, settings=None):
        client = self.connect_soap(wsdl, model, settings=settings)
        port_name = self.get_test_mode(port_name, model)
        serv = client.bind(service, port_name)
        return serv

    def send_soap(
        self, service, wsdl, port_name, model, operation, *args, settings=None
    ):
        serv = self.connect_wsdl(service, wsdl, port_name, model, settings=settings)
        res = serv[operation](*args)
        return res
