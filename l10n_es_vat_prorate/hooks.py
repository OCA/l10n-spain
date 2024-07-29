# Copyright 2024 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging


def pre_init_hook(env):
    """Create computed columns if not exists when the module is installed"""
    logger = logging.getLogger(__name__)
    logger.info("Prepopulating stored related fields")
    env.cr.execute(
        """
        ALTER TABLE account_move
        ADD COLUMN IF NOT EXISTS prorate_id integer;
        """
    )
    env.cr.execute(
        """
        ALTER TABLE account_move
        ADD COLUMN IF NOT EXISTS with_special_vat_prorate BOOLEAN;
        """
    )
    env.cr.execute(
        """
        ALTER TABLE account_move_line
        ADD COLUMN IF NOT EXISTS with_vat_prorate BOOLEAN;
        """
    )
