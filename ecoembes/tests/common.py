# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase


class TestEcoembesBase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_system = cls.env["res.users"].create(
            {
                "name": "user_system",
                "login": "user_system",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("base.group_system").id,
                        ],
                    )
                ],
            }
        )
