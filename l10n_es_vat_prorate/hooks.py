# Copyright 2024 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging


def pre_init_hook(cr):
    """Create computed columns if not exists when the module is installed"""
    logger = logging.getLogger(__name__)
    logger.info("Prepopulating stored related fields")
    cr.execute(
        """
        ALTER TABLE account_move
        ADD COLUMN IF NOT EXISTS prorate_id integer;
        """
    )
    cr.execute(
        """
        ALTER TABLE account_move
        ADD COLUMN IF NOT EXISTS with_special_vat_prorate BOOLEAN;
        """
    )
    cr.execute(
        """
        ALTER TABLE account_move_line
        ADD COLUMN IF NOT EXISTS with_vat_prorate BOOLEAN;
        """
    )
