# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError

SPFE_SERVICE_CONFIG = {
    "send": {
        "endpoint": "SendInvoiceSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "SendInvoice/v1/SendInvoice"
        ),
        "eb_service": "urn:cen.eu:en16931:submitinvoice",
        "eb_action": "SUBMITINVOICE",
    },
    "cancel": {
        "endpoint": "CancelInvoiceSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "CancelInvoice/v1/CancelInvoice"
        ),
        "eb_service": "urn:cen.eu:en16931:cancelinvoice",
        "eb_action": "CANCELINVOICE",
    },
    "query_id": {
        "endpoint": "GetInvoicesSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "GetInvoices/v1/GetInvoices"
        ),
        "eb_service": "urn:cen.eu:en16931:queryinvoice",
        "eb_action": "QUERYBYID",
    },
    "query_filter": {
        "endpoint": "GetRegisteredInvoiceSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "GetRegisteredInvoice/v1/GetRegisteredInvoice"
        ),
        "eb_service": "urn:cen.eu:en16931:queryinvoices",
        "eb_action": "QUERYBYFILTER",
    },
    "download_id": {
        "endpoint": "DownloadInvoicesByIDSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "DownloadInvoicesByID/v1/DownloadInvoicesByID"
        ),
        "eb_service": "urn:cen.eu:en16931:downloadinvoice",
        "eb_action": "DOWNLOADBYID",
    },
    "download_loc": {
        "endpoint": "DownloadInvoicesByLOCSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "DownloadInvoicesByLOC/v1/DownloadInvoicesByLOC"
        ),
        "eb_service": "urn:cen.eu:en16931:downloadinvoice",
        "eb_action": "DOWNLOADBYLOC",
    },
    "customer_events": {
        "endpoint": "CustomerInvoiceEventsSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "CustomerInvoiceEvents/v1/CustomerInvoiceEvents"
        ),
        "eb_service": "urn:cen.eu:en16931:submitaction",
        "eb_action": "ACCOUNTINGCUSTOMERPARTYACTION",
    },
    "supplier_events": {
        "endpoint": "SupplierInvoiceEventsSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "SupplierInvoiceEvents/v1/SupplierInvoiceEvents"
        ),
        "eb_service": "urn:cen.eu:en16931:submitaction",
        "eb_action": "ACCOUNTINGSUPPLIERPARTYACTION",
    },
    "validate_pre": {
        "endpoint": "ValidationInvoiceSOAP",
        "soap_action": (
            "https://www.agenciatributaria.gob.es/spfe/ns/services/"
            "ValidationInvoice/v1/ValidationInvoice"
        ),
        "eb_service": False,
        "eb_action": False,
    },
}


class AeatTaxAgency(models.Model):
    _inherit = "aeat.tax.agency"

    spfe_party_id = fields.Char(
        string="SPFE AEAT Party ID (NIF)",
        default="Q2826000H",
        help="Recipient PartyId in ebMS 3.0 header (AEAT NIF: Q2826000H).",
    )
    spfe_prod_cert_base_url = fields.Char(
        string="SPFE Production Base URL (Certificate)",
        default="https://www1.agenciatributaria.gob.es/wlpl/SPFE-FACT/ws",
    )
    spfe_prod_seal_base_url = fields.Char(
        string="SPFE Production Base URL (Electronic Seal)",
        default="https://www10.agenciatributaria.gob.es/wlpl/SPFE-FACT/ws",
    )
    spfe_test_cert_base_url = fields.Char(
        string="SPFE Pre-production Base URL (Certificate)",
        default="https://prewww1.aeat.es/wlpl/SPFE-FACT/ws",
    )
    spfe_test_seal_base_url = fields.Char(
        string="SPFE Pre-production Base URL (Electronic Seal)",
        default="https://prewww10.aeat.es/wlpl/SPFE-FACT/ws",
    )

    def _get_spfe_connection_info(self, company, service_key):
        """Return endpoint URL, SOAP action, and ebMS metadata for a SPFE service."""
        self.ensure_one()
        if service_key not in SPFE_SERVICE_CONFIG:
            raise UserError(
                self.env._(
                    "Unknown SPFE service key: %(key)s",
                    key=service_key,
                )
            )
        if service_key == "validate_pre" and not company.spfe_test:
            raise UserError(
                self.env._(
                    "The SPFE individual validation service (ValidationInvoiceSOAP) "
                    "is only available in the Pre-production (PRE) environment."
                )
            )
        cfg = SPFE_SERVICE_CONFIG[service_key]
        if company.spfe_test:
            base_url = (
                self.spfe_test_seal_base_url
                if company.spfe_use_seal_certificate
                else self.spfe_test_cert_base_url
            )
        else:
            base_url = (
                self.spfe_prod_seal_base_url
                if company.spfe_use_seal_certificate
                else self.spfe_prod_cert_base_url
            )
        if not base_url:
            raise UserError(
                self.env._(
                    "Missing SPFE base URL on tax agency '%(agency)s'.",
                    agency=self.name,
                )
            )
        url = f"{base_url.rstrip('/')}/{cfg['endpoint']}"
        return {
            "url": url,
            "soap_action": cfg["soap_action"],
            "eb_service": cfg["eb_service"],
            "eb_action": cfg["eb_action"],
            "to_party_id": self.spfe_party_id or "Q2826000H",
        }
