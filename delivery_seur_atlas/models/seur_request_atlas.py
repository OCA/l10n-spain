# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from urllib.parse import urljoin

import requests

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ATLAS_API_DOMAINS = {
    "prod": "servicios.api.seur.io",
    "test": "servicios.apipre.seur.io",
}


def seur_method(http_method):
    """Decorator to attach our request custom headers in the SEUR request object"""

    def decorator(method):
        def wrapper(*args, **kwargs):
            # Only allow supported methods
            if http_method not in ["GET", "POST", "PUT"]:
                return
            self, *_ = args
            seur_method = method.__name__.replace("__", "/").replace("_", "-")
            self.request(request_method=http_method, seur_method=seur_method, **kwargs)
            res = method(*args, **kwargs)
            return res

        return wrapper

    return decorator


class SeurAtlasRequest:
    """Interface between SEUR Atlas API and the Odoo ORM. Abstracts Seur API Operations
    to connect them with the proper Odoo workflows.
    """

    def __init__(
        self,
        user,
        password,
        secret,
        client_id,
        acc_number,
        id_number,
        prod=False,
        timeout=5,
    ):
        self.user = user
        self.password = password
        self.secret = secret
        self.client_id = client_id
        self.account_number = acc_number
        self.id_number = id_number
        self.last_request = False
        self.last_response = False
        self.response = False
        self.error = False
        self.api_url = f"https://{ATLAS_API_DOMAINS['prod' if prod else 'test']}"
        self.timeout = timeout
        self._set_token()

    def _log_request(self):
        """Store the last request and response for easier debugging"""
        self.last_request = (
            f"{self.response.request.method} request to {self.response.request.url}\n"
            f"Headers: {self.response.request.headers}\n"
            f"Body: {self.response.request.body}"
        )
        self.last_response = (
            f"{self.response.status_code} {self.response.reason} {self.response.url}\n"
            f"Headers: {self.response.headers}\n"
            f"Response:\n{self.response.text}"
        )

    def _set_token(self):
        """In order to operate, we should gather a token from the API. This token
        lasts for 30 seconds. After that, we must gather a new one"""
        self.response = requests.post(
            urljoin(self.api_url, "/pic_token"),
            data={
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.secret,
                "username": self.user,
                "password": self.password,
            },
            timeout=self.timeout,
        )
        self._log_request()
        if not self.response.ok:
            self.error = self.response.json()
            return
        self.token = self.response.json()["access_token"]

    def request(self, request_method, seur_method, **kwargs):
        """Raw query. It can be used as it is calling any API method, although its
        recomended to implement the proper methods in this connector so we abstract
        the output as much as possible in advance letting Odoo just retrieving what's
        needed"""
        if request_method not in ["GET", "POST", "PUT"]:
            return
        request_params = {
            "method": request_method,
            "url": urljoin(self.api_url, f"/pic/v1/{seur_method}"),
            "headers": {"Authorization": f"Bearer {self.token}"},
        }
        if request_method in ["POST", "PUT"]:
            request_params["json"] = kwargs.get("payload", {})
        elif request_method == "GET":
            request_params["params"] = {**kwargs}
        _logger.debug(f"SEUR Request to {seur_method}: {request_params}")
        self.response = requests.request(**request_params, timeout=self.timeout)
        _logger.debug(f"SEUR Response from {seur_method}: {self.response.content}")
        self._log_request()
        if not self.response.ok:
            self.error = "\n".join(
                [
                    f"{error['title']} ({error['status']}): {error['detail']}"
                    for error in self.response.json().get("errors")
                ]
            )
            raise UserError(f"SEUR ERROR: \n\n{self.error}")

    # SEUR ATLAS API METHODS

    @seur_method("POST")
    def shipments(self, payload: dict = None):
        return self.response.json()["data"]

    @seur_method("GET")
    def labels(self, **kw):
        return self.response.json()["data"]

    @seur_method("POST")
    def shipments__cancel(self, payload: dict = None):
        return self.response.json()["data"]

    @seur_method("GET")
    def tracking_services__simplified(self, **kw):
        """Query the current shipping state for a given shipping reference"""
        if not self.response.content:
            return []
        return self.response.json()["data"][0]

    @seur_method("GET")
    def tracking_services__extended(self, **kw) -> list:
        """Query the current shipping state history  for a given shipping
        reference"""
        if not self.response.content:
            return []
        return self.response.json()["data"][0]["situations"]

    @seur_method("GET")
    def next_working_day(self, **kw):
        return self.response.json()["data"]["nextWorkingDay"]

    @seur_method("GET")
    def cities(self, **kw):
        return self.response.json()["data"][0]
