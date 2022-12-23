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


def log_request(method):
    """Decorator to write raw request/response in the SEUR request object"""

    def wrapper(*args, **kwargs):
        res = method(*args, **kwargs)
        try:
            res = args[0].response
            args[0].last_request = (
                f"{res.request.method} request to {res.request.url}\n"
                f"Headers: {res.request.headers}\n"
                f"Body: {res.request.body}"
            )
            args[0].last_response = (
                f"{res.status_code} {res.reason} {res.url}\n"
                f"Headers: {res.headers}\n"
                f"Response:\n{res.text}"
            )
        # Allow the decorator to fail
        except Exception:
            return res
        return res

    return wrapper


@log_request
def seur_method(http_method):
    """Decorator to attach our request custom headers in the SEUR request object"""

    def decorator(method):
        def wrapper(*args, **kwargs):
            # Only allow supported methods
            if http_method not in ["GET", "POST"]:
                return
            self, *_ = args
            seur_method = method.__name__.replace("__", "/").replace("_", "-")
            request = {
                "method": http_method,
                "url": urljoin(self.api_url, f"/pic/v1/{seur_method}"),
                "headers": {"Authorization": f"Bearer {self.token}"},
            }
            if http_method == "POST":
                request["json"] = kwargs.get("payload", {})
            elif http_method == "GET":
                request["params"] = {**kwargs}
            self.response = requests.request(**request)
            if not self.response.ok:
                self.error = "\n".join(
                    [
                        f"{error['title']} ({error['status']}): {error['detail']}"
                        for error in self.response.json().get("errors")
                    ]
                )
                raise UserError(f"SEUR ERROR: \n\n{self.error}")
            res = method(*args, **kwargs)
            return res

        return wrapper

    return decorator


class SeurAtlasRequest:
    """Interface between SEUR Atlas API and the Odoo ORM. Abstracts Seur API Operations
    to connect them with the proper Odoo workflows.
    """

    def __init__(
        self, user, password, secret, client_id, acc_number, id_number, prod=False
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
        self._set_token()

    @log_request
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
        )
        if not self.response.ok:
            self.error = self.response.json()
            return
        self.token = self.response.json()["access_token"]

    # SEUR ATLAS API METHODS

    @seur_method("POST")
    def shipments(self, payload=None):
        return self.response.json()

    @seur_method("GET")
    def labels(self, **kw):
        return self.response.json()["data"]

    @seur_method("GET")
    def tracking_services__simplified(self, **kw):
        """Query the current shipping state for a given shipping reference"""
        return self.response.json()["data"][0]

    @seur_method("GET")
    def tracking_services__extended(self, **kw):
        """Query the current shipping state history  for a given shipping
        reference"""
        return self.response.json()["data"][0]["situations"]

    @seur_method("GET")
    def next_working_day(self, **kw):
        return self.response.json()["data"]["nextWorkingDay"]

    @seur_method("GET")
    def cities(self, **kw):
        return self.response.json()["data"][0]