# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEcoembesBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ecoembes_manager = new_test_user(
            cls.env,
            login="ecoembes_manager",
            groups="base.group_user,account.group_account_invoice,"
            "ecoembes.group_ecoembes_manager",
        )
        cls.user_system = new_test_user(
            cls.env,
            login="user_system",
            groups="base.group_user,base.group_system",
        )
