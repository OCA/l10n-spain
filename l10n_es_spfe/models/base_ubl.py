# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, fields, models
from odoo.tools import float_is_zero, float_repr, float_round

SPFE_CUSTOMIZATION_ID = (
    "urn:cen.eu:en16931:2026#conformant#urn:aeat.es:spfe:1.0.0:extended"
)
SPFE_PROFILE_ID = "urn:aeat:names:specification:ubl:schema:profile:B2B"
SPFE_SCHEMA_DOC_PREFIX = "urn:aeat:names:specification:schema:"
SPFE_SCHEMA_LINE_PREFIX = "urn:aeat:names:specification:schema:lin:"
SPFE_SCHEMA_ADD_PREFIX = "urn:aeat:names:specification:schema:add:"
VATEX_ALLOWED_CATEGORIES = ("E", "AE", "O", "G", "D", "F")


class BaseUblSpfe(models.AbstractModel):
    _inherit = "base.ubl"

    # -------------------------------------------------------------------------
    # SPFE UBL 2.5 INVOICE GENERATION (Anexo I)
    # -------------------------------------------------------------------------

    @api.model
    def spfe_generate_invoice_ubl_xml(self, move):
        """Generate and XSD-validate SPFE UBL 2.5 Invoice XML bytes."""
        move.ensure_one()
        move._check_spfe_invoice_ready()
        nsmap, ns = self._ubl_get_nsmap_namespace("Invoice-2", version="2.5")
        root = etree.Element("Invoice", nsmap=nsmap)

        self._spfe_add_invoice_header(move, root, ns)
        self._spfe_add_invoice_references(move, root, ns)
        self._spfe_add_invoice_annotations(move, root, ns)
        self._spfe_add_supplier_party(move, root, ns)
        self._spfe_add_customer_party(move, root, ns)
        self._spfe_add_payment_means_and_terms(move, root, ns)
        self._spfe_add_prepaid_and_exchange(move, root, ns)

        tax_summary = self._spfe_compute_tax_summary(move)
        self._spfe_add_tax_totals(move, tax_summary, root, ns)
        self._spfe_add_withholding_tax_total(move, tax_summary, root, ns)
        self._spfe_add_legal_monetary_total(move, tax_summary, root, ns)
        self._spfe_add_collection_invoice_lines(move, tax_summary, root, ns)
        self._spfe_add_invoice_lines(move, tax_summary, root, ns)

        xml_bytes = etree.tostring(
            root,
            xml_declaration=True,
            encoding="UTF-8",
            pretty_print=True,
        )
        self._ubl_check_xml_schema(xml_bytes, "Invoice", version="2.5")
        return xml_bytes

    @api.model
    def _spfe_add_invoice_header(self, move, root, ns):
        etree.SubElement(
            root, ns["cbc"] + "CustomizationID"
        ).text = SPFE_CUSTOMIZATION_ID
        etree.SubElement(root, ns["cbc"] + "ProfileID").text = SPFE_PROFILE_ID
        etree.SubElement(root, ns["cbc"] + "ID").text = move.name
        etree.SubElement(root, ns["cbc"] + "CopyIndicator").text = (
            "true" if move.spfe_copy_indicator else "false"
        )
        etree.SubElement(
            root, ns["cbc"] + "IssueDate"
        ).text = move.invoice_date.isoformat()
        due_date = move._get_spfe_due_date()
        if due_date:
            etree.SubElement(root, ns["cbc"] + "DueDate").text = due_date.isoformat()
        etree.SubElement(root, ns["cbc"] + "InvoiceTypeCode").text = (
            move.spfe_invoice_type or "380"
        )
        op_date = move.spfe_operation_date or getattr(move, "delivery_date", False)
        if op_date and op_date != move.invoice_date:
            etree.SubElement(
                root, ns["cbc"] + "TaxPointDate"
            ).text = op_date.isoformat()
        etree.SubElement(
            root,
            ns["cbc"] + "DocumentCurrencyCode",
            listID="ISO 4217 Alpha",
        ).text = move.currency_id.name
        if move.currency_id.name != "EUR":
            etree.SubElement(root, ns["cbc"] + "TaxCurrencyCode").text = "EUR"

    @api.model
    def _spfe_add_invoice_references(self, move, root, ns):
        if move.spfe_period_start_date and move.spfe_period_end_date:
            period = etree.SubElement(root, ns["cac"] + "InvoicePeriod")
            etree.SubElement(
                period, ns["cbc"] + "StartDate"
            ).text = move.spfe_period_start_date.isoformat()
            etree.SubElement(
                period, ns["cbc"] + "EndDate"
            ).text = move.spfe_period_end_date.isoformat()

        if move.invoice_origin:
            order_ref = etree.SubElement(root, ns["cac"] + "OrderReference")
            etree.SubElement(order_ref, ns["cbc"] + "ID").text = move.invoice_origin[
                :100
            ]

        rectified_moves = move._get_spfe_rectified_moves()
        for orig_move in rectified_moves:
            billing_ref = etree.SubElement(root, ns["cac"] + "BillingReference")
            inv_doc_ref = etree.SubElement(
                billing_ref, ns["cac"] + "InvoiceDocumentReference"
            )
            etree.SubElement(inv_doc_ref, ns["cbc"] + "ID").text = orig_move.name
            orig_date = orig_move.invoice_date or move.invoice_date
            etree.SubElement(
                inv_doc_ref, ns["cbc"] + "IssueDate"
            ).text = orig_date.isoformat()

        self._spfe_add_additional_doc_references(move, root, ns)

        if move.ref:
            buyer_ref_node = etree.SubElement(
                root, ns["cac"] + "BuyerAssignedReference"
            )
            etree.SubElement(
                buyer_ref_node, ns["cbc"] + "BuyerReference"
            ).text = move.ref[:100]

    @api.model
    def _spfe_add_additional_doc_references(self, move, root, ns):
        qr_url, qr_type = move._get_spfe_qr_info()
        if qr_url:
            doc_ref = etree.SubElement(root, ns["cac"] + "AdditionalDocumentReference")
            etree.SubElement(
                doc_ref, ns["cbc"] + "ID"
            ).text = f"{SPFE_SCHEMA_DOC_PREFIX}QR"
            etree.SubElement(doc_ref, ns["cbc"] + "UUID").text = qr_url
            etree.SubElement(doc_ref, ns["cbc"] + "DocumentDescription").text = (
                qr_type or "VERIFACTU"
            )

        auth_ref = move.company_id.spfe_billing_authorization_ref
        if auth_ref:
            doc_ref = etree.SubElement(root, ns["cac"] + "AdditionalDocumentReference")
            etree.SubElement(
                doc_ref, ns["cbc"] + "ID"
            ).text = f"{SPFE_SCHEMA_DOC_PREFIX}AUT"
            etree.SubElement(doc_ref, ns["cbc"] + "UUID").text = auth_ref
            auth_desc = move.company_id.spfe_billing_authorization_desc
            if auth_desc:
                etree.SubElement(
                    doc_ref, ns["cbc"] + "DocumentDescription"
                ).text = auth_desc

        if move.spfe_invoice_type in ("384", "471"):
            self._spfe_add_rectificativa_references(move, root, ns)

    @api.model
    def _spfe_add_rectificativa_references(self, move, root, ns):
        refund_type = move.spfe_refund_type or "R1"
        type_labels = dict(
            move._fields["spfe_refund_type"]._description_selection(self.env)
        )
        doc_tipo = etree.SubElement(root, ns["cac"] + "AdditionalDocumentReference")
        etree.SubElement(
            doc_tipo, ns["cbc"] + "ID"
        ).text = f"{SPFE_SCHEMA_DOC_PREFIX}RECT:TIPO"
        etree.SubElement(doc_tipo, ns["cbc"] + "DocumentTypeCode").text = refund_type
        etree.SubElement(
            doc_tipo, ns["cbc"] + "DocumentDescription"
        ).text = type_labels.get(refund_type, "Factura Rectificativa")

        refund_mode = move.spfe_refund_mode or "I"
        mode_labels = {
            "I": "Rectificativa por diferencias",
            "S": "Rectificativa por sustitución",
        }
        doc_mod = etree.SubElement(root, ns["cac"] + "AdditionalDocumentReference")
        etree.SubElement(
            doc_mod, ns["cbc"] + "ID"
        ).text = f"{SPFE_SCHEMA_DOC_PREFIX}RECT:MODALIDAD"
        etree.SubElement(doc_mod, ns["cbc"] + "DocumentTypeCode").text = refund_mode
        etree.SubElement(
            doc_mod, ns["cbc"] + "DocumentDescription"
        ).text = mode_labels.get(refund_mode, "Rectificativa")

        if refund_mode == "S":
            for code, val in (
                ("Base", move.spfe_rectified_base),
                ("Cuota", move.spfe_rectified_tax),
                ("CuotaRecargo", move.spfe_rectified_surcharge),
            ):
                if code in ("Base", "Cuota") or not float_is_zero(
                    val, precision_digits=2
                ):
                    doc_imp = etree.SubElement(
                        root, ns["cac"] + "AdditionalDocumentReference"
                    )
                    etree.SubElement(
                        doc_imp, ns["cbc"] + "ID"
                    ).text = f"{SPFE_SCHEMA_DOC_PREFIX}RECT:IMPORTES"
                    etree.SubElement(
                        doc_imp, ns["cbc"] + "DocumentTypeCode"
                    ).text = code
                    etree.SubElement(
                        doc_imp, ns["cbc"] + "DocumentDescription"
                    ).text = f"{val:.2f}"

    @api.model
    def _spfe_add_invoice_annotations(self, move, root, ns):
        if move.spfe_note:
            ann = etree.SubElement(root, ns["cac"] + "Annotation")
            if move.spfe_note_code:
                etree.SubElement(
                    ann, ns["cbc"] + "SubjectCode"
                ).text = move.spfe_note_code
            etree.SubElement(
                ann, ns["cbc"] + "AnnotationContent"
            ).text = move.spfe_note.strip()[:1000]

    @api.model
    def _spfe_add_postal_address(self, partner, parent_node, ns):
        address = etree.SubElement(parent_node, ns["cac"] + "PostalAddress")
        street = partner.street or partner.street2 or ""
        etree.SubElement(address, ns["cbc"] + "StreetName").text = street
        if partner.street and partner.street2:
            etree.SubElement(
                address, ns["cbc"] + "AdditionalStreetName"
            ).text = partner.street2
        if partner.city:
            etree.SubElement(address, ns["cbc"] + "CityName").text = partner.city
        if partner.zip:
            etree.SubElement(
                address, ns["cbc"] + "PostalZone"
            ).text = partner.zip.strip()
        if partner.state_id:
            etree.SubElement(
                address, ns["cbc"] + "CountrySubentity"
            ).text = partner.state_id.name
        country_node = etree.SubElement(address, ns["cac"] + "Country")
        etree.SubElement(
            country_node, ns["cbc"] + "IdentificationCode"
        ).text = partner.country_id.code

    @api.model
    def _spfe_add_party_node(
        self, partner, parent_node, ns, legal_form=False, third_party=False
    ):
        commercial = partner.commercial_partner_id
        party = etree.SubElement(parent_node, ns["cac"] + "Party")
        if commercial.website and commercial.website.startswith(
            ("http://", "https://")
        ):
            etree.SubElement(party, ns["cbc"] + "WebsiteURI").text = commercial.website

        self._spfe_add_postal_address(commercial, party, ns)

        scheme_id, tax_scheme_code, comp_id = commercial._get_spfe_party_tax_info()
        party_tax_scheme = etree.SubElement(party, ns["cac"] + "PartyTaxScheme")
        etree.SubElement(
            party_tax_scheme, ns["cbc"] + "CompanyID", schemeID=scheme_id
        ).text = comp_id
        tax_scheme = etree.SubElement(party_tax_scheme, ns["cac"] + "TaxScheme")
        etree.SubElement(tax_scheme, ns["cbc"] + "ID").text = tax_scheme_code

        legal_entity = etree.SubElement(party, ns["cac"] + "PartyLegalEntity")
        etree.SubElement(
            legal_entity, ns["cbc"] + "RegistrationName"
        ).text = commercial.name
        etree.SubElement(legal_entity, ns["cbc"] + "CompanyID").text = comp_id
        if legal_form:
            etree.SubElement(
                legal_entity, ns["cbc"] + "CompanyLegalForm"
            ).text = legal_form

        phone = partner.phone or commercial.phone
        email = partner.email or commercial.email
        if phone or email:
            contact = etree.SubElement(party, ns["cac"] + "Contact")
            etree.SubElement(contact, ns["cbc"] + "Name").text = commercial.name
            if phone:
                etree.SubElement(contact, ns["cbc"] + "Telephone").text = phone
            if email:
                etree.SubElement(contact, ns["cbc"] + "ElectronicMail").text = email

        if third_party:
            sp_node = etree.SubElement(party, ns["cac"] + "ServiceProviderParty")
            etree.SubElement(
                sp_node, ns["cbc"] + "ServiceTypeCode"
            ).text = "FacturaciónPorTercero"
            self._spfe_add_party_node(third_party, sp_node, ns)
        return party

    @api.model
    def _spfe_add_supplier_party(self, move, root, ns):
        supplier_root = etree.SubElement(root, ns["cac"] + "AccountingSupplierParty")
        third_party = (
            move.spfe_third_party_issuer_id
            or move.company_id.spfe_third_party_issuer_id
        )
        self._spfe_add_party_node(
            move.company_id.partner_id,
            supplier_root,
            ns,
            legal_form=move.company_id._get_spfe_legal_form_text(),
            third_party=third_party,
        )

    @api.model
    def _spfe_add_customer_party(self, move, root, ns):
        customer_root = etree.SubElement(root, ns["cac"] + "AccountingCustomerParty")
        self._spfe_add_party_node(move.partner_id, customer_root, ns)

    @api.model
    def _spfe_add_payment_means_and_terms(self, move, root, ns):
        means_code, iban = move._get_spfe_payment_means_info()
        if means_code:
            pay_means = etree.SubElement(root, ns["cac"] + "PaymentMeans")
            etree.SubElement(
                pay_means,
                ns["cbc"] + "PaymentMeansCode",
                listID="UN/ECE 4461",
            ).text = means_code
            if means_code in ("30", "49") and iban:
                fin_acc = etree.SubElement(
                    pay_means, ns["cac"] + "PayeeFinancialAccount"
                )
                etree.SubElement(fin_acc, ns["cbc"] + "ID", schemeID="IBAN").text = iban

        term_note = (
            move.invoice_payment_term_id.name or move.payment_mode_id.name or False
        )
        due_date = move._get_spfe_due_date()
        if term_note or due_date:
            pay_terms = etree.SubElement(root, ns["cac"] + "PaymentTerms")
            if term_note:
                etree.SubElement(pay_terms, ns["cbc"] + "Note").text = term_note
            etree.SubElement(
                pay_terms,
                ns["cbc"] + "Amount",
                currencyID=move.currency_id.name,
            ).text = f"{self._spfe_sign(move) * move.amount_total:.2f}"
            if due_date:
                etree.SubElement(
                    pay_terms, ns["cbc"] + "PaymentDueDate"
                ).text = due_date.isoformat()

    @api.model
    def _spfe_get_eur_exchange_rate(self, move):
        eur = self.env.ref("base.EUR", raise_if_not_found=False)
        if move.company_id.currency_id.name == "EUR" and not float_is_zero(
            move.amount_untaxed, precision_digits=2
        ):
            return abs(move.amount_untaxed_signed / move.amount_untaxed)
        if eur:
            return self.env["res.currency"]._get_conversion_rate(
                move.currency_id,
                eur,
                move.company_id,
                move.invoice_date or fields.Date.context_today(move),
            )
        return 1.0

    @api.model
    def _spfe_add_prepaid_and_exchange(self, move, root, ns):
        if move.spfe_prepaid_date:
            prepaid = etree.SubElement(root, ns["cac"] + "PrepaidPayment")
            etree.SubElement(
                prepaid, ns["cbc"] + "PaidDate"
            ).text = move.spfe_prepaid_date.isoformat()

        if move.currency_id.name != "EUR":
            exch = etree.SubElement(root, ns["cac"] + "TaxExchangeRate")
            etree.SubElement(
                exch, ns["cbc"] + "SourceCurrencyCode"
            ).text = move.currency_id.name
            etree.SubElement(exch, ns["cbc"] + "TargetCurrencyCode").text = "EUR"
            rate = self._spfe_get_eur_exchange_rate(move)
            etree.SubElement(exch, ns["cbc"] + "CalculationRate").text = f"{rate:.6f}"

    @api.model
    def _spfe_sign(self, move):
        """Return -1 for difference-based credit notes so UBL amounts are signed."""
        if move.move_type in ("out_refund", "in_refund") and (
            move.spfe_refund_mode != "S"
        ):
            return -1.0
        return 1.0

    @api.model
    def _spfe_accumulate_line_taxes(self, line, base_amt, vat_buckets, wth_buckets):
        vat_tax, req_tax, wth_taxes = line._get_spfe_split_taxes()
        categ_code = "N" if req_tax else (vat_tax.unece_categ_code or "S")
        percent = (
            0.0
            if categ_code in VATEX_ALLOWED_CATEGORIES
            else float_round(vat_tax.amount, precision_digits=2)
        )
        vatex_code = (
            vat_tax.unece_vatex_code
            if categ_code in VATEX_ALLOWED_CATEGORIES
            else False
        )
        vatex_reason = (
            (vat_tax.unece_vatex_id.name or vat_tax.invoice_legal_notes)
            if vatex_code
            else False
        )
        entry = vat_buckets.setdefault(
            (vat_tax.id, categ_code, percent, vatex_code or "", False),
            {
                "tax_id": vat_tax.id,
                "categ": categ_code,
                "percent": percent,
                "vatex_code": vatex_code,
                "vatex_reason": vatex_reason,
                "base": 0.0,
                "tax": 0.0,
                "is_surcharge": False,
            },
        )
        entry["base"] = float_round(entry["base"] + base_amt, precision_digits=2)

        if req_tax:
            req_pct = float_round(req_tax.amount, precision_digits=2)
            req_entry = vat_buckets.setdefault(
                (req_tax.id, "N", req_pct, "", True),
                {
                    "tax_id": req_tax.id,
                    "categ": "N",
                    "percent": req_pct,
                    "vatex_code": False,
                    "vatex_reason": False,
                    "base": 0.0,
                    "tax": 0.0,
                    "is_surcharge": True,
                },
            )
            req_entry["base"] = float_round(
                req_entry["base"] + base_amt, precision_digits=2
            )

        for wtax in wth_taxes:
            wpct = abs(float_round(wtax.amount, precision_digits=2))
            wcode = wtax.spfe_withholding_type or "01"
            wentry = wth_buckets.setdefault(
                (wtax.id, wcode, wpct),
                {
                    "tax_id": wtax.id,
                    "code": wcode,
                    "percent": wpct,
                    "base": 0.0,
                    "tax": 0.0,
                    "name": wtax.name,
                },
            )
            wentry["base"] = float_round(wentry["base"] + base_amt, precision_digits=2)

    @api.model
    def _spfe_assign_posted_tax_quotas(self, move, sign, vat_buckets, wth_buckets):
        """Populate exact posted tax quotas from accounting tax lines."""
        tax_lines = move.line_ids.filtered(
            lambda ln: ln.display_type == "tax" and ln.tax_line_id
        )
        quota_by_tax = {}
        for tline in tax_lines:
            tid = tline.tax_line_id.id
            quota_by_tax[tid] = float_round(
                quota_by_tax.get(tid, 0.0) + abs(tline.amount_currency),
                precision_digits=2,
            )

        by_tax = {}
        for bucket in vat_buckets.values():
            by_tax.setdefault(bucket["tax_id"], []).append(bucket)
        for tid, buckets in by_tax.items():
            target = float_round(sign * quota_by_tax.get(tid, 0.0), precision_digits=2)
            tot_base = sum(b["base"] for b in buckets)
            allocated = 0.0
            for idx, bucket in enumerate(buckets):
                if idx == len(buckets) - 1 or float_is_zero(tot_base, 2):
                    bucket["tax"] = float_round(target - allocated, precision_digits=2)
                else:
                    share = float_round(
                        target * (bucket["base"] / tot_base), precision_digits=2
                    )
                    bucket["tax"] = share
                    allocated = float_round(allocated + share, precision_digits=2)

        for wbucket in wth_buckets.values():
            wbucket["tax"] = quota_by_tax.get(wbucket["tax_id"], 0.0)

    @api.model
    def _spfe_merge_tax_buckets(self, vat_buckets, wth_buckets):
        vat_groups = {}
        for b in vat_buckets.values():
            gkey = (
                "N_REQ" if b["is_surcharge"] else b["categ"],
                b["percent"],
                b["vatex_code"] or "",
            )
            grp = vat_groups.setdefault(
                gkey,
                {
                    "categ": b["categ"],
                    "percent": b["percent"],
                    "vatex_code": b["vatex_code"],
                    "vatex_reason": b["vatex_reason"],
                    "base": 0.0,
                    "tax": 0.0,
                    "is_surcharge": b["is_surcharge"],
                },
            )
            grp["base"] = float_round(grp["base"] + b["base"], precision_digits=2)
            grp["tax"] = float_round(grp["tax"] + b["tax"], precision_digits=2)

        wth_groups = {}
        for wb in wth_buckets.values():
            wgrp = wth_groups.setdefault(
                (wb["code"], wb["percent"]),
                {
                    "code": wb["code"],
                    "percent": wb["percent"],
                    "base": 0.0,
                    "tax": 0.0,
                    "name": wb["name"],
                },
            )
            wgrp["base"] = float_round(wgrp["base"] + wb["base"], precision_digits=2)
            wgrp["tax"] = float_round(wgrp["tax"] + wb["tax"], precision_digits=2)
        return vat_groups, wth_groups

    @api.model
    def _spfe_build_collection_items(self, collection_lines, sign, wth_total):
        coll_items = []
        for cline in collection_lines:
            ctype = cline.spfe_collection_line_type
            camt = float_round(sign * cline.price_total, precision_digits=2)
            if ctype == "MINO" and camt > 0:
                camt = -camt
            coll_items.append(
                {
                    "code": ctype,
                    "amount": camt,
                    "description": cline.name or ctype,
                }
            )
        if not float_is_zero(wth_total, precision_digits=2):
            coll_items.append(
                {
                    "code": "RETE",
                    "amount": -sign * wth_total,
                    "description": "Retenciones practicadas",
                }
            )
        return coll_items

    @api.model
    def _spfe_compute_tax_summary(self, move):
        """Compute grouped VAT/RE subtotals, withholdings, and collection lines."""
        sign = self._spfe_sign(move)
        lines = move.invoice_line_ids.filtered(lambda ln: ln.display_type == "product")
        regular_lines = lines.filtered(lambda ln: not ln.spfe_collection_line_type)
        collection_lines = lines - regular_lines
        vat_buckets = {}
        wth_buckets = {}
        line_ext_total = 0.0

        for line in regular_lines:
            base_amt = float_round(sign * line.price_subtotal, precision_digits=2)
            line_ext_total = float_round(line_ext_total + base_amt, precision_digits=2)
            self._spfe_accumulate_line_taxes(line, base_amt, vat_buckets, wth_buckets)

        self._spfe_assign_posted_tax_quotas(move, sign, vat_buckets, wth_buckets)
        vat_groups, wth_groups = self._spfe_merge_tax_buckets(vat_buckets, wth_buckets)

        vat_total = float_round(
            sum(v["tax"] for v in vat_groups.values()), precision_digits=2
        )
        wth_total = float_round(
            sum(w["tax"] for w in wth_groups.values()), precision_digits=2
        )
        coll_items = self._spfe_build_collection_items(
            collection_lines, sign, wth_total
        )
        coll_sum = float_round(sum(c["amount"] for c in coll_items), precision_digits=2)
        tax_inclusive = float_round(line_ext_total + vat_total, precision_digits=2)
        return {
            "sign": sign,
            "regular_lines": regular_lines,
            "vat_subtotals": list(vat_groups.values()),
            "wth_subtotals": list(wth_groups.values()),
            "collection_items": coll_items,
            "line_extension_total": line_ext_total,
            "vat_total": vat_total,
            "wth_total": wth_total,
            "tax_inclusive_total": tax_inclusive,
            "payable_total": float_round(tax_inclusive + coll_sum, precision_digits=2),
        }

    @api.model
    def _spfe_add_tax_totals(self, move, summary, root, ns):
        curr = move.currency_id.name
        tax_total = etree.SubElement(root, ns["cac"] + "TaxTotal")
        etree.SubElement(
            tax_total, ns["cbc"] + "TaxAmount", currencyID=curr
        ).text = f"{summary['vat_total']:.2f}"

        for sub in summary["vat_subtotals"]:
            sub_node = etree.SubElement(tax_total, ns["cac"] + "TaxSubtotal")
            etree.SubElement(
                sub_node, ns["cbc"] + "TaxableAmount", currencyID=curr
            ).text = f"{sub['base']:.2f}"
            etree.SubElement(
                sub_node, ns["cbc"] + "TaxAmount", currencyID=curr
            ).text = f"{sub['tax']:.2f}"
            cat_node = etree.SubElement(sub_node, ns["cac"] + "TaxCategory")
            etree.SubElement(cat_node, ns["cbc"] + "ID").text = sub["categ"]
            etree.SubElement(cat_node, ns["cbc"] + "Percent").text = f"{sub['percent']}"
            if sub["vatex_code"]:
                etree.SubElement(
                    cat_node, ns["cbc"] + "TaxExemptionReasonCode"
                ).text = sub["vatex_code"]
                if sub["vatex_reason"]:
                    etree.SubElement(
                        cat_node, ns["cbc"] + "TaxExemptionReason"
                    ).text = sub["vatex_reason"][:500]
            scheme_node = etree.SubElement(cat_node, ns["cac"] + "TaxScheme")
            etree.SubElement(scheme_node, ns["cbc"] + "ID").text = "VAT"

        if curr != "EUR":
            rate = self._spfe_get_eur_exchange_rate(move)
            eur_vat = float_round(summary["vat_total"] * rate, precision_digits=2)
            tax_total_eur = etree.SubElement(root, ns["cac"] + "TaxTotal")
            etree.SubElement(
                tax_total_eur, ns["cbc"] + "TaxAmount", currencyID="EUR"
            ).text = f"{eur_vat:.2f}"

    @api.model
    def _spfe_add_withholding_tax_total(self, move, summary, root, ns):
        if not summary["wth_subtotals"]:
            return
        curr = move.currency_id.name
        wth_root = etree.SubElement(root, ns["cac"] + "WithholdingTaxTotal")
        etree.SubElement(
            wth_root, ns["cbc"] + "TaxAmount", currencyID=curr
        ).text = f"{summary['wth_total']:.2f}"
        for wsub in summary["wth_subtotals"]:
            sub_node = etree.SubElement(wth_root, ns["cac"] + "TaxSubtotal")
            etree.SubElement(
                sub_node, ns["cbc"] + "TaxableAmount", currencyID=curr
            ).text = f"{wsub['base']:.2f}"
            etree.SubElement(
                sub_node, ns["cbc"] + "TaxAmount", currencyID=curr
            ).text = f"{wsub['tax']:.2f}"
            cat_node = etree.SubElement(sub_node, ns["cac"] + "TaxCategory")
            etree.SubElement(cat_node, ns["cbc"] + "ID").text = "S"
            etree.SubElement(
                cat_node, ns["cbc"] + "Percent"
            ).text = f"{wsub['percent']}"
            scheme_node = etree.SubElement(cat_node, ns["cac"] + "TaxScheme")
            etree.SubElement(scheme_node, ns["cbc"] + "ID").text = "WTH"
            etree.SubElement(scheme_node, ns["cbc"] + "TaxTypeCode").text = wsub["code"]

    @api.model
    def _spfe_add_legal_monetary_total(self, move, summary, root, ns):
        curr = move.currency_id.name
        lmt = etree.SubElement(root, ns["cac"] + "LegalMonetaryTotal")
        etree.SubElement(
            lmt, ns["cbc"] + "LineExtensionAmount", currencyID=curr
        ).text = f"{summary['line_extension_total']:.2f}"
        etree.SubElement(
            lmt, ns["cbc"] + "TaxExclusiveAmount", currencyID=curr
        ).text = f"{summary['line_extension_total']:.2f}"
        etree.SubElement(
            lmt, ns["cbc"] + "TaxInclusiveAmount", currencyID=curr
        ).text = f"{summary['tax_inclusive_total']:.2f}"
        etree.SubElement(
            lmt, ns["cbc"] + "PayableAmount", currencyID=curr
        ).text = f"{summary['payable_total']:.2f}"

    @api.model
    def _spfe_add_collection_invoice_lines(self, move, summary, root, ns):
        curr = move.currency_id.name
        for item in summary["collection_items"]:
            cline = etree.SubElement(root, ns["cac"] + "CollectionInvoiceLine")
            etree.SubElement(
                cline, ns["cbc"] + "ID"
            ).text = f"{SPFE_SCHEMA_ADD_PREFIX}{item['code']}"
            etree.SubElement(
                cline,
                ns["cbc"] + "TaxInclusiveLineExtensionAmount",
                currencyID=curr,
            ).text = f"{item['amount']:.2f}"
            item_node = etree.SubElement(cline, ns["cac"] + "Item")
            etree.SubElement(item_node, ns["cbc"] + "Description").text = item[
                "description"
            ][:500]

    @api.model
    def _spfe_add_invoice_lines(self, move, summary, root, ns):
        curr = move.currency_id.name
        sign = summary["sign"]
        for idx, line in enumerate(summary["regular_lines"], start=1):
            inv_line = etree.SubElement(root, ns["cac"] + "InvoiceLine")
            etree.SubElement(inv_line, ns["cbc"] + "ID").text = str(idx)

            uom_code = line.product_uom_id.unece_code or "EA"
            qty = sign * line.quantity
            qty_digits = self.env["decimal.precision"].precision_get("Product Unit")
            etree.SubElement(
                inv_line, ns["cbc"] + "InvoicedQuantity", unitCode=uom_code
            ).text = float_repr(qty, qty_digits)

            line_ext = float_round(sign * line.price_subtotal, precision_digits=2)
            etree.SubElement(
                inv_line, ns["cbc"] + "LineExtensionAmount", currencyID=curr
            ).text = f"{line_ext:.2f}"

            unit_price_excl = self._spfe_get_line_unit_price(
                line, inv_line, curr, qty, line_ext, ns
            )
            self._spfe_add_line_item(line, inv_line, ns)

            price_node = etree.SubElement(inv_line, ns["cac"] + "Price")
            etree.SubElement(
                price_node, ns["cbc"] + "PriceAmount", currencyID=curr
            ).text = (
                f"{unit_price_excl:.4f}".rstrip("0").rstrip(".")
                if (
                    "." in f"{unit_price_excl:.4f}"
                    and len(f"{unit_price_excl:.4f}".rstrip("0").split(".")[1]) > 2
                )
                else f"{unit_price_excl:.2f}"
            )

    @api.model
    def _spfe_get_line_unit_price(self, line, inv_line, curr, qty, line_ext, ns):
        """Add AllowanceCharge if discounted and return coherent PriceAmount."""
        if float_is_zero(qty, precision_digits=4):
            return abs(line.price_unit)
        if line.discount and line.discount > 0:
            if any(t.price_include for t in line.tax_ids):
                tax_res = line.tax_ids.compute_all(
                    line.price_unit,
                    currency=line.currency_id,
                    quantity=1.0,
                    product=line.product_id,
                    partner=line.move_id.partner_id,
                )
                gross_unit = abs(tax_res["total_excluded"])
            else:
                gross_unit = abs(line.price_unit)
            gross_total = float_round(qty * gross_unit, precision_digits=2)
            disc_amt = float_round(gross_total - line_ext, precision_digits=2)
            if not float_is_zero(disc_amt, precision_digits=2):
                allow = etree.SubElement(inv_line, ns["cac"] + "AllowanceCharge")
                etree.SubElement(allow, ns["cbc"] + "ChargeIndicator").text = "false"
                etree.SubElement(
                    allow, ns["cbc"] + "AllowanceChargeReason"
                ).text = self.env._("Discount")
                etree.SubElement(
                    allow, ns["cbc"] + "Amount", currencyID=curr
                ).text = f"{disc_amt:.2f}"
                etree.SubElement(
                    allow, ns["cbc"] + "BaseAmount", currencyID=curr
                ).text = f"{gross_total:.2f}"
                return gross_unit
        return abs(float_round(line_ext / qty, precision_digits=6))

    @api.model
    def _spfe_add_line_item(self, line, inv_line, ns):
        item_node = etree.SubElement(inv_line, ns["cac"] + "Item")
        desc = (line.name or line.product_id.display_name or "-").strip()
        item_name = (
            line.product_id.name if line.product_id else desc.split("\n")[0]
        ).strip()
        etree.SubElement(item_node, ns["cbc"] + "Description").text = desc[:1000]
        etree.SubElement(item_node, ns["cbc"] + "Name").text = item_name[:200]

        vat_tax, req_tax, _wth_taxes = line._get_spfe_split_taxes()
        categ_code = "N" if req_tax else (vat_tax.unece_categ_code or "S")
        percent = (
            0.0
            if categ_code in VATEX_ALLOWED_CATEGORIES
            else float_round(vat_tax.amount, precision_digits=2)
        )
        cat_node = etree.SubElement(item_node, ns["cac"] + "ClassifiedTaxCategory")
        etree.SubElement(cat_node, ns["cbc"] + "ID").text = categ_code
        etree.SubElement(cat_node, ns["cbc"] + "Percent").text = f"{percent}"
        if categ_code in VATEX_ALLOWED_CATEGORIES and vat_tax.unece_vatex_code:
            etree.SubElement(
                cat_node, ns["cbc"] + "TaxExemptionReasonCode"
            ).text = vat_tax.unece_vatex_code
        scheme_node = etree.SubElement(cat_node, ns["cac"] + "TaxScheme")
        etree.SubElement(scheme_node, ns["cbc"] + "ID").text = "VAT"

        reg_keys = line._get_spfe_effective_registration_keys()
        for reg_key in reg_keys:
            prop = etree.SubElement(item_node, ns["cac"] + "AdditionalItemProperty")
            etree.SubElement(
                prop, ns["cbc"] + "Name"
            ).text = f"{SPFE_SCHEMA_LINE_PREFIX}REGI"
            etree.SubElement(prop, ns["cbc"] + "Value").text = reg_key.code
            etree.SubElement(
                prop, ns["cbc"] + "ValueQualifier"
            ).text = reg_key.tax_qualifier

        cadastral_ref, prop_sit = line._get_spfe_real_estate_info()
        if prop_sit:
            prop = etree.SubElement(item_node, ns["cac"] + "AdditionalItemProperty")
            etree.SubElement(
                prop, ns["cbc"] + "Name"
            ).text = f"{SPFE_SCHEMA_LINE_PREFIX}RCAT"
            etree.SubElement(prop, ns["cbc"] + "Value").text = (
                "-" if prop_sit in ("03", "04") else (cadastral_ref or "-")
            )
            etree.SubElement(prop, ns["cbc"] + "ValueQualifier").text = prop_sit

        if line.spfe_line_info:
            prop = etree.SubElement(item_node, ns["cac"] + "AdditionalItemProperty")
            etree.SubElement(
                prop, ns["cbc"] + "Name"
            ).text = f"{SPFE_SCHEMA_LINE_PREFIX}INFO"
            etree.SubElement(prop, ns["cbc"] + "Value").text = line.spfe_line_info[:500]

    # -------------------------------------------------------------------------
    # SPFE UBL 2.5 APPLICATION RESPONSE GENERATION (Cancel, Query, Download, Anexo II)
    # -------------------------------------------------------------------------

    @api.model
    def _spfe_init_application_response(self, comm_id, issue_date=None):
        nsmap, ns = self._ubl_get_nsmap_namespace(
            "ApplicationResponse-2", version="2.5"
        )
        root = etree.Element("ApplicationResponse", nsmap=nsmap)
        etree.SubElement(root, ns["cbc"] + "ID").text = comm_id
        etree.SubElement(root, ns["cbc"] + "IssueDate").text = (
            issue_date or fields.Date.context_today(self)
        ).isoformat()
        etree.SubElement(root, ns["cac"] + "SenderParty")
        etree.SubElement(root, ns["cac"] + "ReceiverParty")
        return root, ns

    @api.model
    def _spfe_append_doc_reference(
        self, parent, ns, inv_number, inv_date, issuer_vat, issuer_name
    ):
        doc_ref = etree.SubElement(parent, ns["cac"] + "DocumentReference")
        etree.SubElement(doc_ref, ns["cbc"] + "ID").text = inv_number
        etree.SubElement(doc_ref, ns["cbc"] + "IssueDate").text = fields.Date.to_date(
            inv_date
        ).isoformat()
        etree.SubElement(doc_ref, ns["cbc"] + "DocumentType").text = "Invoice"
        issuer = etree.SubElement(doc_ref, ns["cac"] + "IssuerParty")
        pts = etree.SubElement(issuer, ns["cac"] + "PartyTaxScheme")
        etree.SubElement(pts, ns["cbc"] + "CompanyID").text = issuer_vat
        etree.SubElement(pts, ns["cac"] + "TaxScheme")
        ple = etree.SubElement(issuer, ns["cac"] + "PartyLegalEntity")
        etree.SubElement(ple, ns["cbc"] + "RegistrationName").text = issuer_name
        return doc_ref

    @api.model
    def spfe_generate_cancel_response_xml(self, move, effective_date=None, reason=None):
        move.ensure_one()
        today = fields.Date.context_today(self)
        root, ns = self._spfe_init_application_response(
            f"VOID-{today.strftime('%Y%m%d')}-{move.id}"
        )
        doc_resp = etree.SubElement(root, ns["cac"] + "DocumentResponse")
        resp = etree.SubElement(doc_resp, ns["cac"] + "Response")
        etree.SubElement(resp, ns["cbc"] + "ResponseCode").text = "CANCELINVOICE"
        if reason:
            etree.SubElement(resp, ns["cbc"] + "Description").text = reason[:500]
        etree.SubElement(resp, ns["cbc"] + "EffectiveDate").text = (
            effective_date or today
        ).isoformat()

        _s, _t, issuer_vat = move.company_id.partner_id._get_spfe_party_tax_info()
        self._spfe_append_doc_reference(
            doc_resp,
            ns,
            move.name,
            move.invoice_date,
            issuer_vat,
            move.company_id.partner_id.commercial_partner_id.name,
        )
        xml_bytes = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )
        self._ubl_check_xml_schema(xml_bytes, "ApplicationResponse", version="2.5")
        return xml_bytes

    @api.model
    def spfe_generate_query_or_download_by_id_xml(self, response_code, doc_refs):
        """Build QUERYBYID or DOWNLOADBYID ApplicationResponse XML."""
        today = fields.Date.context_today(self)
        root, ns = self._spfe_init_application_response(
            f"{response_code}-{today.strftime('%Y%m%d')}"
        )
        doc_resp = etree.SubElement(root, ns["cac"] + "DocumentResponse")
        resp = etree.SubElement(doc_resp, ns["cac"] + "Response")
        etree.SubElement(resp, ns["cbc"] + "ResponseCode").text = response_code
        etree.SubElement(resp, ns["cbc"] + "Description").text = f"SPFE {response_code}"
        for ref in doc_refs:
            self._spfe_append_doc_reference(
                doc_resp,
                ns,
                ref["id"],
                ref["issue_date"],
                ref["issuer_vat"],
                ref["issuer_name"],
            )
        xml_bytes = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )
        self._ubl_check_xml_schema(xml_bytes, "ApplicationResponse", version="2.5")
        return xml_bytes

    @api.model
    def spfe_generate_download_by_loc_xml(self, locators):
        """Build DOWNLOADBYLOC ApplicationResponse XML."""
        today = fields.Date.context_today(self)
        root, ns = self._spfe_init_application_response(
            f"DOWNLOADLOC-{today.strftime('%Y%m%d')}"
        )
        doc_resp = etree.SubElement(root, ns["cac"] + "DocumentResponse")
        resp = etree.SubElement(doc_resp, ns["cac"] + "Response")
        etree.SubElement(resp, ns["cbc"] + "ResponseCode").text = "DOWNLOADBYLOC"
        etree.SubElement(
            resp, ns["cbc"] + "Description"
        ).text = "Solicitud de descarga por localizador"
        for loc in locators:
            doc_ref = etree.SubElement(doc_resp, ns["cac"] + "DocumentReference")
            etree.SubElement(doc_ref, ns["cbc"] + "ID").text = loc
        xml_bytes = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )
        self._ubl_check_xml_schema(xml_bytes, "ApplicationResponse", version="2.5")
        return xml_bytes

    @api.model
    def spfe_generate_invoice_events_xml(self, comm_prefix, events):
        """Build Anexo II Customer or Supplier Invoice Events ApplicationResponse."""
        today = fields.Date.context_today(self)
        root, ns = self._spfe_init_application_response(
            f"{comm_prefix}-{today.strftime('%Y%m%d')}"
        )
        for ev in events:
            doc_resp = etree.SubElement(root, ns["cac"] + "DocumentResponse")
            resp = etree.SubElement(doc_resp, ns["cac"] + "Response")
            code = ev["response_code"]
            etree.SubElement(resp, ns["cbc"] + "ResponseCode").text = code
            if ev.get("effective_date") and code in (
                "PAYMENT",
                "REJECTION",
                "SETTLEMENT",
                "DEFAULT",
            ):
                etree.SubElement(
                    resp, ns["cbc"] + "EffectiveDate"
                ).text = fields.Date.to_date(ev["effective_date"]).isoformat()

            self._spfe_add_event_statuses(resp, ns, code, ev)
            self._spfe_append_doc_reference(
                doc_resp,
                ns,
                ev["id"],
                ev["issue_date"],
                ev["issuer_vat"],
                ev["issuer_name"],
            )
        xml_bytes = etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", pretty_print=True
        )
        self._ubl_check_xml_schema(xml_bytes, "ApplicationResponse", version="2.5")
        return xml_bytes

    @api.model
    def _spfe_add_event_statuses(self, resp, ns, code, ev):
        if code == "REJECTION" and ev.get("rejection_reason"):
            st = etree.SubElement(resp, ns["cac"] + "Status")
            etree.SubElement(st, ns["cbc"] + "ConditionCode").text = ev[
                "rejection_reason"
            ]
            return

        if code not in ("PAYMENT", "SETTLEMENT", "DEFAULT"):
            return

        for attr_id, key in (
            ("DueDate", "due_date"),
            ("ShipmentDate", "shipment_date"),
            ("ReceptionDate", "reception_date"),
        ):
            if ev.get(key) and (code != "DEFAULT" or attr_id != "DueDate"):
                st = etree.SubElement(resp, ns["cac"] + "Status")
                etree.SubElement(
                    st, ns["cbc"] + "ReferenceDate"
                ).text = fields.Date.to_date(ev[key]).isoformat()
                cond = etree.SubElement(st, ns["cac"] + "Condition")
                etree.SubElement(cond, ns["cbc"] + "AttributeID").text = attr_id

        if code == "PAYMENT":
            for flag, reason_val in (
                ("is_corrected_invoice", "CorrectedInvoice"),
                ("is_negative_invoice", "NegativeAmountInvoice"),
            ):
                if ev.get(flag):
                    st = etree.SubElement(resp, ns["cac"] + "Status")
                    etree.SubElement(st, ns["cbc"] + "StatusReason").text = reason_val
        elif code == "SETTLEMENT" and ev.get("financing_arrangement"):
            st = etree.SubElement(resp, ns["cac"] + "Status")
            cond = etree.SubElement(st, ns["cac"] + "Condition")
            etree.SubElement(
                cond, ns["cbc"] + "AttributeID"
            ).text = "FinancingArrangement"

    # -------------------------------------------------------------------------
    # SPFE UBL 2.5 PARSING (DocumentStatus & Downloaded Invoice)
    # -------------------------------------------------------------------------

    @api.model
    def spfe_parse_document_status_xml(self, xml_bytes):
        """Parse SPFE UBL DocumentStatus XML into a structured Python dict."""
        root = etree.fromstring(xml_bytes)
        _nsmap, ns_braced = self._ubl_get_nsmap_namespace("DocumentStatus-2")
        ns = {k: v.strip("{}") for k, v in ns_braced.items()}
        doc_id = self._spfe_xpath_text(root, "cbc:ID", ns)
        resp_code = self._spfe_xpath_text(
            root,
            "cac:DocumentResponse/cac:Response/cbc:ResponseCode"
            " | cac:DocumentResponse/cac:Response/cac:Status/cbc:StatusReasonCode",
            ns,
        )
        resp_desc = self._spfe_xpath_text(
            root,
            "cac:DocumentResponse/cac:Response/cbc:Description"
            " | cac:DocumentResponse/cac:Response/cac:Status/cbc:StatusReason",
            ns,
        )
        seq_id = self._spfe_xpath_text(
            root,
            "cac:DocumentResponse/cac:Response/cac:Status/cbc:SequenceID",
            ns,
        )

        items = []
        for ref in root.xpath(
            "cac:DocumentResponse/cac:DocumentReference", namespaces=ns
        ):
            ref_id = self._spfe_xpath_text(ref, "cbc:ID", ns)
            if not ref_id:
                continue
            items.append(
                {
                    "id": ref_id,
                    "issue_date": self._spfe_xpath_text(ref, "cbc:IssueDate", ns),
                    "locator": self._spfe_xpath_text(
                        ref, "cbc:ReferencedDocumentInternalAddress", ns
                    ),
                    "status_code": self._spfe_xpath_text(
                        ref, "cbc:DocumentStatusCode", ns
                    )
                    or resp_code,
                    "description": self._spfe_xpath_text(
                        ref, "cbc:DocumentDescription", ns
                    ),
                    "issuer_vat": self._spfe_xpath_text(
                        ref,
                        "cac:IssuerParty/cac:PartyTaxScheme/cbc:CompanyID",
                        ns,
                    ),
                }
            )

        for add_resp in root.xpath("cac:AdditionalDocumentResponse", namespaces=ns):
            state_code = self._spfe_xpath_text(
                add_resp, "cac:Response/cbc:ResponseCode", ns
            )
            for ref in add_resp.xpath("cac:DocumentReference", namespaces=ns):
                items.append(
                    {
                        "id": self._spfe_xpath_text(ref, "cbc:ID", ns),
                        "issue_date": self._spfe_xpath_text(ref, "cbc:IssueDate", ns),
                        "locator": self._spfe_xpath_text(
                            ref, "cbc:ReferencedDocumentInternalAddress", ns
                        ),
                        "status_code": state_code,
                        "description": state_code or "",
                        "issuer_vat": self._spfe_xpath_text(
                            ref,
                            "cac:IssuerParty/cac:PartyTaxScheme/cbc:CompanyID",
                            ns,
                        ),
                    }
                )

        return {
            "id": doc_id,
            "response_code": resp_code,
            "description": resp_desc or "",
            "sequence_id": seq_id,
            "items": items,
        }

    @api.model
    def _spfe_parse_ubl_invoice_line(
        self, line_node, ns, company, sign, inv_id, wth_taxes=None
    ):
        qty = sign * float(
            self._spfe_xpath_text(line_node, "cbc:InvoicedQuantity", ns) or "1"
        )
        line_ext = sign * float(
            self._spfe_xpath_text(line_node, "cbc:LineExtensionAmount", ns) or "0"
        )
        raw_price = float(
            self._spfe_xpath_text(line_node, "cac:Price/cbc:PriceAmount", ns) or "0"
        )
        has_qty = not float_is_zero(qty, precision_digits=4)
        price_unit = line_ext / qty if has_qty else raw_price
        name = (
            self._spfe_xpath_text(line_node, "cac:Item/cbc:Description", ns)
            or self._spfe_xpath_text(line_node, "cac:Item/cbc:Name", ns)
            or inv_id
        )
        pct = float(
            self._spfe_xpath_text(
                line_node, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent", ns
            )
            or "0"
        )
        categ = self._spfe_xpath_text(
            line_node, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID", ns
        )
        taxes = self._spfe_match_purchase_tax(company, categ, pct)
        if wth_taxes and not float_is_zero(line_ext, precision_digits=2):
            taxes |= wth_taxes
        return (
            0,
            0,
            {
                "name": name,
                "quantity": qty if has_qty else 1.0,
                "price_unit": price_unit,
                "tax_ids": [(6, 0, taxes.ids)] if taxes else [],
            },
        )

    @api.model
    def _spfe_parse_ubl_withholding_taxes(self, root, ns, company):
        wth_taxes = self.env["account.tax"]
        for wsub in root.xpath(
            "cac:WithholdingTaxTotal/cac:TaxSubtotal", namespaces=ns
        ):
            wpct = float(
                self._spfe_xpath_text(wsub, "cac:TaxCategory/cbc:Percent", ns) or "0"
            )
            if float_is_zero(wpct, precision_digits=2):
                continue
            wcode = self._spfe_xpath_text(
                wsub, "cac:TaxCategory/cac:TaxScheme/cbc:TaxTypeCode", ns
            )
            wtax = self._spfe_match_purchase_withholding_tax(company, wpct, wcode)
            if wtax:
                wth_taxes |= wtax
        return wth_taxes

    @api.model
    def spfe_parse_invoice_ubl_to_move_vals(self, xml_bytes, company):
        """Parse a downloaded SPFE UBL Invoice into Odoo vendor bill create vals."""
        root = etree.fromstring(xml_bytes)
        _nsmap, ns_braced = self._ubl_get_nsmap_namespace("Invoice-2")
        ns = {k: v.strip("{}") for k, v in ns_braced.items()}
        inv_id = self._spfe_xpath_text(root, "cbc:ID", ns)
        issue_date = self._spfe_xpath_text(root, "cbc:IssueDate", ns)
        due_date = self._spfe_xpath_text(root, "cbc:DueDate", ns)
        inv_type = self._spfe_xpath_text(root, "cbc:InvoiceTypeCode", ns) or "380"
        curr_code = self._spfe_xpath_text(root, "cbc:DocumentCurrencyCode", ns) or "EUR"

        supp_nodes = root.xpath("cac:AccountingSupplierParty", namespaces=ns)
        partner = self._spfe_find_or_create_supplier(
            supp_nodes[0] if supp_nodes else None, ns, company
        )
        currency = (
            self.env["res.currency"].search([("name", "=", curr_code)], limit=1)
            or company.currency_id
        )
        payable_txt = self._spfe_xpath_text(
            root, "cac:LegalMonetaryTotal/cbc:PayableAmount", ns
        )
        is_refund = inv_type in ("384", "471") and (float(payable_txt or "0") < 0)
        move_type = "in_refund" if is_refund else "in_invoice"
        sign = -1.0 if is_refund else 1.0
        wth_taxes = self._spfe_parse_ubl_withholding_taxes(root, ns, company)

        line_vals = [
            self._spfe_parse_ubl_invoice_line(
                ln_node, ns, company, sign, inv_id, wth_taxes=wth_taxes
            )
            for ln_node in root.xpath("cac:InvoiceLine", namespaces=ns)
        ]

        valid_types = ("380", "384", "388", "389", "471")
        return {
            "company_id": company.id,
            "move_type": move_type,
            "partner_id": partner.id,
            "ref": inv_id,
            "invoice_date": issue_date,
            "invoice_date_due": due_date or issue_date,
            "currency_id": currency.id,
            "spfe_invoice_type": inv_type if inv_type in valid_types else "380",
            "invoice_line_ids": line_vals,
        }

    @api.model
    def _spfe_find_or_create_supplier(self, supp_node, ns, company):
        if supp_node is None:
            return company.partner_id
        partner_dict = self.ubl_parse_supplier_party(supp_node, ns)
        reg_name = self._spfe_xpath_text(
            supp_node,
            "cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
            ns,
        )
        vat = (partner_dict.get("vat") or "").strip().upper()
        country_code = partner_dict.get("country_code") or "ES"
        if vat:
            candidates = [vat]
            if country_code == "ES" and not vat.startswith("ES"):
                candidates.append(f"ES{vat}")
            found = self.env["res.partner"].search(
                [
                    ("vat", "in", candidates),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )
            if found:
                return found.commercial_partner_id
        country = self.env["res.country"].search([("code", "=", country_code)], limit=1)
        norm_vat = (
            f"ES{vat}"
            if (country_code == "ES" and vat and not vat.startswith("ES"))
            else vat
        )
        return self.env["res.partner"].create(
            {
                "name": (
                    reg_name or partner_dict.get("name") or vat or "SPFE Supplier"
                ),
                "is_company": True,
                "vat": norm_vat,
                "street": partner_dict.get("street"),
                "city": partner_dict.get("city"),
                "zip": partner_dict.get("zip"),
                "country_id": country.id if country else False,
                "email": partner_dict.get("email"),
                "phone": partner_dict.get("phone"),
            }
        )

    @api.model
    def _spfe_match_purchase_tax(self, company, categ, percent):
        """Return a purchase tax only when unambiguously matched (never at random)."""
        domain = [
            ("company_id", "=", company.id),
            ("type_tax_use", "=", "purchase"),
            ("amount_type", "=", "percent"),
            ("amount", "=", percent),
            ("spfe_is_surcharge", "=", False),
            ("spfe_is_withholding", "=", False),
        ]
        if categ:
            exact = self.env["account.tax"].search(
                domain + [("unece_categ_code", "=", categ)], limit=2
            )
            if len(exact) == 1:
                return exact
        candidates = self.env["account.tax"].search(domain, limit=2)
        return candidates if len(candidates) == 1 else self.env["account.tax"]

    @api.model
    def _spfe_match_purchase_withholding_tax(self, company, percent, wth_code=False):
        domain = [
            ("company_id", "=", company.id),
            ("type_tax_use", "=", "purchase"),
            ("amount_type", "=", "percent"),
            ("amount", "=", -abs(percent)),
        ]
        if wth_code:
            exact = self.env["account.tax"].search(
                domain + [("spfe_withholding_type", "=", wth_code)], limit=2
            )
            if len(exact) == 1:
                return exact
        candidates = self.env["account.tax"].search(domain, limit=2)
        return candidates if len(candidates) == 1 else self.env["account.tax"]

    @api.model
    def _spfe_xpath_text(self, node, expr, ns):
        res = node.xpath(expr, namespaces=ns)
        if res and res[0].text:
            return res[0].text.strip()
        return False
