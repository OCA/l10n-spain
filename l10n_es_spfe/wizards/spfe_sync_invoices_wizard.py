# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import re

from lxml import etree

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import split_every


class L10nEsSpfeSyncWizard(models.TransientModel):
    _name = "l10n.es.spfe.sync.wizard"
    _description = "Query and Download Invoices from AEAT SPFE"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    role = fields.Selection(
        selection=[
            ("AccountingCustomerParty", "Received Invoices (Customer / Recipient)"),
            ("AccountingSupplierParty", "Issued Invoices (Supplier / Issuer)"),
        ],
        required=True,
        default="AccountingCustomerParty",
    )
    date_filter = fields.Selection(
        selection=[
            ("IssueDate", "Invoice Issue Date"),
            ("RegistrationDate", "SPFE Registration Date"),
        ],
        string="Filter By",
        required=True,
        default="IssueDate",
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        default=fields.Date.context_today,
    )
    date_end = fields.Date(
        string="End Date",
        required=True,
        default=fields.Date.context_today,
    )
    download_and_import_bills = fields.Boolean(
        string="Download UBL & Create Draft Vendor Bills",
        default=True,
        help="Automatically download UBL 2.5 XML via locator "
        "(DownloadInvoicesByLOCSOAP) and import missing vendor bills.",
    )

    def action_sync_spfe_invoices(self):
        self.ensure_one()
        if self.date_start > self.date_end:
            raise UserError(
                self.env._("Start Date must be earlier than or equal to End Date.")
            )
        company = self.company_id
        _s, _t, comp_vat = company.partner_id._get_spfe_party_tax_info()
        comp_name = company.partner_id.commercial_partner_id.name

        all_items = []
        seq_id = False
        last_sub = False
        while True:
            props = [
                ("Role", self.role),
                ("InvoiceCompanyID", comp_vat),
                ("InvoiceRegistrationName", comp_name),
                ("DateFilter", self.date_filter),
            ]
            if self.date_filter == "IssueDate":
                props.extend(
                    [
                        ("IssueStartDate", self.date_start.isoformat()),
                        ("IssueEndDate", self.date_end.isoformat()),
                    ]
                )
            else:
                props.extend(
                    [
                        (
                            "RegistrationStartDate",
                            f"{self.date_start.isoformat()}T00:00:00Z",
                        ),
                        (
                            "RegistrationEndDate",
                            f"{self.date_end.isoformat()}T23:59:59Z",
                        ),
                    ]
                )
            if seq_id:
                props.append(("SequenceID", seq_id))

            resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
                company, "query_filter", message_properties=props
            )
            ds_bytes = next(iter(resp["attachments"].values()), None)
            if not ds_bytes:
                break
            st = self.env["base.ubl"].spfe_parse_document_status_xml(ds_bytes)
            last_sub = self.env["l10n.es.spfe.submission"].create(
                {
                    "company_id": company.id,
                    "operation_type": "query_filter",
                    "state": self.env[
                        "l10n.es.spfe.submission"
                    ]._map_response_code_to_state(st["response_code"]),
                    "message_id": resp["message_id"],
                    "response_id": st["id"],
                    "response_code": st["response_code"],
                    "response_description": st["description"],
                    "request_soap_xml": resp["request_soap_xml"].decode("utf-8"),
                    "response_xml": ds_bytes.decode("utf-8"),
                }
            )
            for item in st["items"]:
                self.env["l10n.es.spfe.submission.line"].create(
                    {
                        "submission_id": last_sub.id,
                        "invoice_number": item.get("id"),
                        "issuer_vat": item.get("issuer_vat"),
                        "status_code": item.get("status_code"),
                        "status_description": item.get("description"),
                        "spfe_locator": item.get("locator"),
                    }
                )
                all_items.append(item)
            if not st.get("sequence_id") or len(st["items"]) < 1000:
                break
            seq_id = st["sequence_id"]

        created_moves = self.env["account.move"]
        if (
            self.download_and_import_bills
            and self.role == "AccountingCustomerParty"
            and all_items
        ):
            created_moves = self._download_and_create_bills(company, all_items)

        if created_moves:
            return {
                "type": "ir.actions.act_window",
                "name": self.env._("Imported SPFE Vendor Bills"),
                "res_model": "account.move",
                "view_mode": "list,form",
                "domain": [("id", "in", created_moves.ids)],
            }
        if last_sub:
            return {
                "type": "ir.actions.act_window",
                "name": self.env._("SPFE Query Result"),
                "res_model": "l10n.es.spfe.submission",
                "res_id": last_sub.id,
                "view_mode": "form",
            }
        return True

    def _download_and_create_bills(self, company, items):
        locators_to_fetch = []
        loc_by_inv_key = {}
        loc_by_id = {}
        for item in items:
            loc = item.get("locator")
            if not loc:
                continue
            item_id = item.get("id")
            item_vat = (item.get("issuer_vat") or "").strip().upper()
            if item_id:
                loc_by_inv_key[(item_id, item_vat)] = loc
                loc_by_id[item_id] = loc
            existing = self.env["account.move"].search(
                [("company_id", "=", company.id), ("spfe_locator", "=", loc)],
                limit=1,
            )
            if not existing:
                locators_to_fetch.append(loc)

        created = self.env["account.move"]
        ubl_helper = self.env["base.ubl"]
        _nsmap, ns_braced = ubl_helper._ubl_get_nsmap_namespace("Invoice-2")
        ns = {k: v.strip("{}") for k, v in ns_braced.items()}
        for batch_locs in split_every(100, locators_to_fetch):
            dl_xml = ubl_helper.spfe_generate_download_by_loc_xml(batch_locs)
            resp = self.env["l10n.es.spfe.soap"].call_ebms_service(
                company,
                "download_loc",
                attachments=[("DescargarFacturaPorLOC.xml", dl_xml)],
                message_properties=[("Role", self.role)],
            )
            sub_vals = {
                "company_id": company.id,
                "operation_type": "download_loc",
                "state": "accepted",
                "message_id": resp["message_id"],
                "response_code": "200",
                "request_soap_xml": resp["request_soap_xml"].decode("utf-8"),
            }
            inv_attachments = []
            for att_xml in resp["attachments"].values():
                root = etree.fromstring(att_xml)
                local_name = etree.QName(root).localname
                if local_name == "DocumentStatus":
                    st = ubl_helper.spfe_parse_document_status_xml(att_xml)
                    sub_vals.update(
                        {
                            "state": self.env[
                                "l10n.es.spfe.submission"
                            ]._map_response_code_to_state(st["response_code"]),
                            "response_id": st["id"],
                            "response_code": st["response_code"],
                            "response_description": st["description"],
                            "response_xml": att_xml.decode("utf-8"),
                        }
                    )
                elif local_name == "Invoice":
                    inv_attachments.append((root, att_xml))
            if not sub_vals.get("response_description"):
                sub_vals["response_description"] = self.env._(
                    "Downloaded %(count)s UBL invoices.",
                    count=len(inv_attachments),
                )
            sub = self.env["l10n.es.spfe.submission"].create(sub_vals)
            for inv_root, inv_xml in inv_attachments:
                created |= self._import_single_spfe_ubl_bill(
                    company,
                    sub,
                    inv_root,
                    inv_xml,
                    ns,
                    loc_by_inv_key,
                    loc_by_id if len(locators_to_fetch) == 1 else {},
                )
        return created

    def _import_single_spfe_ubl_bill(
        self, company, sub, inv_root, inv_xml, ns, loc_by_inv_key, loc_by_id
    ):
        ubl_helper = self.env["base.ubl"]
        vals = ubl_helper.spfe_parse_invoice_ubl_to_move_vals(inv_xml, company)
        supp_vat = (
            ubl_helper._spfe_xpath_text(
                inv_root,
                "cac:AccountingSupplierParty/cac:Party/"
                "cac:PartyTaxScheme/cbc:CompanyID",
                ns,
            )
            or ""
        ).upper()
        loc = loc_by_inv_key.get((vals["ref"], supp_vat)) or loc_by_id.get(vals["ref"])
        bill = self.env["account.move"].search(
            [
                ("company_id", "=", company.id),
                ("move_type", "in", ("in_invoice", "in_refund")),
                ("commercial_partner_id", "=", vals["partner_id"]),
                ("ref", "=", vals["ref"]),
                ("spfe_locator", "=", False),
            ],
            limit=1,
        )
        if bill:
            bill.write({"spfe_state": "sent", "spfe_locator": loc})
        else:
            vals.update({"spfe_state": "sent", "spfe_locator": loc})
            bill = self.env["account.move"].create(vals)
        safe_ref = re.sub(r"[^A-Za-z0-9_.-]", "_", bill.ref or f"bill_{bill.id}")
        att = self.env["ir.attachment"].create(
            {
                "name": f"SPFE_IN_{safe_ref}.xml",
                "type": "binary",
                "datas": base64.b64encode(inv_xml),
                "mimetype": "application/xml",
                "res_model": "account.move",
                "res_id": bill.id,
            }
        )
        bill.spfe_ubl_attachment_id = att.id
        self.env["l10n.es.spfe.submission.line"].create(
            {
                "submission_id": sub.id,
                "move_id": bill.id,
                "invoice_number": bill.ref,
                "invoice_date": bill.invoice_date,
                "issuer_vat": supp_vat,
                "status_code": "200",
                "spfe_locator": loc,
                "payload_xml": inv_xml.decode("utf-8"),
            }
        )
        return bill
