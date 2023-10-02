# Copyright (C) 2023 FactorLibre - Alejandro Ji Cheung
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


@common.at_install(False)
@common.post_install(True)
class TestL10nEsAeatMod390Extra(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get Map Tax Lines where taxes are being added
        cls.MapTaxLine = cls.env["l10n.es.aeat.map.tax.line"]
        cls.map_tax_line_702 = cls.MapTaxLine.search(
            [
                ("name", "=", "Régimen ordinario - Base imponible 5%"),
                ("field_number", "=", "702"),
            ]
        )
        cls.map_tax_line_703 = cls.MapTaxLine.search(
            [
                ("name", "=", "Régimen ordinario - Cuota 5%"),
                ("field_number", "=", "703"),
            ]
        )
        map_tax_line_724_name = (
            "IVA deducible en operaciones corrientes de bienes y servicios - Base 5%"
        )
        cls.map_tax_line_724 = cls.MapTaxLine.search(
            [
                (
                    "name",
                    "=",
                    map_tax_line_724_name,
                ),
                ("field_number", "=", "724"),
            ]
        )
        map_tax_line_725_name = (
            "IVA deducible en operaciones corrientes de bienes y servicios - Cuota 5%"
        )
        cls.map_tax_line_725 = cls.MapTaxLine.search(
            [
                (
                    "name",
                    "=",
                    map_tax_line_725_name,
                ),
                ("field_number", "=", "725"),
            ]
        )

        # Get tax templates
        cls.tax_template_s_iva5_a = cls.env.ref(
            "l10n_es_extra_data.account_tax_template_s_iva5_a"
        )
        cls.tax_template_s_iva5s = cls.env.ref(
            "l10n_es_extra_data.account_tax_template_s_iva5s"
        )
        cls.tax_template_p_iva5_sc = cls.env.ref(
            "l10n_es_extra_data.account_tax_template_p_iva5_sc"
        )

    def test_model_390_extra_data(self):
        # Check if tax templates have been added to 702 map tax line
        self.assertIn(self.tax_template_s_iva5_a.id, self.map_tax_line_702.tax_ids.ids)
        self.assertIn(self.tax_template_s_iva5s.id, self.map_tax_line_702.tax_ids.ids)

        # Check if tax templates have been added to 703 map tax line
        self.assertIn(self.tax_template_s_iva5_a.id, self.map_tax_line_703.tax_ids.ids)
        self.assertIn(self.tax_template_s_iva5s.id, self.map_tax_line_703.tax_ids.ids)

        # Check if tax template have been added to 724 map tax line
        self.assertIn(self.tax_template_p_iva5_sc.id, self.map_tax_line_724.tax_ids.ids)

        # Check if tax template have been added to 725 map tax line
        self.assertIn(self.tax_template_p_iva5_sc.id, self.map_tax_line_725.tax_ids.ids)
