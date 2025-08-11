# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from logging import getLogger

from odoo.tools.sql import SQL, _convert_column

_logger = getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'res_partner' AND column_name = 'not_in_mod347'
    """)
    type_ = cr.fetchone()
    if type_ and type_[0] == "jsonb":
        # Already migrated in earlier versions
        return
    _logger.info("Migrating 'not_in_mod347' column to company dependent")
    cr.execute("SELECT ARRAY_AGG(id) FROM res_company")
    company_ids = cr.fetchone()[0]
    args = ", ".join("%s, not_in_mod347" for cid in company_ids)
    _convert_column(
        cr,
        "res_partner",
        "not_in_mod347",
        "jsonb",
        SQL(f"jsonb_build_object({args})", *company_ids),
    )
