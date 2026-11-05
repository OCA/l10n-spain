# Copyright 2026 Tecnativa - Carlos Lopez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Initialize existing weights through the Odoo 18 UoM-aware ORM computes."""
    for model_name in ("stock.move", "stock.picking"):
        model = env[model_name]
        last_id = 0
        while records := model.search([("id", ">", last_id)], limit=1000, order="id"):
            env.add_to_compute(model._fields["deca_weight"], records)
            records._recompute_recordset(["deca_weight"])
            records.flush_recordset(["deca_weight"])
            last_id = records[-1].id
