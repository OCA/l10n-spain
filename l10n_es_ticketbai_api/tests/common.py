# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import json
import os
from random import randrange

from lxml import etree

from odoo import fields
from odoo.tests import common
from odoo.tests.common import tagged

from ..models.ticketbai_invoice import RefundCode, RefundType
from ..models.ticketbai_invoice_tax import (
    ExemptedCause,
    NotExemptedType,
    NotSubjectToCause,
    SurchargeOrSimplifiedRegimeType,
    VATRegimeKey,
)
from ..ticketbai.xml_schema import TicketBaiSchema, XMLSchema


@tagged("post_install", "-at_install")
class TestL10nEsTicketBAIAPI(common.TransactionCase):
    catalogs = [
        "file:"
        + (
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)), "schemas/catalog.xml"
            )
        )
    ]

    def _send_to_tax_agency(self, invoice):
        pending_invoices = self.env["tbai.invoice"].get_next_pending_invoice(
            company_id=self.main_company.id, limit=0
        )
        self.assertEqual(1, len(pending_invoices))
        self.env["tbai.invoice"].send_pending_invoices()
        self.assertEqual("sent", invoice.state)
        pending_invoices = self.env["tbai.invoice"].get_next_pending_invoice(
            company_id=self.main_company.id, limit=0
        )
        self.assertEqual(0, len(pending_invoices))
        invoice.with_user().unlink()

    def create_tbai_national_invoice_cancellation(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        return (
            self.env["tbai.invoice"]
            .with_user(uid)
            .create(
                {
                    "schema": TicketBaiSchema.AnulaTicketBai.value,
                    "name": name,
                    "company_id": company_id,
                    "number": number,
                    "number_prefix": number_prefix,
                    "expedition_date": fields.date.today().strftime("%d-%m-%Y"),
                }
            )
        )

    @staticmethod
    def _get_invoice_header_values(
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        vat_regime_key="01",
        is_invoice_refund=False,
        refund_code=None,
        refund_type=None,
        refunded_invoice_number="",
        refunded_invoice_number_prefix="",
        substituted_invoice_amount_total_untaxed=0.0,
        substituted_invoice_total_tax_amount=0.0,
    ):
        vals = {
            "schema": TicketBaiSchema.TicketBai.value,
            "name": name,
            "company_id": company_id,
            "number": number,
            "number_prefix": number_prefix,
            "vat_regime_key": vat_regime_key,
            "expedition_date": fields.date.today().strftime("%d-%m-%Y"),
            "expedition_hour": "09:00:00",
        }
        if is_invoice_refund:
            vals.update(
                {
                    "is_invoice_refund": is_invoice_refund,
                    "refund_code": refund_code,
                    "refund_type": refund_type,
                    "tbai_invoice_refund_ids": [
                        (
                            0,
                            0,
                            {
                                "number_prefix": refunded_invoice_number_prefix,
                                "number": refunded_invoice_number,
                                "expedition_date": fields.date.today().strftime(
                                    "%d-%m-%Y"
                                ),
                            },
                        )
                    ],
                }
            )
            if RefundType.substitution.value == refund_type:
                vals.update(
                    {
                        "substituted_invoice_amount_total_untaxed": "%.2f"
                        % substituted_invoice_amount_total_untaxed,
                        "substituted_invoice_total_tax_amount": "%.2f"
                        % substituted_invoice_total_tax_amount,
                    }
                )
        return vals

    @staticmethod
    def _get_invoice_line_values(
        desc="Description", qty=1.0, price=100.0, disc=0.0, total=121.0
    ):
        return {
            "description": desc,
            "quantity": "%.2f" % qty,
            "price_unit": "%.2f" % price,
            "discount_amount": "%.2f" % disc,
            "amount_total": "%.2f" % total,
        }

    @staticmethod
    def _get_invoice_tax_values(
        base=100.0,
        is_subject_to=True,
        not_subject_to_cause=None,
        is_exempted=False,
        exempted_cause=None,
        not_exempted_type=None,
        amount=21.0,
        amount_total=21.0,
        re_amount=0.0,
        re_amount_total=0.0,
        surcharge_or_simplified_regime="N",
        tax_type=None,
    ):
        return {
            "base": "%.2f" % base,
            "is_subject_to": is_subject_to,
            "not_subject_to_cause": not_subject_to_cause,
            "is_exempted": is_exempted,
            "exempted_cause": exempted_cause,
            "not_exempted_type": not_exempted_type,
            "amount": amount and "%.2f" % amount or "",
            "amount_total": amount_total and "%.2f" % amount_total or "",
            "re_amount": re_amount and "%.2f" % re_amount or "",
            "re_amount_total": re_amount_total and "%.2f" % re_amount_total or "",
            "surcharge_or_simplified_regime": surcharge_or_simplified_regime,
            "type": tax_type,
        }

    def create_tbai_national_invoice_exempted(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        vals = self._get_invoice_header_values(
            name=name, company_id=company_id, number=number, number_prefix=number_prefix
        )
        l1_qty = 1.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total = l1_qty * l1_price_unit - l1_discount_amount
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 1.25
        l2_price_unit = 4.99
        l2_amount_total = l2_qty * l2_price_unit
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=True,
            exempted_cause=ExemptedCause.E1.value,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_national_invoice(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        vals = self._get_invoice_header_values(
            name=name, company_id=company_id, number=number, number_prefix=number_prefix
        )
        l1_qty = 1.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total_untaxed = l1_qty * l1_price_unit - l1_discount_amount
        l1_amount_total = l1_amount_total_untaxed * 1.21
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 1.25
        l2_price_unit = 4.99
        l2_amount_total_untaxed = l2_qty * l2_price_unit
        l2_amount_total = l2_amount_total_untaxed * 1.21
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total_untaxed = l1_amount_total_untaxed + l2_amount_total_untaxed
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=False,
            not_exempted_type=NotExemptedType.S1.value,
            amount=21.0,
            amount_total=amount_total - amount_total_untaxed,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_national_invoice_not_subject_to(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        vals = self._get_invoice_header_values(
            name=name, company_id=company_id, number=number, number_prefix=number_prefix
        )
        l1_qty = 1.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total = l1_qty * l1_price_unit - l1_discount_amount
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 1.25
        l2_price_unit = 4.99
        l2_amount_total = l2_qty * l2_price_unit
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=False,
            not_subject_to_cause=NotSubjectToCause.RL.value,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_extracommunity_invoice(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        vals = self._get_invoice_header_values(
            name=name,
            company_id=company_id,
            number=number,
            number_prefix=number_prefix,
            vat_regime_key=VATRegimeKey.K02.value,
        )
        l1_qty = 1.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total = l1_qty * l1_price_unit - l1_discount_amount
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 1.25
        l2_price_unit = 4.99
        l2_amount_total = l2_qty * l2_price_unit
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=True,
            exempted_cause=ExemptedCause.E2.value,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_intracommunity_invoice(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        vals = self._get_invoice_header_values(
            name=name, company_id=company_id, number=number, number_prefix=number_prefix
        )
        l1_qty = 1.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total = l1_qty * l1_price_unit - l1_discount_amount
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 1.25
        l2_price_unit = 4.99
        l2_amount_total = l2_qty * l2_price_unit
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=True,
            exempted_cause=ExemptedCause.E5.value,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_national_invoice_irpf(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        vals = self._get_invoice_header_values(
            name=name, company_id=company_id, number=number, number_prefix=number_prefix
        )
        l1_qty = 1.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total_untaxed = l1_qty * l1_price_unit - l1_discount_amount
        l1_retention = l1_amount_total_untaxed * 0.07  # 7% IRPF
        l1_amount_total = l1_amount_total_untaxed * 1.21 - l1_retention
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 1.25
        l2_price_unit = 4.99
        l2_amount_total_untaxed = l2_qty * l2_price_unit
        l2_retention = l2_amount_total_untaxed * 0.07  # 7% IRPF
        l2_amount_total = l2_amount_total_untaxed * 1.21 - l2_retention
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total_untaxed = l1_amount_total_untaxed + l2_amount_total_untaxed
        total_retention = l1_retention + l2_retention
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=False,
            not_exempted_type=NotExemptedType.S1.value,
            amount=21.0,
            amount_total=amount_total_untaxed * 0.21,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "tax_retention_amount_total": "%.2f" % total_retention,
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_national_invoice_surcharge(
        self,
        name="TBAITEST/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/",
        uid=1,
    ):
        vals = self._get_invoice_header_values(
            name=name, company_id=company_id, number=number, number_prefix=number_prefix
        )
        l1_qty = 1.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total_untaxed = l1_qty * l1_price_unit - l1_discount_amount
        l1_surcharge = l1_amount_total_untaxed * 0.052  # 5.2% Surcharge
        l1_amount_total = l1_amount_total_untaxed * 1.21 + l1_surcharge
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 1.25
        l2_price_unit = 4.99
        l2_amount_total_untaxed = l2_qty * l2_price_unit
        l2_surcharge = l2_amount_total_untaxed * 0.052  # 5.2% Surcharge
        l2_amount_total = l2_amount_total_untaxed * 1.21 + l2_surcharge
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total_untaxed = l1_amount_total_untaxed + l2_amount_total_untaxed
        total_surcharge = l1_surcharge + l2_surcharge
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=False,
            not_exempted_type=NotExemptedType.S1.value,
            amount=21.0,
            amount_total=amount_total_untaxed * 0.21,
            re_amount=5.2,
            re_amount_total=total_surcharge,
            surcharge_or_simplified_regime=SurchargeOrSimplifiedRegimeType.S.value,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_national_invoice_refund_by_differences(
        self,
        name="TBAITEST/REF/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/REF/",
        uid=1,
    ):
        # Simulate Original Invoice Discount Amount should be '0' instead of '10'.
        # In this particular case we are increasing the Original Invoice Amount Total
        vals = self._get_invoice_header_values(
            name=name,
            company_id=company_id,
            number=number,
            number_prefix=number_prefix,
            is_invoice_refund=True,
            refund_code=RefundCode.R1.value,
            refund_type=RefundType.differences.value,
            refunded_invoice_number="00001",
            refunded_invoice_number_prefix="TBAITEST/",
        )
        l1_qty = 1.0
        l1_price_unit = 10.0
        l1_amount_total_untaxed = l1_qty * l1_price_unit
        l1_amount_total = l1_amount_total_untaxed * 1.21
        l1_vals = self._get_invoice_line_values(
            desc="L1", qty=l1_qty, price=l1_price_unit, total=l1_amount_total
        )
        amount_total_untaxed = l1_amount_total_untaxed
        amount_total = l1_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=False,
            not_exempted_type=NotExemptedType.S1.value,
            amount=21.0,
            amount_total=amount_total - amount_total_untaxed,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def create_tbai_national_invoice_refund_by_substitution(
        self,
        name="TBAITEST/REF/00001",
        company_id=1,
        number="00001",
        number_prefix="TBAITEST/REF/",
        uid=1,
    ):
        # Simulate Original Invoice wrong quantities on its lines.
        # '10' instead of '1' and '4.25' instead of '1.25'.
        l1_original_base = 1.0 * 100.0 - 10.0
        l1_original_amount_total_untaxed = l1_original_base
        l1_original_total_tax_amount = l1_original_base * 0.21
        l2_original_base = 1.25 * 4.99
        l2_original_amount_total_untaxed = l1_original_base
        l2_original_total_tax_amount = l2_original_base * 0.21
        original_amount_total_untaxed = (
            l1_original_amount_total_untaxed + l2_original_amount_total_untaxed
        )
        original_total_tax_amount = (
            l1_original_total_tax_amount + l2_original_total_tax_amount
        )
        vals = self._get_invoice_header_values(
            name=name,
            company_id=company_id,
            number=number,
            number_prefix=number_prefix,
            is_invoice_refund=True,
            refund_code=RefundCode.R1.value,
            refund_type=RefundType.substitution.value,
            refunded_invoice_number="00001",
            refunded_invoice_number_prefix="TBAITEST/",
            substituted_invoice_amount_total_untaxed=original_amount_total_untaxed,
            substituted_invoice_total_tax_amount=original_total_tax_amount,
        )
        l1_qty = 10.0
        l1_price_unit = 100.0
        l1_discount_amount = 10.0
        l1_amount_total_untaxed = l1_qty * l1_price_unit - l1_discount_amount
        l1_amount_total = l1_amount_total_untaxed * 1.21
        l1_vals = self._get_invoice_line_values(
            desc="L1",
            qty=l1_qty,
            price=l1_price_unit,
            disc=l1_discount_amount,
            total=l1_amount_total,
        )
        l2_qty = 4.25
        l2_price_unit = 4.99
        l2_amount_total_untaxed = l2_qty * l2_price_unit
        l2_amount_total = l2_amount_total_untaxed * 1.21
        l2_vals = self._get_invoice_line_values(
            desc="L2", qty=l2_qty, price=l2_price_unit, total=l2_amount_total
        )
        amount_total_untaxed = l1_amount_total_untaxed + l2_amount_total_untaxed
        amount_total = l1_amount_total + l2_amount_total
        tax_vals = self._get_invoice_tax_values(
            base=amount_total,
            is_subject_to=True,
            is_exempted=False,
            not_exempted_type=NotExemptedType.S1.value,
            amount=21.0,
            amount_total=amount_total - amount_total_untaxed,
        )
        vals.update(
            {
                "tbai_invoice_line_ids": [(0, 0, l1_vals), (0, 0, l2_vals)],
                "tbai_tax_ids": [(0, 0, tax_vals)],
                "amount_total": "%.2f" % amount_total,
            }
        )
        return self.env["tbai.invoice"].with_user(uid).create(vals)

    def add_customer_from_odoo_partner_to_invoice(self, tbai_invoice_id, partner):
        return self.env["tbai.invoice.customer"].create(
            {
                "tbai_invoice_id": tbai_invoice_id,
                "name": partner.tbai_get_value_apellidos_nombre_razon_social(),
                "country_code": partner.country_id.code.upper(),
                "nif": partner.tbai_get_value_nif(),
                "identification_number": partner.tbai_partner_identification_number
                or partner.vat,
                "idtype": partner.tbai_partner_idtype,
                "address": partner.tbai_get_value_direccion(),
                "zip": partner.zip,
            }
        )

    def create_certificate(self, company_id, cert_path, cert_password):
        with open(cert_path, "rb") as f:
            p12_file = f.read()
        certificate = self.env["tbai.certificate"].create(
            {
                "name": "TicketBAI - Test certificate",
                "company_id": company_id,
                "datas": base64.b64encode(p12_file),
                "password": cert_password,
            }
        )
        return certificate

    def _prepare_gipuzkoa_company(self, company):
        test_dir_path = os.path.abspath(os.path.dirname(__file__))
        self.company_values_json_filepath = os.path.join(test_dir_path, "company.json")
        with open(self.company_values_json_filepath) as fp:
            vals = json.load(fp)
        if "invoice_number" in vals:
            vals.pop("invoice_number")
        if "refund_invoice_number" in vals:
            vals.pop("refund_invoice_number")
        vals.update(
            {
                "tbai_tax_agency_id": self.env.ref(
                    "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa"
                ).id,
            }
        )
        company.write(vals)

    def _prepare_araba_company(self, company):
        test_dir_path = os.path.abspath(os.path.dirname(__file__))
        self.company_values_json_filepath = os.path.join(
            test_dir_path, "company-araba.json"
        )
        with open(self.company_values_json_filepath) as fp:
            vals = json.load(fp)
        if "invoice_number" in vals:
            vals.pop("invoice_number")
        if "refund_invoice_number" in vals:
            vals.pop("refund_invoice_number")
        vals.update(
            {
                "tbai_tax_agency_id": self.env.ref(
                    "l10n_es_ticketbai_api.tbai_tax_agency_araba"
                ).id,
            }
        )
        company.write(vals)

    def _prepare_company(self, company):
        test_dir_path = os.path.abspath(os.path.dirname(__file__))
        json_filepath = self.company_values_json_filepath
        with open(json_filepath) as fp:
            vals = json.load(fp)
            cert_path = os.path.join(
                test_dir_path, vals.pop("tbai_p12_certificate_path")
            )
            cert_password = vals.pop("tbai_p12_certificate_password")
        if "invoice_number" in vals:
            vals.pop("invoice_number")
        if "refund_invoice_number" in vals:
            vals.pop("refund_invoice_number")
        certificate = self.create_certificate(company.id, cert_path, cert_password)
        installation = self.env["tbai.installation"].create(
            {
                "name": vals.pop("tbai_software_name"),
                "version": vals.pop("tbai_software_version"),
                "developer_id": self.env.ref(
                    "l10n_es_ticketbai_api.res_partner_binovo"
                ).id,
                "license_key": vals.pop("tbai_license_key"),
            }
        )
        vals.update(
            {
                "tbai_enabled": True,
                "tbai_test_enabled": True,
                "tbai_tax_agency_id": self.env.ref(
                    "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa"
                ).id,
                "currency_id": self.env.ref("base.EUR").id,
                "tbai_certificate_id": certificate.id,
                "tbai_installation_id": installation.id,
            }
        )
        company.write(vals)

    def get_next_number(self):
        with open(self.company_values_json_filepath, "r") as fp:
            vals = json.load(fp)
        number = "%05d" % (int(vals["invoice_number"]) + 1)
        with open(self.company_values_json_filepath, "w") as fp:
            vals["invoice_number"] = number
            json.dump(vals, fp, indent=4)
        return number

    def get_next_refund_number(self):
        with open(self.company_values_json_filepath, "r") as fp:
            vals = json.load(fp)
        number = "%05d" % (int(vals["refund_invoice_number"]) + 1)
        with open(self.company_values_json_filepath, "w") as fp:
            vals["refund_invoice_number"] = number
            json.dump(vals, fp, indent=4)
        return number

    def setUp(self):
        super().setUp()
        # can only set this environment variable once because lxml
        # loads it only at startup. Luckily having several catalogs is
        # supported so we provide the catalogs variable for related
        # addons to plug any required additional catalog.
        os.environ["XML_CATALOG_FILES"] = " ".join(self.catalogs)
        test_dir_path = os.path.abspath(os.path.dirname(__file__))
        self.company_values_json_filepath = os.path.join(test_dir_path, "company.json")
        # Disabled by default for automatic tests
        self.send_to_tax_agency = False  # Enable for local testing
        self.number_prefix = "%d/" % randrange(1, 10**19)
        self.refund_number_prefix = "%d/" % randrange(1, 10**19)
        schemas_version_dirname = XMLSchema.schemas_version_dirname
        script_dirpath = os.path.abspath(os.path.dirname(__file__))
        schemas_dirpath = os.path.join(script_dirpath, "schemas")
        # Load XSD file with XADES imports
        test_xml_invoice_filepath = os.path.abspath(
            os.path.join(
                schemas_dirpath, "%s/test_ticketBai V1-2.xsd" % schemas_version_dirname
            )
        )
        self.test_xml_invoice_schema_doc = etree.parse(
            test_xml_invoice_filepath, parser=etree.ETCompatXMLParser()
        )
        # Load XSD file with XADES imports
        test_xml_cancellation_filepath = os.path.abspath(
            os.path.join(
                schemas_dirpath,
                "%s/test_Anula_ticketBai V1-2.xsd" % schemas_version_dirname,
            )
        )
        self.test_xml_cancellation_schema_doc = etree.parse(
            test_xml_cancellation_filepath, parser=etree.ETCompatXMLParser()
        )
        self.main_company = self.env.ref("base.main_company")
        self._prepare_company(self.main_company)

        # Contact creation
        self.partner = self.env["res.partner"].create(
            {
                "name": "Binovo IT Human Project S.L.",
                "is_company": True,
                "city": "Oiartzun",
                "zip": "20180",
                "country_id": self.env.ref("base.es").id,
                "vat": "ESB20990602",
                "street": "Astigarraga bidea 2, 2ª Izquierda, Oficina 10-11",
                "email": "sales@binovo.es",
                "phone": "+34 943569206",
                "website": "https://www.binovo.es/",
            }
        )

        self.partner_extracommunity = self.env["res.partner"].create(
            {
                "name": "Yamaha Motor Co., Ltd.",
                "is_company": True,
                "city": "Iwata",
                "zip": "438-8501",
                "country_id": self.env.ref("base.jp").id,
                "street": "2500 Shingai, Iwata-shi",
                "tbai_partner_idtype": "06",
                "tbai_partner_identification_number": "JP3942800008",
                "phone": "+81 03-5713-3820",
                "website": "https://global.yamaha-motor.com",
            }
        )

        self.partner_intracommunity = self.env["res.partner"].create(
            {
                "name": "SA PSA AUTOMOBILES SA",
                "is_company": True,
                "city": "POISSY",
                "zip": "78300",
                "country_id": self.env.ref("base.fr").id,
                "vat": "FR82542065479",
                "street": "2 BD DE L EUROPE",
                "tbai_partner_idtype": "02",
                "website": "www.groupe-psa.com",
            }
        )

        self.tech_partner = self.env["res.partner"].create(
            {
                "name": "Tech User",
                "company_id": self.env.ref("base.main_company").id,
                "city": "Oiartzun",
                "zip": "20180",
                "country_id": self.env.ref("base.es").id,
                "street": "Astigarraga bidea 2, 2ª Izquierda, Oficina 10-11",
                "email": "tech@yourcompany.example.com",
                "company_name": "Binovo IT Human Project S.L.",
            }
        )

        group_ids = [
            self.env.ref("base.group_user").id,
            self.env.ref("base.group_partner_manager").id,
            self.env.ref("base.group_system").id,
        ]

        self.tech_user = self.env.ref("base.user_demo")
        self.tech_user.write(
            {
                "groups_id": [
                    (
                        6,
                        0,
                        group_ids,
                    )
                ]
            }
        )
