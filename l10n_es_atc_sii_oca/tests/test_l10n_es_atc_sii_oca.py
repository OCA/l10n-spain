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
        cls.igic = cls.company._get_taxes_from_xmlids(["account_tax_template_igic_r_7"])
        # The breakdown is built from the taxes the selected aeat.sii.map
        # classifies. The ATC map this module ships is never the selected one
        # (see readme/ROADMAP.md), so an invoice has to carry a tax of the
        # generic map for a breakdown to exist at all and the renaming this
        # module does to be observable.
        cls.mapped_tax = cls.company._get_taxes_from_xmlids(
            ["account_tax_template_s_iva21b"]
        )
        # The product of the base is exempt (E5), so its invoice carries no
        # tax breakdown at all: this one is taxed
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

    def _canary_invoice(self, partner=None, taxes=None):
        return self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": (partner or self.partner).id,
                "invoice_date": "2020-01-01",
                "move_type": "out_invoice",
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
                            "tax_ids": [(6, 0, (taxes or self.mapped_tax).ids)],
                        },
                    )
                ],
            }
        )

    def test_the_canary_igic_taxes_come_from_the_merged_chart(self):
        """20.0 ships the IGIC taxes in es_common, not in a Canary chart."""
        self.assertEqual(len(self.igic), 1)
        self.assertEqual(self.igic.amount, 7)

    def test_atc_sii_map_covers_the_igic_taxes(self):
        """The ATC map sends the IGIC taxes under the issued-invoices code."""
        sii_map = self.env.ref("l10n_es_atc_sii_oca.atc_sii_map")
        self.assertEqual(sii_map.tax_agency_id, self.agency_canarias)
        goods_line = sii_map.map_lines.filtered(lambda x: x.code == "SFESB")
        self.assertIn(
            "account_tax_template_igic_r_7", goods_line.tax_xmlid_ids.mapped("name")
        )

    def test_atc_header_declares_its_own_sii_version(self):
        """The ATC still runs version 1.0 of the SII, the AEAT does not."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice()
        self.assertEqual(invoice._get_aeat_header()["IDVersionSii"], "1.0")
        self.company.tax_agency_id = self.agency_spain
        self.assertNotEqual(invoice._get_aeat_header()["IDVersionSii"], "1.0")

    def test_the_breakdown_sent_to_the_atc_is_igic_not_iva(self):
        """The ATC rejects the IVA key names, so they are renamed to IGIC."""
        invoice = self._canary_invoice()
        self.company.tax_agency_id = self.agency_canarias
        keys = collect_keys(invoice._get_aeat_invoice_dict_out())
        self.assertIn("DesgloseIGIC", keys)
        self.assertNotIn("DesgloseIVA", keys)
        self.assertNotIn("DetalleIVA", keys)
        # The same invoice sent to the AEAT keeps the IVA names
        self.company.tax_agency_id = self.agency_spain
        aeat_keys = collect_keys(invoice._get_aeat_invoice_dict_out())
        self.assertIn("DesgloseIVA", aeat_keys)
        self.assertNotIn("DesgloseIGIC", aeat_keys)

    def test_a_foreign_vat_is_an_official_document_for_the_atc(self):
        """IDType 02 is rejected with error 1103: the ATC only takes 04."""
        self.company.tax_agency_id = self.agency_canarias
        invoice = self._canary_invoice(partner=self.foreign_partner)
        self.assertEqual(invoice._get_sii_identifier()["IDOtro"]["IDType"], "04")
        self.company.tax_agency_id = self.agency_spain
        self.assertEqual(invoice._get_sii_identifier()["IDOtro"]["IDType"], "02")
