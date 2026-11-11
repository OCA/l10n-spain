# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)
from odoo.addons.l10n_es_atc_sii_oca.hooks import post_init_hook


def collect_keys(value, found=None):
    """Every key name appearing anywhere in a nested SII dictionary."""
    found = set() if found is None else found
    if isinstance(value, dict):
        for key, item in value.items():
            found.add(key)
            collect_keys(item, found)
    elif isinstance(value, list | tuple):
        for item in value:
            collect_keys(item, found)
    return found


class TestL10nEsAtcSiiOca(TestL10nEsAeatSiiBase):
    # The SII settings of the companies are set by an administrator
    _test_user_groups = (*TestL10nEsAeatSiiBase._test_user_groups, "base.group_system")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agency_canarias = cls.env.ref("l10n_es_aeat.aeat_tax_agency_canarias")
        cls.agency_spain = cls.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        # A mainland company with an establishment in the Canary Islands: the
        # IGIC taxes are archived by default
        cls.igic = cls._tax("igic_r_7")
        cls.igic_investment = cls._tax("igic_sop_7_inv")
        (cls.igic | cls.igic_investment).active = True
        cls.vat = cls._tax("s_iva21b")
        cls.taxed_product = cls.env["product.product"].create(
            {"name": "Test taxed product"}
        )
        cls.foreign_partner = cls.env["res.partner"].create(
            {
                "name": "Test intra-community partner",
                "vat": "FR23334175221",
                "country_id": cls.env.ref("base.fr").id,
                "property_account_position_id": cls.fp_intra.id,
            }
        )

    @classmethod
    def _tax(cls, xml_id):
        return cls.company._get_taxes_from_xmlids([f"account_tax_template_{xml_id}"])

    @classmethod
    def _igic(cls, *xml_ids):
        """IGIC taxes of the chart, which are archived in a mainland company."""
        taxes = cls.env["account.tax"]
        for xml_id in xml_ids:
            taxes |= cls._tax(xml_id)
        taxes.active = True
        return taxes

    def _canary_invoice(self, taxes_list, partner=None, move_type="out_invoice"):
        return self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": (partner or self.partner).id,
                "invoice_date": "2020-01-01",
                "ref": "sup-001",
                "sii_account_registration_date": "2020-10-01",
                "move_type": move_type,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.taxed_product.id,
                            "account_id": self.account_expense.id,
                            "name": "Test line",
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [(6, 0, taxes.ids)],
                        },
                    )
                    for taxes in taxes_list
                ],
            }
        )

    def test_igic_tax_data(self):
        """The IGIC taxes carry the Spanish data that the breakdown needs."""
        self.assertEqual(self._tax("igic_ISP7").l10n_es_type, "sujeto_isp")
        self.assertEqual(self._tax("igic_p_re07").l10n_es_type, "recargo")
        self.assertEqual(self._tax("igic_re_ex").l10n_es_type, "exento")
        self.assertEqual(self._tax("s_igic_ns").l10n_es_type, "no_sujeto")
        self.assertTrue(self.igic_investment.l10n_es_bien_inversion)
        # IGIC taxes that the core leaves without applicability
        self.assertEqual(self._tax("igic_sop_7_s").l10n_es_applicability, "03")

    def test_install_on_a_company_with_its_chart(self):
        """Installing the module gives the IGIC data to the taxes that a
        company already has, which the chart template did not create with it,
        even when they are used."""
        import_tax = self._igic("igic_sop_i_7")
        export_tax = self._igic("igic_ex_0")
        self._canary_invoice([import_tax], move_type="in_invoice")
        self.assertTrue(import_tax.is_used)
        # The core values of the chart template
        import_tax.l10n_es_type = "sujeto"
        export_tax.write(
            {
                "l10n_es_type": "sujeto",
                "l10n_es_exempt_reason": False,
                "l10n_es_regime_code": False,
            }
        )
        # The install runs as superuser, on every company
        post_init_hook(self.env(su=True))
        self.assertEqual(import_tax.l10n_es_type, "dua")
        self.assertRecordValues(
            export_tax,
            [
                {
                    "l10n_es_type": "exento",
                    "l10n_es_exempt_reason": "E2",
                    "l10n_es_regime_code": "02_sale",
                }
            ],
        )

    def test_atc_header_declares_its_own_sii_version(self):
        """The ATC still runs version 1.0 of the SII, the AEAT does not."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice([self.igic])
        self.assertEqual(invoice._get_aeat_header()["IDVersionSii"], "1.0")
        self.company.tax_agency_id = self.agency_spain
        self.assertNotEqual(invoice._get_aeat_header()["IDVersionSii"], "1.0")

    def test_each_agency_gets_its_own_taxes(self):
        """The ATC gets the IGIC breakdown, with the IGIC key names, and the
        AEAT the VAT one."""
        invoice = self._canary_invoice([self.igic, self.vat])
        self.company.tax_agency_id = self.agency_canarias
        sii_dict = invoice._get_aeat_invoice_dict_out()["FacturaExpedida"]
        self.assertEqual(
            sii_dict["TipoDesglose"]["DesgloseFactura"]["Sujeta"]["NoExenta"],
            {
                "TipoNoExenta": "S1",
                "DesgloseIGIC": {
                    "DetalleIGIC": [
                        {
                            "TipoImpositivo": "7.0",
                            "BaseImponible": 100.0,
                            "CuotaRepercutida": 7.0,
                        }
                    ]
                },
            },
        )
        self.assertNotIn("DesgloseIVA", collect_keys(sii_dict))
        self.company.tax_agency_id = self.agency_spain
        sii_dict = invoice._get_aeat_invoice_dict_out()["FacturaExpedida"]
        self.assertEqual(
            sii_dict["TipoDesglose"]["DesgloseFactura"]["Sujeta"]["NoExenta"][
                "DesgloseIVA"
            ]["DetalleIVA"],
            [
                {
                    "TipoImpositivo": "21.0",
                    "BaseImponible": 100.0,
                    "CuotaRepercutida": 21.0,
                }
            ],
        )
        self.assertNotIn("DesgloseIGIC", collect_keys(sii_dict))

    def test_igic_purchase_regime_code(self):
        """The IGIC purchases have their own registration keys, and the
        investment goods are flagged."""
        self.assertIn(
            "15_igic_purchase",
            self.igic_investment.l10n_es_available_regime_codes.split(","),
        )
        self.assertNotIn(
            "15_igic_purchase",
            self.igic.l10n_es_available_regime_codes.split(","),
        )
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice([self.igic_investment], move_type="in_invoice")
        invoice.l10n_es_regime_code = "15_igic_purchase"
        sii_dict = invoice._get_aeat_invoice_dict_in()["FacturaRecibida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "15")
        self.assertEqual(
            sii_dict["DesgloseFactura"]["DesgloseIGIC"]["DetalleIGIC"],
            [
                {
                    "TipoImpositivo": "7.0",
                    "BaseImponible": 100.0,
                    "CuotaSoportada": 7.0,
                    "BienInversion": "S",
                }
            ],
        )

    def test_a_foreign_vat_is_an_official_document_for_the_atc(self):
        """IDType 02 is rejected with error 1103: the ATC only takes 04."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice([self.igic], partner=self.foreign_partner)
        self.assertEqual(invoice._get_sii_identifier()["IDOtro"]["IDType"], "04")
        self.company.tax_agency_id = self.agency_spain
        self.assertEqual(invoice._get_sii_identifier()["IDOtro"]["IDType"], "02")

    def test_not_subject_igic_is_reported_by_article_9(self):
        """The ATC schema has no articles 7 and 14 of the VAT law: a not subject
        IGIC operation goes as article 9 of Law 20/1991."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice([self._igic("s_igic_ns")])
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertEqual(
            sii_dict["TipoDesglose"]["DesgloseFactura"]["NoSujeta"],
            {"ImportePorArticulos9_Otros": 100.0},
        )

    def test_retail_trader_import(self):
        """An IGIC import is a customs declaration (F5) of the company, and the
        import surcharge, only paid by the retail traders, gives their key 15
        and is reported by its amount, as the ATC schema has no equivalence
        surcharge."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice(
            [self._igic("igic_sop_i_7", "igic_p_re07")], move_type="in_invoice"
        )
        self.assertEqual(invoice.l10n_es_invoice_type, "F5")
        self.assertEqual(invoice.l10n_es_regime_code, "15_igic_purchase")
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaRecibida"]
        self.assertEqual(sii_dict["TipoFactura"], "F5")
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "15")
        self.assertEqual(sii_dict["Contraparte"]["NIF"], "U2687761C")
        self.assertNotIn("ImporteTotal", sii_dict)
        self.assertEqual(
            sii_dict["DesgloseFactura"]["DesgloseIGIC"]["DetalleIGIC"],
            [
                {
                    "TipoImpositivo": "7.0",
                    "BaseImponible": 100.0,
                    "CuotaSoportada": 7.0,
                    "CuotaRecargoMinorista": 0.7,
                }
            ],
        )
        self.assertNotIn("TipoRecargoEquivalencia", collect_keys(sii_dict))
        # The retail trade is exempt and does not deduct (error 1333)
        self.assertEqual(sii_dict["CuotaDeducible"], 0.0)

    def test_igic_export(self):
        """An IGIC export goes with the key 02 and the exemption of art. 11 of
        Law 20/1991 (E2), which the ATC rejects with the key 01 alone (1295)."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice([self._igic("igic_ex_0")])
        self.assertEqual(invoice.l10n_es_regime_code, "02_sale")
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "02")
        self.assertEqual(
            sii_dict["TipoDesglose"]["DesgloseFactura"]["Sujeta"],
            {
                "Exenta": {
                    "DetalleExenta": [{"BaseImponible": 100.0, "CausaExencion": "E2"}]
                }
            },
        )

    def test_retail_trader_sale(self):
        """A sale of a retail trader goes with its key 17 as exempt by art. 50 of
        Law 4/2012 (E1), as the ATC FAQ 8.1 says."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice([self._igic("igic_cmino")])
        self.assertEqual(invoice.l10n_es_regime_code, "17_igic_sale")
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "17")
        self.assertEqual(
            sii_dict["TipoDesglose"]["DesgloseFactura"]["Sujeta"],
            {
                "Exenta": {
                    "DetalleExenta": [{"BaseImponible": 100.0, "CausaExencion": "E1"}]
                }
            },
        )

    def test_igic_only_exemption_cause(self):
        """The ATC has two exemption causes that the AEAT has not, E7 and E8,
        which only an IGIC tax can have."""
        self.company.tax_agency_id = self.agency_canarias
        exempt = self._igic("igic_re_ex")
        exempt.l10n_es_exempt_reason = "E7"
        invoice = self._canary_invoice([exempt])
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertEqual(
            sii_dict["TipoDesglose"]["DesgloseFactura"]["Sujeta"]["Exenta"],
            {"DetalleExenta": [{"BaseImponible": 100.0, "CausaExencion": "E7"}]},
        )
        with self.assertRaises(ValidationError):
            self._tax("s_iva0").l10n_es_exempt_reason = "E8"

    def test_purchase_to_a_retail_trader(self):
        """A purchase to a retail trader deducts its implicit IGIC with the key
        15: the ATC wants the nominal rate, which is the only kind it admits,
        and the implicit tax burden instead of a quota (ATC FAQ 8.2)."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice(
            [self._igic("igic_sop_7_cmino")], move_type="in_invoice"
        )
        self.assertEqual(invoice.l10n_es_regime_code, "15_igic_purchase")
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaRecibida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "15")
        self.assertEqual(
            sii_dict["DesgloseFactura"]["DesgloseIGIC"]["DetalleIGIC"],
            [
                {
                    "TipoImpositivo": "7.0",
                    "BaseImponible": 100.0,
                    "CargaImpositivaImplicita": 4.9,
                }
            ],
        )
        self.assertEqual(sii_dict["CuotaDeducible"], 4.9)
        # The ATC checks the total without the implicit tax burden (error 2045)
        self.assertEqual(invoice.amount_total, 104.9)
        self.assertEqual(sii_dict["ImporteTotal"], 100.0)

    def test_exempt_purchase(self):
        """An exempt purchase goes with its base alone, without the 0 % rate
        that the ATC keeps for the subject operations (ATC FAQ 8.3)."""
        self.company.tax_agency_id = self.agency_canarias
        exempt = self._igic("igic_p_ex")
        invoice = self._canary_invoice([exempt, exempt], move_type="in_invoice")
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaRecibida"]
        self.assertEqual(
            sii_dict["DesgloseFactura"]["DesgloseIGIC"]["DetalleIGIC"],
            [{"BaseImponible": 200.0}],
        )
        self.assertEqual(sii_dict["CuotaDeducible"], 0.0)

    def test_purchase_to_a_small_business(self):
        """With the key 16 of the small businesses alone, the ATC rejects any
        quota (errors 1325 and 1328), even when the invoice was booked with a
        subject tax."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice(
            [self._igic("igic_sop_0")], move_type="in_invoice"
        )
        invoice.l10n_es_regime_code = "16_igic_purchase"
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaRecibida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "16")
        self.assertEqual(
            sii_dict["DesgloseFactura"]["DesgloseIGIC"]["DetalleIGIC"],
            [{"BaseImponible": 100.0}],
        )
        self.assertEqual(sii_dict["CuotaDeducible"], 0.0)

    def test_art25_sale(self):
        """A sale exempt by art. 25 of Law 19/1994 (key 19, E5) needs the
        details of the good and its document, which the ATC rejects without
        (error 2031), as the FAQ 7.1 example of a building sold by deed."""
        self.company.tax_agency_id = self.agency_canarias
        exempt = self._igic("igic_re_ex")
        exempt.l10n_es_exempt_reason = "E5"
        invoice = self._canary_invoice([exempt])
        invoice.l10n_es_regime_code = "19_igic_sale"
        self.assertTrue(invoice.sii_art25_required)
        with self.assertRaises(UserError):
            invoice._aeat_check_exceptions()
        with self.assertRaises(ValidationError):
            invoice.sii_art25_detail_ids = [
                Command.create({"asset_type": "01", "document_type": "01"})
            ]
        invoice.sii_art25_detail_ids = [
            Command.create(
                {
                    "asset_type": "01",
                    "document_type": "01",
                    "protocol_number": "1234",
                    "notary_name": "Test Notary",
                }
            ),
            Command.create({"asset_type": "02", "advance_payment": True}),
        ]
        invoice._aeat_check_exceptions()
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "19")
        self.assertEqual(
            sii_dict["DatosArticulo25"],
            {
                "DetalleArticulo25": [
                    {
                        "PagoAnticipadoArt25": "N",
                        "TipoBienArt25": "01",
                        "IDDocumentoArt25": [
                            {
                                "TipoDocumArt25": "01",
                                "NumeroProtocolo": "1234",
                                "ApellidosNombreNotario": "Test Notary",
                            }
                        ],
                    },
                    {"PagoAnticipadoArt25": "S", "TipoBienArt25": "02"},
                ]
            },
        )
        # Only the key 19 admits the block (error 2031)
        invoice.l10n_es_regime_code = "01_sale"
        self.assertFalse(invoice.sii_art25_required)
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertNotIn("DatosArticulo25", sii_dict)
        with self.assertRaises(ValidationError):
            invoice.sii_art25_detail_ids = [
                Command.create({"asset_type": "02"}) for _index in range(2)
            ]

    def test_art25_purchase(self):
        """A purchase exempt by art. 25 of Law 19/1994 goes with the key 17
        and the details of the good (error 2028), the key that the sales give
        to the retail traders."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice(
            [self._igic("igic_p_ex")], move_type="in_invoice"
        )
        invoice.write(
            {
                "l10n_es_regime_code": "17_igic_purchase",
                "sii_art25_detail_ids": [
                    Command.create({"asset_type": "03", "document_type": "02"})
                ],
            }
        )
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaRecibida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "17")
        self.assertEqual(
            sii_dict["DatosArticulo25"]["DetalleArticulo25"],
            [
                {
                    "PagoAnticipadoArt25": "N",
                    "TipoBienArt25": "03",
                    "IDDocumentoArt25": [{"TipoDocumArt25": "02"}],
                }
            ],
        )
        self.assertEqual(sii_dict["CuotaDeducible"], 0.0)
        # The key 17 of a sale is the one of the retail traders
        sale = self._canary_invoice([self._igic("igic_cmino")])
        self.assertEqual(sale.l10n_es_regime_code, "17_igic_sale")
        self.assertFalse(sale.sii_art25_required)

    def test_group_of_entities_cost_tax_base(self):
        """The invoices of the advanced level of the group of entities regime
        (key 06) need their cost tax base (error 1233), with the sign of their
        quotas (error 1234), and only them (error 1301)."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice([self.igic])
        invoice.l10n_es_regime_code = "06"
        self.assertTrue(invoice.sii_atc)
        with self.assertRaises(UserError):
            invoice._aeat_check_exceptions()
        invoice.sii_cost_tax_base = 80
        invoice._aeat_check_exceptions()
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertEqual(sii_dict["ClaveRegimenEspecialOTrascendencia"], "06")
        self.assertEqual(sii_dict["BaseImponibleACoste"], 80.0)
        refund = self._canary_invoice([self.igic], move_type="out_refund")
        refund.write({"l10n_es_regime_code": "06", "sii_cost_tax_base": 80})
        sii_dict = refund._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertEqual(sii_dict["BaseImponibleACoste"], -80.0)
        invoice.l10n_es_regime_code = "01"
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertNotIn("BaseImponibleACoste", sii_dict)
        # The AEAT does not get it
        self.company.tax_agency_id = self.agency_spain
        invoice.l10n_es_regime_code = "06"
        self.assertFalse(invoice.sii_atc)
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaExpedida"]
        self.assertNotIn("BaseImponibleACoste", sii_dict)
