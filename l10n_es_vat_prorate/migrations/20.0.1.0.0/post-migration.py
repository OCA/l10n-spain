# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

# Chart template taxes that were prorated up to 19.0 (``models/prorate_taxes.py``):
# they were marked on their own, so an unmarked one was unmarked by the user
PRORATE_TAXES_19 = {
    "p_iva4_bc",
    "p_iva4_bi",
    "p_iva4_ibc",
    "p_iva4_ibi",
    "p_iva4_ic_bc",
    "p_iva4_ic_bi",
    "p_iva4_isp",
    "p_iva4_isp_bi",
    "p_iva4_sc",
    "p_iva4_sp_ex",
    "p_iva4_sp_in",
    "p_iva5_bc",
    "p_iva5_ibc",
    "p_iva5_ic_bc",
    "p_iva5_ic_sc",
    "p_iva5_isc",
    "p_iva5_sc",
    "p_iva10_bc",
    "p_iva10_bi",
    "p_iva10_ibc",
    "p_iva10_ibi",
    "p_iva10_ic_bc",
    "p_iva10_ic_bi",
    "p_iva10_isp",
    "p_iva10_isp_bi",
    "p_iva10_sc",
    "p_iva10_sp_ex",
    "p_iva10_sp_in",
    "p_iva105_gan",
    "p_iva12_agr",
    "p_iva21_bc",
    "p_iva21_bi",
    "p_iva21_ibc",
    "p_iva21_ibi",
    "p_iva21_ic_bc",
    "p_iva21_ic_bi",
    "p_iva21_isp",
    "p_iva21_isp_bi",
    "p_iva21_sc",
    "p_iva21_sp_ex",
    "p_iva21_sp_in",
}


@openupgrade.migrate()
def migrate(env, version):
    """The taxes to prorate were a fixed list of chart template taxes that missed
    some deductible ones (7.5 %, 2 %, 5 % investment goods). Mark the unmarked taxes
    that the tax type now selects and were not in that list. The mark of the listed
    ones is kept as the user left it."""
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
    xmlids = taxes.get_external_id()
    new_taxes = taxes.filtered(
        lambda tax: (
            tax._is_vat_prorate_tax()
            and xmlids.get(tax.id, "").removeprefix(
                f"account.{tax.company_id.id}_account_tax_template_"
            )
            not in PRORATE_TAXES_19
        )
    )
    new_taxes.with_vat_prorate = True
