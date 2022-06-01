# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)..

import requests

from odoo import _, fields
from odoo.exceptions import UserError

DHL_PARCEL_DELIVERY_STATES_STATIC = {
    "A": "shipping_recorded_in_carrier",  # Assigned
    "T": "in_transit",  # Transit
    "R": "customer_delivered",  # Received
}

DHL_PARCEL_INCOTERMS_STATIC = [
    ("CPT", "Paid transport"),
    ("EXW", "Owed transport"),
]

DHL_PATH = "https://external.dhl.es/cimapi/api/v1/customer/"


class DhlParcelRequest(object):
    """Interface between DHL Parcel API and Odoo recordset
    Abstract DHL Parcel API Operations to connect them with Odoo
    """

    def __init__(self, carrier):
        self.carrier_id = carrier
        self.token = self._get_new_auth_token(
            username=carrier.dhl_parcel_uid or "",
            password=carrier.dhl_parcel_password or "",
        )
        self.year = str(fields.Date.today().year)[-1]  # last digit of the year
        self.label_format = self.carrier_id.dhl_parcel_label_format

    def _send_api_request(self, request_type, url, data=None, skip_auth=False):
        if data is None:
            data = {}
        try:
            auth = {}
            if not skip_auth:
                auth = {"Authorization": "Bearer {}".format(self.token)}
            if request_type == "GET":
                res = requests.get(url=url, headers=auth, timeout=60)
            elif request_type == "POST":
                res = requests.post(url=url, json=data, headers=auth, timeout=60)
            else:
                raise UserError(
                    _("Unsupported request type, please only use 'GET' or 'POST'")
                )
            res.raise_for_status()
            dhl_parcel_last_request = ("Request type: {}\nURL: {}\nData: {}").format(
                request_type, url, data
            )
            self.carrier_id.log_xml(dhl_parcel_last_request, "dhl_parcel_last_request")
            self.carrier_id.log_xml(res.text or "", "dhl_parcel_last_response")
        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 60s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(e, res.json().get("Message", "") if res.text else ""))
            )
        return res

    def _get_new_auth_token(self, username, password):
        res = self._send_api_request(
            request_type="POST",
            url=DHL_PATH + "authenticate",
            data={"Username": username, "Password": password},
            skip_auth=True,
        )
        return res.json()

    def create_shipment(self, vals):
        """
        :param dict vals -- data to use in create request
        :return dict with format
            {
                "Origin": "08",
                "Customer": "001000",
                "Tracking": "0870002260",
                "AWB": "",
                "LP": ["JJD00006080070002260001"],
                "Label": "JVBERi0xL..........” (Label data in Base64)
            }
        """
        res = self._send_api_request(
            request_type="POST", url=DHL_PATH + "shipment", data=vals
        )
        return res.json()

    def track_shipment(self, reference=False, track="status"):
        """Gets tracking info for shipment
            Event Code meaning:
                T - Transit
                A - Assigned
                R - Received
        :param str reference -- public shipping reference
        :param str track --
            - "events" (events)
            - "status" (current status with latest event)
            _ "both"
        :returns: dict with format
            {
                "Year": "0",
                "From": "20",
                "Tracking": "2013902080",
                "Origin": "San Sebastián",
                "Destination": "Vitoria",
                "Product": "EUROPLUS DOM",
                "Parcels": 1,
                "Weight": 86,
                "Ship_Reference": "PXKW00340DM99901",
                "AWB": "",
                "Receiver": "",
                "Events": [
                    {
                        "DateTime": "2020-10-02T10:40:49",
                        "Code": "A",
                        "Status": "Es posible que la fecha prevista de entrega"
                                    " se posponga un día hábil",
                        "Ubication": "Araba/Álava"
                    }
                ]
            }
        """
        res = self._send_api_request(
            request_type="GET",
            url=(DHL_PATH + "track?id={}&idioma=es&show={}".format(reference, track)),
        )
        return res.json()

    # TODO: The label_format parameter is not used and can be removed.
    def print_shipment(self, reference=False, label_format="PDF"):
        """Get shipping label for the given ref
        :param str reference -- public shipping reference
        :returns: base64 with pdf label or False
        """
        res = self._send_api_request(
            request_type="GET",
            url=(
                DHL_PATH + "shipment?"
                "Year={}&Tracking={}&Action=PRINT"
                "&LabelFrom={}&LabelTo={}&Format={}".format(
                    self.year, reference, 1, 1, self.label_format
                )
            ),
        )
        return res.json().get("Label", False)

    def cancel_shipment(self, reference=False):
        """Delete shipment
        :param str reference -- public shipping reference
        :returns: str -- message text
        """
        res = self._send_api_request(
            request_type="GET",
            url=DHL_PATH + "shipment?"
            "Year={}&Tracking={}&Action=DELETE".format(self.year, reference),
        )
        return True if res.status_code == 200 else False

    def hold_shipment(self, reference=False):
        """Hold shipment, shipping will not be documented until it's released
        :param str reference -- public shipping reference
        :returns: Boolean
        """
        res = self._send_api_request(
            request_type="GET",
            url=DHL_PATH + "shipment?"
            "Year={}&Tracking={}&Action=HOLD".format(self.year, reference),
        )
        return True if res.status_code == 200 else False

    def release_shipment(self, reference=False):
        """Release shipment
        :param str reference -- public shipping reference
        :returns: Boolean
        """
        res = self._send_api_request(
            request_type="GET",
            url=DHL_PATH + "shipment?"
            "Year={}&Tracking={}&Action=RELEASE".format(self.year, reference),
        )
        return True if res.status_code == 200 else False

    def end_day(self, customers="", report_type=""):
        """End day
        :param str customers -- Customer codes seperated by ',' or "ALL" for all of them
        :param str report_type -- PDF, DOC, XLS, RTF
        :returns: dict in format
            {
                "Shipments": [{
                    "Origin": "08",
                    "Customer": "001000",
                    "Year": "1",
                    "Tracking": "0824005834"
                }],
                "Report": "JVBERi..."
            }
        """
        res = self._send_api_request(
            request_type="POST",
            url=DHL_PATH + "endday",
            data={"Accounts": customers, "Report": report_type},
        )
        return res.json()
