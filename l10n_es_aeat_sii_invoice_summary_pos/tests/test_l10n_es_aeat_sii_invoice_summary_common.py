# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo.fields import Command

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


class TestL10nEsAeatSiiSummaryCommon(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PosOrder = cls.env["pos.order"]
        cls.invoice.is_invoice_summary = True
        cls.invoice.sii_invoice_summary_start = True
        cls.invoice.sii_invoice_summary_end = True
        invoice_values = {
            "partner_id": cls.partner.id,
            "invoice_date": "2018-02-01",
            "move_type": "in_invoice",
            "is_invoice_summary": True,
            "sii_invoice_summary_start": 1,
            "sii_invoice_summary_end": 10,
        }
        cls.invoice_supplier_summary = cls.env["account.move"].create(invoice_values)
        invoice_values.update(
            {
                "ref": "REF-TEST",
                "invoice_date": "2025-04-15",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Test product",
                            "quantity": 1,
                            "price_unit": 100,
                            "product_id": cls.product.id,
                        }
                    )
                ],
            }
        )
        cls.invoice_summary = cls.env["account.move"].create(invoice_values)
        cls.pos_order_1 = cls.env.ref("point_of_sale.pos_closed_order_1_1")
        cls.pos_order_1.company_id = cls.env.company.id
        cls.pos_order_1.invoice_summary_id = False
        cls.pos_order_2 = cls.env.ref("point_of_sale.pos_closed_order_1_2")
        cls.pos_order_2.company_id = cls.env.company.id
        cls.pos_order_2.invoice_summary_id = False
        cls.date_order_today = datetime.now().date()
        cls.date_order_today_2_months = datetime.now().date() + relativedelta(months=2)
        cls.date_order_today_min_2_days = datetime.now().date() - relativedelta(days=2)
