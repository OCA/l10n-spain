# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from .common import L10nEsBankCommon


class TestSpanishBankCode(L10nEsBankCommon):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.bank_account_model = cls.env["res.partner.bank"]

    def test_01_entity_code_is_extracted_from_spanish_ibans(self) -> None:
        for iban, expected_code in (
            ("ES0421002739890200122581", "2100"),
            ("ES9101820000000000000000", "0182"),
            ("ES1299999999509999999999", "9999"),
        ):
            account = self.bank_account_model.create(
                {"partner_id": self.partner.id, "account_number": iban}
            )
            self.assertEqual(account.l10n_es_bank_code, expected_code)

    def test_02_entity_code_updates_and_clears_without_changing_bank_details(
        self,
    ) -> None:
        account = self.bank_account_model.create(
            {
                "partner_id": self.partner.id,
                "account_number": "ES0421002739890200122581",
                "bank_name": "Manual bank name",
                "bank_bic": "MANUALESXXX",
                "street": "Manual street",
            }
        )
        account.write({"account_number": "ES9101820000000000000000"})
        self.assertEqual(account.l10n_es_bank_code, "0182")
        self.assertEqual(account.bank_name, "Manual bank name")
        self.assertEqual(account.bank_bic, "MANUALESXXX")
        self.assertEqual(account.street, "Manual street")

        account.invalidate_recordset(
            ["l10n_es_bank_code", "bank_name", "bank_bic", "street"]
        )
        account = self.bank_account_model.browse(account.id)
        self.assertEqual(account.l10n_es_bank_code, "0182")

        for iban in ("invalid IBAN", "DE89370400440532013000", ""):
            account.write({"account_number": iban})
            self.assertFalse(account.l10n_es_bank_code)
            self.assertEqual(account.bank_name, "Manual bank name")
            self.assertEqual(account.bank_bic, "MANUALESXXX")
            self.assertEqual(account.street, "Manual street")

    def test_03_entity_code_is_searchable_groupable_and_shown_in_views(
        self,
    ) -> None:
        other_partner = self.env["res.partner"].create(
            {"name": "Other bank test partner"}
        )
        accounts = self.bank_account_model.create(
            [
                {
                    "partner_id": other_partner.id,
                    "account_number": "ES0421002739890200122581",
                },
                {
                    "partner_id": self.partner.id,
                    "account_number": "ES0421002739890200122581",
                },
                {
                    "partner_id": self.partner.id,
                    "account_number": "ES9101820000000000000000",
                },
            ]
        )
        self.assertEqual(
            self.bank_account_model.search(
                [("id", "in", accounts.ids), ("l10n_es_bank_code", "=", "2100")]
            ),
            accounts[:2],
        )
        groups = self.bank_account_model.read_group(
            [("id", "in", accounts.ids)],
            ["l10n_es_bank_code"],
            ["__count"],
        )
        self.assertEqual(
            set(groups),
            {("2100", 2), ("0182", 1)},
        )

        form_view = self.bank_account_model.get_view(
            view_id=self.env.ref("base.view_partner_bank_form").id,
            view_type="form",
        )
        list_view = self.bank_account_model.get_view(
            view_id=self.env.ref("base.view_partner_bank_tree").id,
            view_type="list",
        )
        search_view = self.bank_account_model.get_view(
            view_id=self.env.ref("base.view_partner_bank_search").id,
            view_type="search",
        )
        self.assertIn('name="l10n_es_bank_code"', form_view["arch"])
        self.assertIn('name="l10n_es_bank_code"', list_view["arch"])
        self.assertIn('name="l10n_es_bank_code"', search_view["arch"])
        self.assertIn("group_by_l10n_es_bank_code", search_view["arch"])
