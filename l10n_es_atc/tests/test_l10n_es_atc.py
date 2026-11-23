# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError

from odoo.addons.base.tests.common import BaseCommon


class TestL10nEsAtc(BaseCommon):
    """The module is the glue every ATC declaration sits on: it adds the ATC
    menu, the public way of the company and the helpers that turn Odoo data
    into what the ATC files expect. The province codes, the amounts in cents and
    the generation of a declaration file are covered by the tests of
    l10n_es_atc_mod417, mod420 and mod425, on the files they produce.
    """

    _test_user_groups = (
        "base.group_user",
        "account.group_account_manager",
        "l10n_es_aeat.group_account_aeat",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.atc_report = cls.env["l10n.es.atc.report"]
        cls.atc_menu = cls.env.ref("l10n_es_atc.menu_root_atc")
        cls.aeat_group = cls.env.ref("l10n_es_aeat.group_account_aeat")

    def test_atc_menu_is_shown_only_to_the_aeat_group(self):
        """The ATC entry hangs under the AEAT one and is reserved to its group:
        the people who file the declarations with the tax administrations.

        It carries no action of its own: the web client shows it once a
        declaration module hangs a menu with an action under it, as this test
        does, and only to the users of the AEAT group.
        """
        self.assertEqual(
            self.atc_menu.parent_id, self.env.ref("l10n_es_aeat.menu_root_aeat")
        )
        declaration_action = (
            self.env["ir.actions.act_window"]
            .sudo()
            .create({"name": "ATC declarations", "res_model": "res.partner"})
        )
        self.env["ir.ui.menu"].sudo().create(
            {
                "name": "ATC declaration",
                "parent_id": self.atc_menu.id,
                "action": f"ir.actions.act_window,{declaration_action.id}",
            }
        )
        other_accountant = self._test_user.sudo().copy(
            {"login": "accountant-without-aeat"}
        )
        other_accountant.group_ids -= self.aeat_group
        Menu = self.env["ir.ui.menu"]
        self.assertIn(
            self.atc_menu.id, Menu.with_user(self._test_user).load_menus(False)
        )
        self.assertNotIn(
            self.atc_menu.id, Menu.with_user(other_accountant).load_menus(False)
        )

    def test_aeat_group_is_named_for_both_administrations(self):
        """The group that files the AEAT declarations files the ATC ones too, so
        the user form names it after both administrations."""
        self.assertEqual(self.aeat_group.name, "AEAT/ATC manager")
        self.assertEqual(self.aeat_group.privilege_id.name, "AEAT/ATC Permissions")

    def test_company_public_way_is_filled_on_the_aeat_page(self):
        """The public way is the ATC field of the company, next to its AEAT data."""
        arch = self.env["res.company"].get_view(view_type="form")["arch"]
        self.assertIn('name="atc_public_way"', arch)

    def test_a_state_outside_the_mapping_is_refused(self):
        """A company in a state the ATC does not know stops the declaration."""
        foreign_state = (
            self.env["res.country.state"]
            .sudo()
            .create(
                {
                    "name": "Test state",
                    "code": "ZZ",
                    "country_id": self.env.ref("base.fr").id,
                }
            )
        )
        with self.assertRaisesRegex(UserError, "state code is not mapped"):
            self.atc_report._atc_get_country_state_code(foreign_state)
