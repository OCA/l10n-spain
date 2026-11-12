# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestL10nEsBank(BaseCommon):
    _test_user_groups = ("base.group_user", "base.group_partner_manager")

    def _new_account_form(self):
        # As opened from the bank accounts of the partner
        return Form(
            self.env["res.partner.bank"].with_context(
                default_partner_id=self.partner.id
            )
        )

    def _create_account(self, account_number):
        with self._new_account_form() as account_form:
            account_form.account_number = account_number
        return account_form.record

    def test_entity_code_from_spanish_iban(self):
        with self._new_account_form() as account_form:
            account_form.account_number = "ES91 2100 0418 4502 0005 1332"
            self.assertEqual(account_form.l10n_es_bank_code, "2100")
        account = account_form.record
        self.assertEqual(account.l10n_es_bank_code, "2100")
        # Distinct numbers once normalized: with account installed the number is
        # stored formatted, and a partner cannot have the same account twice
        for account_number, code in (
            ("es9101820000000000000000", "0182"),
            ("_ES7921000813610123456789", "2100"),
        ):
            self.assertEqual(
                self._create_account(account_number).l10n_es_bank_code,
                code,
                account_number,
            )

    def test_entity_code_follows_the_account_number(self):
        account = self._create_account("ES9121000418450200051332")
        account.bank_name = "Manual bank name"
        for account_number, code in (
            ("DE89370400440532013000", False),
            ("ES9121000418450200051333", False),
            ("12345678", False),
            ("ES9101820000000000000000", "0182"),
        ):
            with Form(account) as account_form:
                account_form.account_number = account_number
            self.assertEqual(account.l10n_es_bank_code, code, account_number)
        self.assertEqual(account.bank_name, "Manual bank name")

    def test_search_and_group_by_entity_code(self):
        accounts = (
            self._create_account("ES9121000418450200051332")
            | self._create_account("ES9101820000000000000000")
            | self._create_account("DE89370400440532013000")
        )
        domain = [("id", "in", accounts.ids)]
        self.assertEqual(
            self.env["res.partner.bank"].search(
                domain + [("l10n_es_bank_code", "=", "0182")]
            ),
            accounts[1],
        )
        self.assertEqual(
            dict(
                self.env["res.partner.bank"].read_group(
                    domain, ["l10n_es_bank_code"], ["__count"]
                )
            ),
            {"2100": 1, "0182": 1, False: 1},
        )

    def test_search_view_groups_by_entity_code(self):
        arch = self.env["res.partner.bank"].get_views([(False, "search")])["views"][
            "search"
        ]["arch"]
        # The web client reads a filter with child filters as a parent filter
        # whose options need a domain, so group by filters go in a group
        self.assertTrue(
            etree.fromstring(arch).xpath(
                "//search/group/filter[@name='groupby_l10n_es_bank_code']"
            )
        )
