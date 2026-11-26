# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class SpfeTestCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_es = cls.env.ref("base.es")
        cls.state_madrid = cls.env["res.country.state"].search(
            [("country_id", "=", cls.country_es.id)], limit=1
        )
        if not cls.state_madrid:
            cls.state_madrid = cls.env["res.country.state"].create(
                {
                    "name": "Madrid",
                    "code": "M",
                    "country_id": cls.country_es.id,
                }
            )
        cls.company = cls.env["res.company"].create(
            {
                "name": "Acysos SPFE Test S.L.",
                "vat": "ESB12345674",
                "street": "Calle Mayor 10",
                "city": "Madrid",
                "zip": "28001",
                "state_id": cls.state_madrid.id,
                "country_id": cls.country_es.id,
                "phone": "910000001",
                "email": "emisor@example.com",
                "website": "https://www.example.com",
                "currency_id": cls.env.ref("base.EUR").id,
            }
        )
        cls.env["account.chart.template"].try_loading(
            "es_pymes", company=cls.company, install_demo=False
        )
        cls.company.write(
            {
                "spfe_enabled": True,
                "spfe_test": True,
                "spfe_start_date": "2026-10-06",
                "spfe_company_legal_form": "R.M. Madrid, Tomo 100, Folio 20",
            }
        )
        cls.partner_es = cls.env["res.partner"].create(
            {
                "name": "Cliente B2B S.A.",
                "is_company": True,
                "vat": "ESA12345674",
                "street": "Avenida Diagonal 200",
                "city": "Madrid",
                "zip": "28020",
                "state_id": cls.state_madrid.id,
                "country_id": cls.country_es.id,
                "phone": "930000002",
                "email": "cliente@example.com",
            }
        )
        cls.company_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "ES4900496608132665031369",
                "partner_id": cls.company.partner_id.id,
                "company_id": cls.company.id,
            }
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        if not cls.uom_unit.unece_code:
            cls.uom_unit.unece_code = "C62"
        cls.product = cls.env["product.product"].create(
            {
                "name": "Servicio Consultoría SPFE",
                "uom_id": cls.uom_unit.id,
            }
        )
        cls.tax_iva21 = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type_tax_use", "=", "sale"),
                ("amount", "=", 21.0),
                ("spfe_is_surcharge", "=", False),
            ],
            limit=1,
        )
        cls.tax_req52 = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type_tax_use", "=", "sale"),
                ("amount", "=", 5.2),
            ],
            limit=1,
        )
        cls.tax_irpf15 = cls.env["account.tax"].search(
            [
                ("company_id", "=", cls.company.id),
                ("type_tax_use", "=", "sale"),
                ("amount", "=", -15.0),
            ],
            limit=1,
        )

    def _create_spfe_invoice(
        self,
        move_type="out_invoice",
        partner=None,
        invoice_date="2026-10-20",
        lines=None,
        **extra_vals,
    ):
        partner = partner or self.partner_es
        if lines is None:
            lines = [
                {
                    "product_id": self.product.id,
                    "name": "Consultoría técnica SPFE",
                    "quantity": 2.0,
                    "price_unit": 100.0,
                    "tax_ids": [Command.set(self.tax_iva21.ids)],
                }
            ]
        vals = {
            "company_id": self.company.id,
            "move_type": move_type,
            "partner_id": partner.id,
            "invoice_date": invoice_date,
            "invoice_date_due": "2026-11-20",
            "partner_bank_id": self.company_bank.id,
            "invoice_line_ids": [Command.create(ln) for ln in lines],
        }
        vals.update(extra_vals)
        return self.env["account.move"].with_company(self.company).create(vals)
