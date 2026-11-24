# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools import mute_logger

from ..hooks import post_init_hook
from ..models.base_ubl import SPFE_CUSTOMIZATION_ID, SPFE_PROFILE_ID
from .common import SpfeTestCommon

UBL_NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


class TestSpfeUblInvoice(SpfeTestCommon):
    def test_01_standard_b2b_invoice_ubl_25(self):
        """Standard 21% IVA invoice generates valid UBL 2.5 with SPFE Anexo I nodes."""
        inv = self._create_spfe_invoice(
            spfe_qr_url=(
                "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/"
                "ValidarQR?nif=B12345674&numserie=INV001"
                "&fecha=20-10-2026&importe=242.00"
            ),
            spfe_note="Operación sujeta a normativa española",
        )
        inv.action_post()
        xml_bytes = inv._generate_and_attach_spfe_ubl()
        self.assertTrue(inv.spfe_ubl_attachment_id)

        root = etree.fromstring(xml_bytes)
        self.assertEqual(
            root.findtext("cbc:CustomizationID", namespaces=UBL_NS),
            SPFE_CUSTOMIZATION_ID,
        )
        self.assertEqual(
            root.findtext("cbc:ProfileID", namespaces=UBL_NS),
            SPFE_PROFILE_ID,
        )
        self.assertEqual(root.findtext("cbc:InvoiceTypeCode", namespaces=UBL_NS), "380")
        self.assertEqual(root.findtext("cbc:CopyIndicator", namespaces=UBL_NS), "false")
        # Supplier & Customer Spanish NIF LOC/FC mapping
        supp_id = root.xpath(
            "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
            namespaces=UBL_NS,
        )[0]
        self.assertEqual(supp_id.text, "B12345674")
        self.assertEqual(supp_id.get("schemeID"), "FC")
        self.assertEqual(
            root.findtext(
                "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/"
                "cac:TaxScheme/cbc:ID",
                namespaces=UBL_NS,
            ),
            "LOC",
        )
        # QR Fiscal AdditionalDocumentReference
        qr_uuid = root.xpath(
            "cac:AdditionalDocumentReference"
            "[cbc:ID='urn:aeat:names:specification:schema:QR']/cbc:UUID",
            namespaces=UBL_NS,
        )
        self.assertEqual(len(qr_uuid), 1)
        # Line REGI property
        regi_prop = root.xpath(
            "cac:InvoiceLine/cac:Item/cac:AdditionalItemProperty"
            "[cbc:Name='urn:aeat:names:specification:schema:lin:REGI']",
            namespaces=UBL_NS,
        )
        self.assertEqual(len(regi_prop), 1)
        self.assertEqual(regi_prop[0].findtext("cbc:Value", namespaces=UBL_NS), "01")
        self.assertEqual(
            regi_prop[0].findtext("cbc:ValueQualifier", namespaces=UBL_NS),
            "IVA",
        )
        # Totals
        self.assertEqual(
            root.findtext(
                "cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount",
                namespaces=UBL_NS,
            ),
            "200.00",
        )
        self.assertEqual(
            root.findtext(
                "cac:LegalMonetaryTotal/cbc:PayableAmount",
                namespaces=UBL_NS,
            ),
            "242.00",
        )

    def test_02_equivalence_surcharge_and_irpf_withholding(self):
        """Recargo equivalencia (N) + IRPF (WithholdingTaxTotal & RETE)."""
        inv = self._create_spfe_invoice(
            lines=[
                {
                    "product_id": self.product.id,
                    "name": "Mercancía con RE y retención",
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "discount": 10.0,
                    "tax_ids": [
                        Command.set(
                            (self.tax_iva21 | self.tax_req52 | self.tax_irpf15).ids
                        )
                    ],
                }
            ]
        )
        inv.action_post()
        xml_bytes = self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv)
        root = etree.fromstring(xml_bytes)

        # Base = 90.00, IVA 21% = 18.90, RE 5.2% = 4.68 -> VAT total = 23.58
        # IRPF 15% = 13.50 -> TaxInclusive = 113.58, Payable = 113.58 - 13.50 = 100.08
        subtotals = root.xpath("cac:TaxTotal/cac:TaxSubtotal", namespaces=UBL_NS)
        self.assertEqual(len(subtotals), 2)
        for st in subtotals:
            self.assertEqual(
                st.findtext("cac:TaxCategory/cbc:ID", namespaces=UBL_NS), "N"
            )
        self.assertEqual(
            root.findtext("cac:WithholdingTaxTotal/cbc:TaxAmount", namespaces=UBL_NS),
            "13.50",
        )
        rete_amt = root.xpath(
            "cac:CollectionInvoiceLine"
            "[cbc:ID='urn:aeat:names:specification:schema:add:RETE']/"
            "cbc:TaxInclusiveLineExtensionAmount",
            namespaces=UBL_NS,
        )
        self.assertEqual(len(rete_amt), 1)
        self.assertEqual(rete_amt[0].text, "-13.50")
        self.assertEqual(
            root.findtext(
                "cac:LegalMonetaryTotal/cbc:PayableAmount", namespaces=UBL_NS
            ),
            "100.08",
        )

    def test_03_credit_note_rectificativa_and_validations(self):
        """Credit note (384) populates BillingReference, RECT:TIPO, RECT:MODALIDAD."""
        orig = self._create_spfe_invoice()
        orig.action_post()

        refund = self._create_spfe_invoice(
            move_type="out_refund",
            reversed_entry_id=orig.id,
            spfe_refund_type="R1",
            spfe_refund_mode="I",
        )
        refund.action_post()
        xml_bytes = self.env["base.ubl"].spfe_generate_invoice_ubl_xml(refund)
        root = etree.fromstring(xml_bytes)
        self.assertEqual(root.findtext("cbc:InvoiceTypeCode", namespaces=UBL_NS), "384")
        self.assertEqual(
            root.findtext(
                "cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID",
                namespaces=UBL_NS,
            ),
            orig.name,
        )
        rect_tipo = root.xpath(
            "cac:AdditionalDocumentReference"
            "[cbc:ID='urn:aeat:names:specification:schema:RECT:TIPO']/"
            "cbc:DocumentTypeCode",
            namespaces=UBL_NS,
        )
        self.assertEqual(rect_tipo[0].text, "R1")

        # Invoice dated before 2026-10-06 raises UserError
        old_inv = self._create_spfe_invoice(invoice_date="2026-09-15")
        old_inv.action_post()
        with self.assertRaises(UserError):
            self.env["base.ubl"].spfe_generate_invoice_ubl_xml(old_inv)

    def test_04_extended_anexo_i_features_and_real_estate(self):
        """Test substitution refund, foreign currency, real estate, suplidos & hooks."""
        post_init_hook(self.env)
        self.company.action_configure_spfe_spanish_taxes()
        self.company.write(
            {
                "spfe_billing_authorization_ref": "AUT-AEAT-2026-01",
                "spfe_billing_authorization_desc": "Autorización facturación",
                "spfe_third_party_issuer_id": self.partner_es.id,
            }
        )

        # Regime key display_name + unique constraint
        key_01 = self.env.ref("l10n_es_spfe.spfe_reg_key_iva_01")
        self.assertIn("[IVA-01]", key_01.display_name)
        with self.assertRaises(ValidationError):
            self.env["l10n.es.spfe.registration.key"].create(
                {"code": "01", "name": "Duplicada", "tax_qualifier": "IVA"}
            )

        # Real estate records (standard ES, Navarra/foral, foreign)
        re_es = self.env["l10n.es.aeat.real_estate"].create(
            {
                "name": "INM-ES-1",
                "company_id": self.company.id,
                "partner_id": self.company.partner_id.id,
                "reference": "9872023VH5797S0001WX",
                "country_id": self.country_es.id,
                "state_id": self.state_madrid.id,
                "city": "Madrid",
                "zip": "28001",
                "address": "Gran Vía 1",
                "number": 1,
            }
        )
        country_fr = self.env.ref("base.fr")
        re_fr = self.env["l10n.es.aeat.real_estate"].create(
            {
                "name": "INM-FR-1",
                "company_id": self.company.id,
                "partner_id": self.company.partner_id.id,
                "country_id": country_fr.id,
                "city": "Paris",
                "zip": "75001",
                "address": "Rue de Rivoli 1",
                "number": 1,
            }
        )
        partner_fr = self.env["res.partner"].create(
            {
                "name": "Société Client SAS",
                "is_company": True,
                "vat": "FR23334175221",
                "street": "10 Avenue de l'Opéra",
                "street2": "Bâtiment B",
                "city": "Paris",
                "zip": "75001",
                "country_id": country_fr.id,
            }
        )
        usd = self.env.ref("base.USD")
        usd.active = True
        key_11 = self.env.ref("l10n_es_spfe.spfe_reg_key_iva_11")

        orig = self._create_spfe_invoice()
        orig.action_post()

        inv = self._create_spfe_invoice(
            move_type="out_refund",
            partner=partner_fr,
            currency_id=usd.id,
            reversed_entry_id=orig.id,
            spfe_refund_type="R2",
            spfe_refund_mode="S",
            spfe_rectified_base=200.0,
            spfe_rectified_tax=42.0,
            spfe_rectified_surcharge=10.4,
            spfe_operation_date="2026-10-18",
            spfe_prepaid_date="2026-10-10",
            spfe_period_start_date="2026-10-01",
            spfe_period_end_date="2026-10-31",
            invoice_origin="SO-2026-001",
            ref="PO-FR-99",
            spfe_note_code="REG",
            spfe_note="Mención legal obligatoria",
            lines=[
                {
                    "product_id": self.product.id,
                    "name": "Arrendamiento oficina",
                    "quantity": 1.0,
                    "price_unit": 200.0,
                    "tax_ids": [Command.set(self.tax_iva21.ids)],
                    "spfe_second_registration_key_id": key_11.id,
                    "spfe_real_estate_id": re_es.id,
                    "spfe_line_info": "Contrato arrendamiento",
                },
                {
                    "product_id": self.product.id,
                    "name": "Local extranjero",
                    "quantity": 1.0,
                    "price_unit": 50.0,
                    "tax_ids": [Command.set(self.tax_iva21.ids)],
                    "spfe_real_estate_id": re_fr.id,
                },
                {
                    "product_id": self.product.id,
                    "name": "Suplido registral",
                    "quantity": 1.0,
                    "price_unit": 25.0,
                    "tax_ids": [],
                    "spfe_collection_line_type": "SUPL",
                },
            ],
        )
        # Foreign recipient is excluded from automatic SPFE scope by default
        self.assertFalse(inv.spfe_enabled)
        inv.action_post()
        xml_bytes = self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv)
        root = etree.fromstring(xml_bytes)
        self.assertEqual(root.findtext("cbc:TaxCurrencyCode", namespaces=UBL_NS), "EUR")
        self.assertTrue(root.xpath("cac:PrepaidPayment", namespaces=UBL_NS))
        self.assertTrue(root.xpath("cac:TaxExchangeRate", namespaces=UBL_NS))
        self.assertEqual(
            len(
                root.xpath(
                    "cac:AdditionalDocumentReference"
                    "[cbc:ID='urn:aeat:names:specification:schema:RECT:IMPORTES']",
                    namespaces=UBL_NS,
                )
            ),
            3,
        )

    def test_05_party_period_and_schema_validations(self):
        """Test address, VAT, summary period, and XSD validation error branches."""
        # Invalid summary period (cross-month)
        bad_period = self._create_spfe_invoice(
            spfe_period_start_date="2026-10-15",
            spfe_period_end_date="2026-11-05",
        )
        bad_period.action_post()
        with self.assertRaises(UserError):
            self.env["base.ubl"].spfe_generate_invoice_ubl_xml(bad_period)

        # Partner without VAT
        no_vat = self.env["res.partner"].create(
            {
                "name": "Sin NIF S.L.",
                "street": "Calle 1",
                "city": "Madrid",
                "zip": "28001",
                "state_id": self.state_madrid.id,
                "country_id": self.country_es.id,
            }
        )
        inv_novat = self._create_spfe_invoice(partner=no_vat)
        inv_novat.action_post()
        with self.assertRaises(UserError):
            self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv_novat)

        # Spanish partner missing city/zip
        no_city = self.env["res.partner"].create(
            {
                "name": "Sin Ciudad S.L.",
                "vat": "ESA12345674",
                "street": "Calle 2",
                "country_id": self.country_es.id,
            }
        )
        inv_nocity = self._create_spfe_invoice(partner=no_city)
        inv_nocity.action_post()
        with self.assertRaises(UserError):
            self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv_nocity)

        # Line without main VAT tax + invalid XML against XSD 2.5
        inv_notax = self._create_spfe_invoice(
            lines=[
                {
                    "product_id": self.product.id,
                    "name": "Sin IVA",
                    "quantity": 1.0,
                    "price_unit": 10.0,
                    "tax_ids": [],
                }
            ]
        )
        inv_notax.action_post()
        with self.assertRaises(UserError):
            self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv_notax)
        with (
            mute_logger("odoo.addons.base_ubl.models.ubl"),
            self.assertRaises(UserError),
        ):
            self.env["base.ubl"]._ubl_check_xml_schema(
                b"<Invoice/>", "Invoice", version="2.5"
            )

    def test_06_mixed_surcharge_exempt_price_include_and_parse(self):
        """Mixed RE + exempt lines, price_include discount, and UBL WTH/neg parse."""
        # Tax word-boundary check: 'requerido' must NOT be flagged as RE surcharge
        tax_req_word = self.env["account.tax"].create(
            {
                "name": "IVA 10% documento requerido",
                "description": "Documento requerido",
                "amount": 10.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": self.company.id,
            }
        )
        self.company._configure_spfe_spanish_taxes()
        self.assertFalse(tax_req_word.spfe_is_surcharge)

        tax_exempt = self.env["account.tax"].create(
            {
                "name": "IVA Exento Art. 20",
                "description": "Exenta Art 20",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "l10n_es_type": "exento",
                "l10n_es_exempt_reason": "E1",
                "company_id": self.company.id,
            }
        )
        tax_incl = self.env["account.tax"].create(
            {
                "name": "IVA 21% Incluido",
                "amount": 21.0,
                "amount_type": "percent",
                "price_include_override": "tax_included",
                "type_tax_use": "sale",
                "company_id": self.company.id,
            }
        )
        self.company._configure_spfe_spanish_taxes()

        inv = self._create_spfe_invoice(
            lines=[
                {
                    "product_id": self.product.id,
                    "name": "Línea con RE",
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "tax_ids": [Command.set((self.tax_iva21 | self.tax_req52).ids)],
                },
                {
                    "product_id": self.product.id,
                    "name": "Seguro exento",
                    "quantity": 1.0,
                    "price_unit": 50.0,
                    "tax_ids": [Command.set(tax_exempt.ids)],
                },
                {
                    "product_id": self.product.id,
                    "name": "Servicio IVA incluido con dto",
                    "quantity": 1.0,
                    "price_unit": 121.0,
                    "discount": 10.0,
                    "tax_ids": [Command.set(tax_incl.ids)],
                },
                {
                    "product_id": self.product.id,
                    "name": "Abono promocional negativo",
                    "quantity": -1.0,
                    "price_unit": 20.0,
                    "tax_ids": [Command.set((self.tax_iva21 | self.tax_irpf15).ids)],
                },
            ]
        )
        inv.action_post()
        xml_bytes = self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv)
        root = etree.fromstring(xml_bytes)

        # Line 2 keeps category E (not overridden to N) and VATEX code
        line2_cat = root.xpath(
            "cac:InvoiceLine[cbc:ID='2']/cac:Item/cac:ClassifiedTaxCategory/cbc:ID",
            namespaces=UBL_NS,
        )[0].text
        self.assertEqual(line2_cat, "E")
        # Line 3 price_include=True: gross unit without VAT is 100.00, discount 10.00
        line3_price = root.xpath(
            "cac:InvoiceLine[cbc:ID='3']/cac:Price/cbc:PriceAmount",
            namespaces=UBL_NS,
        )[0].text
        self.assertEqual(line3_price, "100.00")

        # Parse back as incoming vendor bill: ambiguous taxes are not guessed,
        # while an unambiguous withholding tax (code 03) is matched cleanly.
        wth_03 = self.env["account.tax"].create(
            {
                "name": "IRPF 15% Forestal Compras",
                "amount": -15.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "company_id": self.company.id,
                "spfe_is_withholding": True,
                "spfe_withholding_type": "03",
            }
        )
        in_xml = xml_bytes.replace(b"B12345674", b"G87846952")
        vals_ambig = self.env["base.ubl"].spfe_parse_invoice_ubl_to_move_vals(
            in_xml, self.company
        )
        self.assertEqual(vals_ambig["invoice_line_ids"][3][2]["tax_ids"], [])

        in_xml_03 = in_xml.replace(
            b"<cbc:TaxTypeCode>01</cbc:TaxTypeCode>",
            b"<cbc:TaxTypeCode>03</cbc:TaxTypeCode>",
        )
        vals = self.env["base.ubl"].spfe_parse_invoice_ubl_to_move_vals(
            in_xml_03, self.company
        )
        neg_line = vals["invoice_line_ids"][3][2]
        self.assertEqual(neg_line["quantity"], -1.0)
        self.assertEqual(neg_line["price_unit"], 20.0)
        self.assertEqual(neg_line["tax_ids"][0][2], [wth_03.id])

        # Global rounding check: 3 lines of 0.05 EUR at 10% IVA = 0.02 EUR (not 0.03)
        tax_10 = self.env["account.tax"].search(
            [
                ("company_id", "=", self.company.id),
                ("type_tax_use", "=", "sale"),
                ("amount", "=", 10.0),
                ("spfe_is_surcharge", "=", False),
            ],
            limit=1,
        )
        inv_rg = self._create_spfe_invoice(
            invoice_date_due="2026-10-20",
            lines=[
                {
                    "product_id": self.product.id,
                    "name": f"Item {i}",
                    "quantity": 1.0,
                    "price_unit": 0.05,
                    "tax_ids": [Command.set(tax_10.ids)],
                }
                for i in (1, 2, 3)
            ],
        )
        inv_rg.action_post()
        rg_root = etree.fromstring(
            self.env["base.ubl"].spfe_generate_invoice_ubl_xml(inv_rg)
        )
        self.assertEqual(
            rg_root.findtext("cac:TaxTotal/cbc:TaxAmount", namespaces=UBL_NS),
            "0.02",
        )
        self.assertEqual(
            rg_root.findtext(
                "cac:LegalMonetaryTotal/cbc:PayableAmount", namespaces=UBL_NS
            ),
            "0.17",
        )
        # Without payment term & due == issue_date, Ley 3/2004 adds 30 days
        self.assertEqual(
            rg_root.findtext("cbc:DueDate", namespaces=UBL_NS), "2026-11-19"
        )
