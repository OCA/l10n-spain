# Copyright 2026 Tecnativa - Carlos Lopez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def pre_init_hook(env):
    """Pre-create the deca_weight column to prevent ORM compute on install."""
    env.cr.execute(
        "ALTER TABLE stock_move ADD COLUMN IF NOT EXISTS deca_weight numeric"
    )
    env.cr.execute(
        "ALTER TABLE stock_picking ADD COLUMN IF NOT EXISTS deca_weight numeric"
    )


def post_init_hook(env):
    """Compute deca_weight via SQL for existing stock moves and pickings."""
    env.flush_all()
    uom_kgm = env.ref("uom.product_uom_kgm")
    kgm_root = uom_kgm.parent_path.split("/")[0]
    precision = env["decimal.precision"].precision_get("Product Unit")
    weight_precision = env["decimal.precision"].precision_get("Stock Weight")

    env.cr.execute(
        """
        WITH move_qty AS (
            SELECT
                sm.id,
                pt.uom_id AS prod_uom_id,
                prod_uom.factor AS prod_uom_factor,
                prod_uom.parent_path AS prod_uom_parent_path,
                COALESCE(pp.weight, 0.0) AS product_weight,
                CASE
                    WHEN COALESCE(sm.quantity, 0.0) != 0.0 THEN
                        ROUND(
                            (
                                CASE
                                    WHEN sm.product_uom = pt.uom_id
                                    THEN sm.quantity
                                    ELSE sm.quantity * move_uom.factor / prod_uom.factor
                                END
                            )::numeric,
                            %(precision)s
                        )
                    ELSE COALESCE(sm.product_qty, 0.0)::numeric
                END AS product_qty
            FROM stock_move sm
            JOIN product_product pp ON pp.id = sm.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN uom_uom move_uom ON move_uom.id = sm.product_uom
            JOIN uom_uom prod_uom ON prod_uom.id = pt.uom_id
            WHERE sm.deca_weight IS NULL
        )
        UPDATE stock_move sm
        SET deca_weight = ROUND(
            (
                CASE
                    WHEN split_part(mq.prod_uom_parent_path, '/', 1) = %(kgm_root)s
                    THEN
                        CASE
                            WHEN mq.prod_uom_id = %(kgm_id)s
                            THEN mq.product_qty
                            ELSE mq.product_qty * mq.prod_uom_factor / %(kgm_factor)s
                        END
                    ELSE mq.product_qty * mq.product_weight
                END
            )::numeric,
            %(weight_precision)s
        )
        FROM move_qty mq
        WHERE sm.id = mq.id
        """,
        {
            "precision": precision,
            "weight_precision": weight_precision,
            "kgm_root": kgm_root,
            "kgm_id": uom_kgm.id,
            "kgm_factor": uom_kgm.factor,
        },
    )
    env.cr.execute(
        """
        UPDATE stock_picking sp
        SET deca_weight = COALESCE(sub.total_weight, 0.0)
        FROM (
            SELECT
                sp_inner.id AS picking_id,
                SUM(
                    CASE
                        WHEN sm.state != 'cancel'
                        THEN COALESCE(sm.deca_weight, 0.0)
                        ELSE 0.0
                    END
                ) AS total_weight
            FROM stock_picking sp_inner
            LEFT JOIN stock_move sm ON sm.picking_id = sp_inner.id
            WHERE sp_inner.deca_weight IS NULL
            GROUP BY sp_inner.id
        ) sub
        WHERE sp.id = sub.picking_id
        """
    )
    env.invalidate_all()
