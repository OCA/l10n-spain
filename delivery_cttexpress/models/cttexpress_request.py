# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from lxml import etree

import logging

from zeep import Client
from zeep.helpers import serialize_object
from zeep.plugins import HistoryPlugin


_logger = logging.getLogger(__name__)

CTTEXPRESS_API_URL = {
    "test": "http://iberws.tourlineexpress.com:8686/ClientsAPI.svc?singleWsdl",
    "prod": "http://iberws.tourlineexpress.com:8700/ClientsAPI.svc?singleWsdl",
}


def log_request(method):
    """Decorator to write raw request/response in the CTT request object"""
    def wrapper(*args, **kwargs):
        res = method(*args, **kwargs)
        try:
            args[0].ctt_last_request = etree.tostring(
                args[0].history.last_sent["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
            args[0].ctt_last_response = etree.tostring(
                args[0].history.last_received["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
        # Don't fail hard on this. Sometimes zeep can't keep history
        except Exception:
            return res
        return res
    return wrapper


class CTTExpressRequest:
    """Interface between CTT Express SOAP API and Odoo recordset.
       Abstract CTT Express API Operations to connect them with Odoo
    """
    def __init__(self, user, password, agency, customer, contract, prod=False):
        self.user = user
        self.password = password
        self.agency = agency
        self.customer = customer
        self.contract = contract
        self.history = HistoryPlugin(maxlen=10)
        # We'll store raw xml request/responses in this properties
        self.ctt_last_request = False
        self.ctt_last_response = False
        self.client = Client(
            wsdl=CTTEXPRESS_API_URL["prod" if prod else "test"],
            plugins=[self.history],
        )

    @staticmethod
    def _format_error(error):
        """Common method to format error outputs

        :param zeep.objects.ArrayOfErrorResult error: Error response or None
        :return list: List of tuples with errors (code, description)
        """
        if not error:
            return []
        return [(x.ErrorCode, x.ErrorMessage) for x in error.ErrorResult]

    @staticmethod
    def _format_document(documents):
        """Common method to format document outputs

        :param list document: List of documents
        """
        if not documents:
            return []
        return [(x.FileName, x.FileContent) for x in documents.Document]

    def _credentials(self):
        """Get the credentials in the API expected format.

        :return dict: Credentials keys and values
        """
        return {
            "Id": self.user,
            "Password": self.password,
            "ContractCode": self.contract,
            "ClientCode": self.customer,
            "AgencyCode": self.agency,
        }

    # API Methods

    @log_request
    def manifest_shipping(self, shipping_values):
        """Create shipping with the proper picking values

        :param dict shipping_values: Shippng values prepared from Odoo
        :return tuple: tuple containing:
            list: Error Codes
            list: Document binaries
            str: Shipping code
        """
        values = dict(self._credentials(), **shipping_values)
        response = self.client.service.ManifestShipping(**values)
        return (
            self._format_error(response.ErrorCodes),
            self._format_document(response.Documents),
            response.ShippingCode
        )

    @log_request
    def get_tracking(self, shipping_code):
        """Gather tracking status of shipping code. Maps to API's GetTracking.

        :param str shipping_code: Shipping code
        :return tuple: contents of tuple:
            list: error codes in the form of tuples (code, descriptions)
            list: of OrderedDict with statuses
        """
        values = dict(self._credentials(), ShippingCode=shipping_code)
        response = self.client.service.GetTracking(**values)
        return (
            self._format_error(response.ErrorCodes),
            (
                response.Tracking
                and serialize_object(response.Tracking.Tracking)
                or []
            )
        )

    @log_request
    def get_documents(self, shipping_code):
        """Get shipping documents (label)

        :param str shipping_code: Shipping code
        :return tuple: tuple containing:
            list: error codes in the form of tuples (code, descriptions)
            list: documents in the form of tuples (file_content, file_name)
        """
        values = dict(self._credentials(), ShippingCode=shipping_code)
        response = self.client.service.GetDocuments(**values)
        return (
            self._format_error(response.ErrorCodes),
            self._format_document(response.Documents)
        )

    @log_request
    def get_documents_multi(
        self,
        shipping_codes,
        document_code="LASER_MAIN_ES",
        model_code="SINGLE",
        kind_code="PDF",
        offset=0
    ):
        """Get shipping codes documents

        :param str shipping_codes: shipping codes separated by ;
        :param str document_code: Document code, defaults to LASER_MAIN_ES
        :param str model_code: (SINGLE|MULTI1|MULTI3|MULTI4), defaults to SINGLE
            - SINGLE: Thermical single label printer
            - MULTI1: Sheet format 1 label per sheet
            - MULTI3: Portrait 3 labels per sheet
            - MULTI4: Landscape 4 labels per sheet
        :param str kind_code: (PDF|PNG|BMP), defaults to PDF
        :param int offset: Document offset, defaults to 0
        :return tuple: tuple containing:
            list: error codes in the form of tuples (code, descriptions)
            list: documents in the form of tuples (file_content, file_name)
        """
        values = dict(
            self._credentials(),
            **{
                "ShippingCodes": shipping_codes,
                "DocumentCode": document_code,
                "ModelCode": model_code,
                "KindCode": kind_code,
                "Offset": offset,
            }
        )
        response = self.client.service.GetDocumentsV2(**values)
        return (
            self._format_error(response.ErrorCodes),
            self._format_document(response.Documents)
        )

    @log_request
    def get_service_types(self):
        """Gets the hired service types. Maps to API's GetServiceTypes.

        :return tuple: contents of tuple:
            list: error codes in the form of tuples (code, descriptions)
            list: list of tuples (service_code, service_description):
        """
        response = self.client.service.GetServiceTypes(**self._credentials())
        return (
            self._format_error(response.ErrorCodes),
            [
                (x.ShippingTypeCode, x.ShippingTypeDescription)
                for x in response.Services.ClientShippingType
            ]
        )

    @log_request
    def cancel_shipping(self, shipping_code):
        """Cancel a shipping by code

        :param str shipping_code: Shipping code
        :return str: Error codes
        """
        values = dict(self._credentials(), ShippingCode=shipping_code)
        response = self.client.service.CancelShipping(**values)
        return [(x.ErrorCode, x.ErrorMessage) for x in response]

    @log_request
    def report_shipping(
        self,
        process_code="MAGENTO",
        document_type="XLSX",
        from_date=None,
        to_date=None
    ):
        """Get the shippings manifest. Mapped to API's ReportShipping

        :param str process_code: (MAGENTO|PRESTASHOP), defaults to "MAGENTO"
        :param str document_type: Report type, defaults to "XLSX" (PDF|XLSX)
        :param str from_date: Date from "yyyy-mm-dd", defaults to None.
        :param str to_date: Date to "yyyy-mm-dd", defaults to None.
        :return tuple: tuple containing:
            list: error codes in the form of tuples (code, descriptions)
            list: documents in the form of tuples (file_content, file_name)
        """
        values = dict(
            self._credentials(),
            ProcessCode=process_code,
            DocumentKindCode=document_type,
            FromDate=from_date,
            ToDate=to_date
        )
        response = self.client.service.ReportShipping(**values)
        return (
            self._format_error(response.ErrorCodes),
            self._format_document(response.Documents)
        )

    @log_request
    def validate_user(self):
        """Validate credentials against the API.

        :return tuple: tuple containing:
            int: Error code (0 for success)
            str: Validation result message
        """
        response = self.client.service.ValidateUser(**self._credentials())[0]
        return [(response.ErrorCode, response.ErrorMessage)]

    @log_request
    def create_request(self, delivery_date, min_hour, max_hour):
        """Create a shipping pickup request. CreateRequest API's mapping.

        :param datetime.date delivery_date: Delivery date
        :param str min_hour: Minimum pickup hour in format "HH:MM"
        :param str max_hour: Maximum pickup hour in format "HH:MM"
        :return tuple: tuple containing:
            list: Error codes
            str: Request shipping code
        """
        values = dict(
            self._credentials(),
            **{
                "DeliveryDate": delivery_date,
                "HourMinuteMin1": min_hour,
                "HourMinuteMax1": max_hour,
            }
        )
        response = self.client.service.CreateRequest(**values)
        return (
            self._format_error(response.ErrorCodes),
            response.RequestShippingCode
        )
