# Copyright 2026 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def pre_init_hook(env):
    """Pre-create the deca_weight column to prevent the compute"""
    env.cr.execute(
        "ALTER TABLE stock_move ADD COLUMN IF NOT EXISTS deca_weight numeric"
    )
    env.cr.execute(
        "ALTER TABLE stock_picking ADD COLUMN IF NOT EXISTS deca_weight numeric"
    )
