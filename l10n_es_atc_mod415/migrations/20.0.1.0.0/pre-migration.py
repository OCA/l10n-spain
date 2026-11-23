# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from logging import getLogger

from odoo.tools.sql import SQL, _convert_column

_logger = getLogger(__name__)


def migrate(cr, version):
    """The flag becomes company dependent: each company keeps the value the
    partner had, as the 18.0 migration of l10n_es_aeat_mod347 does."""
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'res_partner' AND column_name = 'not_in_mod415'
        """
    )
    type_ = cr.fetchone()
    if not type_ or type_[0] == "jsonb":
        return
    _logger.info("Migrating 'not_in_mod415' column to company dependent")
    cr.execute("SELECT ARRAY_AGG(id) FROM res_company")
    company_ids = cr.fetchone()[0]
    args = ", ".join("%s, not_in_mod415" for _company_id in company_ids)
    _convert_column(
        cr,
        "res_partner",
        "not_in_mod415",
        "jsonb",
        SQL(f"jsonb_build_object({args})", *company_ids),
    )
