# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """The taxes to prorate were a fixed list of chart templates that missed some
    deductible ones (7.5 %, 2 %, 5 % investment goods): mark the unmarked taxes
    that the tax type now selects. The marked ones are left as they are."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    taxes = (
        env["account.tax"]
        .with_context(active_test=False)
        .search(
            [
                ("company_id.with_vat_prorate", "=", True),
                ("with_vat_prorate", "=", False),
            ]
        )
    )
    taxes.filtered(lambda tax: tax._is_vat_prorate_tax())._compute_with_vat_prorate()
