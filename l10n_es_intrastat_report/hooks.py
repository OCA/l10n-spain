# Copyright 2020 ACSONE SA/NV
# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Set the intrastat field of the private fiscal position records.
    This is necessary for the intrastat report generation
    """
    b2b_items = env["ir.model.data"].search(
        [
            ("model", "=", "account.fiscal.position"),
            ("name", "like", "%_fp_intra"),
            ("module", "=", "account"),
        ]
    )
    b2c_items = env["ir.model.data"].search(
        [
            ("model", "=", "account.fiscal.position"),
            ("name", "like", "%_fp_intra_private"),
            ("module", "=", "account"),
        ]
    )
    # Avoid modifying fiscal positions created with accounting plans other than l10n_es
    env["account.fiscal.position"].search(
        [
            ("id", "in", b2b_items.mapped("res_id")),
            ("company_id.chart_template", "like", "es_%"),
        ]
    ).write({"intrastat": "b2b", "vat_required": True})
    env["account.fiscal.position"].search(
        [
            ("id", "in", b2c_items.mapped("res_id")),
            ("company_id.chart_template", "like", "es_%"),
        ]
    ).write({"intrastat": "b2c", "vat_required": False})
