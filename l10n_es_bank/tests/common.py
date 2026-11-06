# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.addons.base.tests.common import BaseCommon


class L10nEsBankCommon(BaseCommon):
    _test_user_groups = ("base.group_user", "base.group_partner_manager")

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Bank test partner"})
