# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


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

    def test_import_surcharge_is_the_retail_surcharge(self):
        """The IGIC import surcharge of the retail traders is reported by its
        amount, as the ATC schema has no equivalence surcharge."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice(
            [self._igic("igic_sop_i_7", "igic_p_re07")], move_type="in_invoice"
        )
        sii_dict = invoice._get_aeat_invoice_dict()["FacturaRecibida"]
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
