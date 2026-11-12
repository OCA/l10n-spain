# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json
from unittest.mock import patch

from odoo.exceptions import UserError

from .test_l10n_es_aeat_sii import TestL10nEsAeatSiiBase
from .test_sii_send_batch import FakeSiiService


class TestL10nEsAeatSiiTaxData(TestL10nEsAeatSiiBase):
    """SII breakdown and registration keys taken from the Spanish data of the
    taxes and from the forced key of the fiscal position."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_service = cls.env["product.product"].create(
            {"name": "Test service", "type": "service"}
        )
        cls.product_goods = cls.env["product.product"].create(
            {"name": "Test goods", "type": "consu"}
        )
        cls.eu_customer = cls.env["res.partner"].create(
            {
                "name": "French Customer",
                "country_id": cls.env.ref("base.fr").id,
                "vat": "FR23334175221",
            }
        )
        cls.fp_group = cls.env["account.fiscal.position"].create(
            {
                "name": "Group of entities",
                "company_id": cls.company.id,
                "sii_regime_code_sale": "06",
            }
        )

    @classmethod
    def _tax(cls, xml_id):
        return cls.company._get_taxes_from_xmlids([f"account_tax_template_{xml_id}"])

    @classmethod
    def _create_tax(cls, name, amount, **vals):
        return cls.env["account.tax"].create(
            {
                "name": name,
                "company_id": cls.company.id,
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": amount,
                **vals,
            }
        )

    def _create_sii_invoice(self, lines, partner=None, fiscal_position=None):
        return self.env["account.move"].create(
            {
                "name": "TEST001",
                "partner_id": (partner or self.partner).id,
                "fiscal_position_id": fiscal_position and fiscal_position.id,
                "invoice_date": "2020-01-01",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "account_id": self.account_expense.id,
                            "name": "Test line",
                            "price_unit": price,
                            "quantity": 1,
                            "tax_ids": [(6, 0, taxes.ids)],
                        },
                    )
                    for product, price, taxes in lines
                ],
            }
        )

    def _issued_invoice_dict(self, invoice):
        return invoice._get_aeat_invoice_dict()["FacturaExpedida"]

    def test_forced_regime_code_with_tax_codes(self):
        """The forced key of the fiscal position is the main one, and the keys
        of the taxes the additional ones."""
        self.assertIn("06", self.fp_group.sii_available_regime_codes_sale.split(","))
        invoice = self._create_sii_invoice(
            [
                (self.product_goods, 100, self._tax("s_iva21b")),
                (self.product_goods, 200, self._tax("s_iva0_g_e")),
            ],
            fiscal_position=self.fp_group,
        )
        self.assertEqual(invoice.l10n_es_regime_code, "06")
        self.assertEqual(invoice.l10n_es_regime_code_additional, "02_sale")
        self.assertFalse(invoice.l10n_es_regime_code_additional2)
        sii_dict = self._issued_invoice_dict(invoice)
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "06")
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendenciaAdicional1"], "02")
        self.assertNotIn("ClaveRegimenEspecialOTrascendenciaAdicional2", sii_dict)

    def test_regime_code_additional2(self):
        """A third key goes to the second additional key, which the core fields
        lack."""
        oss_tax = self._create_tax(
            "VAT 20% FR (OSS)",
            20,
            l10n_es_type="no_sujeto_loc",
            l10n_es_regime_code="17",
            tax_scope="consu",
        )
        invoice = self._create_sii_invoice(
            [
                (self.product_goods, 100, self._tax("s_iva21b")),
                (self.product_goods, 200, self._tax("s_iva0_g_e")),
                (self.product_goods, 300, oss_tax),
            ],
            fiscal_position=self.fp_group,
        )
        self.assertEqual(
            (
                invoice.l10n_es_regime_code,
                invoice.l10n_es_regime_code_additional,
                invoice.l10n_es_regime_code_additional2,
            ),
            ("06", "02_sale", "17"),
        )
        sii_dict = self._issued_invoice_dict(invoice)
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendenciaAdicional2"], "17")
        # The user can still change the keys of a draft invoice
        invoice.l10n_es_regime_code_additional2 = False
        sii_dict = self._issued_invoice_dict(invoice)
        self.assertNotIn("ClaveRegimenEspecialOTrascendenciaAdicional2", sii_dict)

    def test_exempt_causes_per_tax(self):
        """Each exempt tax reports its own exemption cause, and the bases of the
        same cause are added up."""
        exempt_e2 = self._create_tax(
            "Exempt export (other)",
            0,
            l10n_es_type="exento",
            l10n_es_exempt_reason="E2",
            tax_scope="consu",
        )
        invoice = self._create_sii_invoice(
            [
                (self.product_goods, 200, self._tax("s_iva0_g_e")),
                (self.product_goods, 50, exempt_e2),
                (self.product_goods, 100, self._tax("s_iva0_g_i")),
            ]
        )
        details = self._issued_invoice_dict(invoice)["TipoDesglose"]["DesgloseFactura"][
            "Sujeta"
        ]["Exenta"]["DetalleExenta"]
        self.assertEqual(
            sorted(details, key=lambda detail: detail["CausaExencion"]),
            [
                {"CausaExencion": "E2", "BaseImponible": 250.0},
                {"CausaExencion": "E5", "BaseImponible": 100.0},
            ],
        )

    def test_exempt_tax_without_reason(self):
        """Without a cause on the exempt tax, the one of the operation type is
        sent (E5 intra-community, E2 export), and none on national operations,
        as the cause is optional."""
        exempt_tax = self._create_tax(
            "Exempt without reason", 0, l10n_es_type="exento", tax_scope="consu"
        )
        for fiscal_position, expected in (
            (False, {"BaseImponible": 100.0}),
            (self.fp_intra, {"CausaExencion": "E5", "BaseImponible": 100.0}),
            (self.fp_extra, {"CausaExencion": "E2", "BaseImponible": 100.0}),
        ):
            with self.subTest(fiscal_position=fiscal_position):
                invoice = self._create_sii_invoice(
                    [(self.product_goods, 100, exempt_tax)],
                    partner=self.eu_customer,
                    fiscal_position=fiscal_position,
                )
                breakdown = self._issued_invoice_dict(invoice)["TipoDesglose"][
                    "DesgloseTipoOperacion"
                ]["Entrega"]
                self.assertEqual(
                    breakdown["Sujeta"]["Exenta"]["DetalleExenta"], [expected]
                )

    def test_igic_taxes_not_reported(self):
        """The taxes of the Canary Islands (IGIC) are not for the SII of the
        AEAT: an invoice with them has no breakdown."""
        igic_tax = self._create_tax(
            "IGIC 7%", 7, l10n_es_applicability="03", tax_scope="consu"
        )
        invoice = self._create_sii_invoice(
            [
                (self.product_goods, 100, self._tax("s_iva21b")),
                (self.product_goods, 200, igic_tax),
            ]
        )
        self.assertEqual(
            self._issued_invoice_dict(invoice)["TipoDesglose"]["DesgloseFactura"][
                "Sujeta"
            ]["NoExenta"]["DesgloseIVA"]["DetalleIVA"],
            [
                {
                    "TipoImpositivo": "21.0",
                    "BaseImponible": 100.0,
                    "CuotaRepercutida": 21.0,
                }
            ],
        )

    def test_tax_scope_from_product_type(self):
        """Without a scope on the tax, the product type of its lines places it in
        the goods or the services breakdown."""
        exempt_tax = self._create_tax(
            "Exempt intra-community",
            0,
            l10n_es_type="exento",
            l10n_es_exempt_reason="E5",
        )
        self.assertFalse(exempt_tax.tax_scope)
        for product, block, other_block in (
            (self.product_service, "PrestacionServicios", "Entrega"),
            (self.product_goods, "Entrega", "PrestacionServicios"),
        ):
            invoice = self._create_sii_invoice(
                [(product, 100, exempt_tax)],
                partner=self.eu_customer,
                fiscal_position=self.fp_intra,
            )
            breakdown = self._issued_invoice_dict(invoice)["TipoDesglose"][
                "DesgloseTipoOperacion"
            ]
            self.assertNotIn(other_block, breakdown)
            self.assertEqual(
                breakdown[block]["Sujeta"]["Exenta"]["DetalleExenta"],
                [{"CausaExencion": "E5", "BaseImponible": 100.0}],
            )

    def test_ignored_taxes(self):
        """A line with only 'ignore' taxes (disbursements) is out of the invoice
        for VAT purposes, while an 'ignore' tax next to VAT (e.g. a levy) is
        only left out of the breakdown."""
        disbursement_tax = self._create_tax("Disbursements", 0, l10n_es_type="ignore")
        levy_tax = self._create_tax("Levy", 2, l10n_es_type="ignore")
        invoice = self._create_sii_invoice(
            [
                (self.product_goods, 100, self._tax("s_iva21b") | levy_tax),
                (self.product_service, 50, disbursement_tax),
            ]
        )
        self.assertEqual(invoice.amount_total, 173)
        sii_dict = self._issued_invoice_dict(invoice)
        self.assertEqual(sii_dict["ImporteTotal"], 123.0)
        self.assertEqual(
            sii_dict["TipoDesglose"],
            {
                "DesgloseFactura": {
                    "Sujeta": {
                        "NoExenta": {
                            "TipoNoExenta": "S1",
                            "DesgloseIVA": {
                                "DetalleIVA": [
                                    {
                                        "TipoImpositivo": "21.0",
                                        "BaseImponible": 100.0,
                                        "CuotaRepercutida": 21.0,
                                    }
                                ]
                            },
                        }
                    }
                }
            },
        )

    def test_not_subject_causes(self):
        """'no_sujeto' goes to articles 7, 14 and others, 'no_sujeto_loc' to the
        location rules."""
        not_subject_tax = self._create_tax(
            "Not subject art. 7", 0, l10n_es_type="no_sujeto"
        )
        invoice = self._create_sii_invoice(
            [
                (self.product_goods, 100, not_subject_tax),
                (self.product_service, 200, self._tax("s_iva_ns")),
            ]
        )
        self.assertEqual(
            self._issued_invoice_dict(invoice)["TipoDesglose"]["DesgloseFactura"][
                "NoSujeta"
            ],
            {
                "ImportePorArticulos7_14_Otros": 100.0,
                "ImporteTAIReglasLocalizacion": 200.0,
            },
        )

    def test_oss_tax_out_of_total(self):
        """The foreign VAT of a distance sale (OSS) is not in ImporteTotal, and
        its regime code is the registration key."""
        oss_tax = self._create_tax(
            "VAT 20% FR (OSS)",
            20,
            l10n_es_type="no_sujeto_loc",
            l10n_es_regime_code="17",
            tax_scope="consu",
        )
        invoice = self._create_sii_invoice([(self.product_goods, 100, oss_tax)])
        self.assertEqual(invoice.amount_total, 120)
        sii_dict = self._issued_invoice_dict(invoice)
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "17")
        self.assertEqual(sii_dict["ImporteTotal"], 100.0)
        self.assertEqual(
            sii_dict["TipoDesglose"]["DesgloseFactura"],
            {"NoSujeta": {"ImporteTAIReglasLocalizacion": 100.0}},
        )

    def test_self_assessed_purchase_total(self):
        """The self-assessed VAT of a foreign purchase is in ImporteTotal, the
        one of a national reverse charge is not."""
        for xml_id, fiscal_position, total in (
            ("p_iva21_isp", False, 100.0),
            ("p_iva21_sp_in", self.fp_intra, 121.0),
            ("p_iva21_sp_ex", False, 121.0),
        ):
            invoice = self.env["account.move"].create(
                {
                    "partner_id": self.partner.id,
                    "fiscal_position_id": fiscal_position and fiscal_position.id,
                    "invoice_date": "2020-01-01",
                    "ref": f"sup-{xml_id}",
                    "sii_account_registration_date": "2020-10-01",
                    "move_type": "in_invoice",
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_service.id,
                                "account_id": self.account_expense.id,
                                "name": "Test line",
                                "price_unit": 100,
                                "quantity": 1,
                                "tax_ids": [(6, 0, self._tax(xml_id).ids)],
                            },
                        )
                    ],
                }
            )
            self.assertEqual(invoice.amount_total, 100)
            sii_dict = invoice._get_aeat_invoice_dict()["FacturaRecibida"]
            self.assertEqual(sii_dict["ImporteTotal"], total, xml_id)

    def _post_and_send_bill(self, tax, product, fiscal_position=None):
        """Validate a vendor bill and let the cron send it, returning what was
        sent to the AEAT."""
        bill = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "fiscal_position_id": fiscal_position and fiscal_position.id,
                "invoice_date": "2020-01-01",
                "ref": f"sup-{tax.name}",
                "sii_account_registration_date": "2020-10-01",
                "move_type": "in_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "account_id": self.account_expense.id,
                            "name": "Test line",
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax.ids)],
                        },
                    )
                ],
            }
        )
        bill.action_post()
        return self._send_to_sii(bill)["FacturaRecibida"]

    def _send_to_sii(self, move):
        """Send a validated document with the cron, as the user does with "Send
        now", returning what was sent to the AEAT."""
        move.send_sii_now()
        with (
            patch.object(
                type(self.env["account.move"]),
                "_connect_aeat",
                lambda move, mapping_key: FakeSiiService(),
            ),
            self.enter_registry_test_mode(),
        ):
            cron = self.env.ref("l10n_es_aeat_sii_oca.invoice_send_to_sii")
            cron.sudo().method_direct_trigger()
        self.assertEqual(move.aeat_state, "sent")
        return json.loads(move.aeat_content_sent)

    def test_core_tax_data_fixes(self):
        """Purchase taxes whose Spanish data in the core chart differs from what
        the SII expects, fixed by the chart template override."""
        # Intra-community current goods at 10 %: not an investment good, unlike
        # the investment goods tax
        for xml_id, investment in (("p_iva10_ic_bc", False), ("p_iva21_ic_bi", True)):
            sent = self._post_and_send_bill(
                self._tax(xml_id), self.product_goods, self.fp_intra
            )
            detail = sent["DesgloseFactura"]["DesgloseIVA"]["DetalleIVA"][0]
            self.assertEqual("BienInversion" in detail, investment, xml_id)
            self.assertEqual(sent["ClaveRegimenEspecialOTrascendencia"], "09")
        # REAGYP compensation of livestock and fishing, archived in the chart
        reagyp = self._tax("p_iva105_gan").with_context(active_test=False)
        reagyp.active = True
        sent = self._post_and_send_bill(reagyp, self.product_goods)
        self.assertEqual(sent["TipoFactura"], "F6")
        self.assertEqual(sent["ClaveRegimenEspecialOTrascendencia"], "02")
        self.assertEqual(
            sent["DesgloseFactura"]["DesgloseIVA"]["DetalleIVA"],
            [
                {
                    "BaseImponible": 100.0,
                    "ImporteCompensacionREAGYP": 10.5,
                    "PorcentCompensacionREAGYP": "10.5",
                }
            ],
        )
        self.assertEqual(sent["CuotaDeducible"], 10.5)
        self.assertEqual(sent["ImporteTotal"], 110.5)
        # Services from outside the EU at 0 %: reverse charge
        sent = self._post_and_send_bill(
            self._tax("p_iva0_isc"), self.product_service, self.fp_extra
        )
        self.assertEqual(
            list(sent["DesgloseFactura"]), ["InversionSujetoPasivo"], "p_iva0_isc"
        )

    def test_lease_additional_key_property(self):
        """The real property goes with a lease of business premises also when
        its key (12 or 13) is an additional one."""
        invoice = self._create_sii_invoice(
            [(self.product_service, 1000, self._tax("s_iva21s"))]
        )
        self.assertFalse(invoice.sii_property_required)
        invoice.write(
            {
                "l10n_es_regime_code_additional": "12_sale",
                "sii_property_location": "1",
                "sii_property_cadastrial_code": "9872023VH5797S0001WX",
            }
        )
        self.assertTrue(invoice.sii_property_required)
        invoice.action_post()
        sent = self._send_to_sii(invoice)["FacturaExpedida"]
        self.assertEqual(sent["ClaveRegimenEspecialOTrascendenciaAdicional1"], "12")
        self.assertEqual(
            sent["DatosInmueble"],
            {
                "DetalleInmueble": [
                    {
                        "SituacionInmueble": "1",
                        "ReferenciaCatastral": "9872023VH5797S0001WX",
                    }
                ]
            },
        )

    def _create_real_estate(self, name, **vals):
        return self.env["l10n.es.aeat.real_estate"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "partner_id": self.company.partner_id.id,
                "address": "Calle Mayor",
                "city": "Madrid",
                "zip": "28001",
                **vals,
            }
        )

    def _create_lease_invoice(self, real_estates):
        invoice = self._create_sii_invoice(
            [(self.product_service, 100, self._tax("s_iva21s"))] * len(real_estates)
        )
        for line, real_estate in zip(
            invoice.invoice_line_ids, real_estates, strict=True
        ):
            line.l10n_es_aeat_real_estate_id = real_estate
        invoice.l10n_es_regime_code_additional = "12_sale"
        return invoice

    def test_lease_line_real_estates(self):
        """The real estates of the invoice lines go to the SII, with the
        situation of its own list, instead of the property of the invoice."""
        reference = "9872023 VH5797S 0001 WX"
        real_estates = (
            self._create_real_estate(
                "Common territory",
                reference=reference,
                state_id=self.env.ref("base.state_es_m").id,
            )
            + self._create_real_estate(
                "Basque Country",
                reference=reference,
                state_id=self.env.ref("base.state_es_bi").id,
            )
            + self._create_real_estate("Without reference")
            + self._create_real_estate(
                "Abroad", country_id=self.env.ref("base.fr").id, zip="75001"
            )
        )
        # The customer can be given the company's real estates on the lines
        self.assertEqual(
            self.env["l10n.es.aeat.real_estate"].search(
                [("id", "in", real_estates.ids), ("owned_by_company", "=", True)]
            ),
            real_estates,
        )
        invoice = self._create_lease_invoice(real_estates + real_estates[:1])
        self.assertEqual(invoice.sii_real_estate_ids, real_estates)
        invoice.action_post()
        sent = self._send_to_sii(invoice)["FacturaExpedida"]
        self.assertEqual(
            sent["DatosInmueble"]["DetalleInmueble"],
            [
                {
                    "SituacionInmueble": "1",
                    "ReferenciaCatastral": "9872023VH5797S0001WX",
                },
                {
                    "SituacionInmueble": "2",
                    "ReferenciaCatastral": "9872023VH5797S0001WX",
                },
                {"SituacionInmueble": "3"},
                {"SituacionInmueble": "4"},
            ],
        )

    def test_lease_too_many_real_estates(self):
        """The SII takes at most 15 real estates on an invoice."""
        real_estates = self.env["l10n.es.aeat.real_estate"].concat(
            self._create_real_estate(f"Premises {i}") for i in range(16)
        )
        invoice = self._create_lease_invoice(real_estates)
        with self.assertRaisesRegex(UserError, "at most 15 real estates"):
            invoice.action_post()
