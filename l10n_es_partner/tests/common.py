# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class L10nEsPartnerCommon(BaseCommon):
    _test_user_groups = ("base.group_user",)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spain = cls.env.ref("base.es")
        cls.admin = cls.env.ref("base.user_admin")
        cls.env["ir.config_parameter"].sudo().set_str(
            "l10n_es_partner.name_pattern", ""
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Empresa de prueba",
                "comercial": "Nombre comercial",
                "vat": "ES12345678Z",
                "country_id": cls.spain.id,
            }
        )
