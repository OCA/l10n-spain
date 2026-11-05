# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)
LEGACY_IDENTIFIERS = {
    "03": "ES_PASSPORT",
    "05": "ES_RES_CERT",
    "06": "ES_OTHER_ID",
}


def _log_unresolved_identifiers(cr) -> None:
    openupgrade.logged_query(
        cr,
        """
        SELECT id,
               CASE
                   WHEN NULLIF(BTRIM(aeat_identification_type), '') IS NULL
                     OR NULLIF(BTRIM(aeat_identification), '') IS NULL
                       THEN 'incomplete legacy fields'
                   WHEN aeat_identification_type NOT IN ('03', '05', '06')
                       THEN 'unsupported legacy type'
                   ELSE 'different native value already exists'
               END AS reason
          FROM res_partner
         WHERE (
                   NULLIF(BTRIM(aeat_identification_type), '') IS NOT NULL
                OR NULLIF(BTRIM(aeat_identification), '') IS NOT NULL
               )
           AND (
                   NULLIF(BTRIM(aeat_identification_type), '') IS NULL
                OR NULLIF(BTRIM(aeat_identification), '') IS NULL
                OR aeat_identification_type NOT IN ('03', '05', '06')
                OR (
                       aeat_identification_type = '03'
                   AND NULLIF(
                           BTRIM(additional_identifiers ->> 'ES_PASSPORT'), ''
                       ) IS NOT NULL
                   AND additional_identifiers ->> 'ES_PASSPORT'
                       IS DISTINCT FROM aeat_identification
                   )
                OR (
                       aeat_identification_type = '05'
                   AND NULLIF(
                           BTRIM(additional_identifiers ->> 'ES_RES_CERT'), ''
                       ) IS NOT NULL
                   AND additional_identifiers ->> 'ES_RES_CERT'
                       IS DISTINCT FROM aeat_identification
                   )
                OR (
                       aeat_identification_type = '06'
                   AND NULLIF(
                           BTRIM(additional_identifiers ->> 'ES_OTHER_ID'), ''
                       ) IS NOT NULL
                   AND additional_identifiers ->> 'ES_OTHER_ID'
                       IS DISTINCT FROM aeat_identification
                   )
               )
        """,
    )
    for partner_id, reason in cr.fetchall():
        _logger.warning(
            "AEAT identifier migration needs reconciliation for partner %s: %s",
            partner_id,
            reason,
        )


@openupgrade.migrate()
def migrate(env, version) -> None:
    for legacy_type, native_key in LEGACY_IDENTIFIERS.items():
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE res_partner
               SET additional_identifiers =
                       COALESCE(additional_identifiers, '{}'::jsonb)
                       || jsonb_build_object(%s, aeat_identification)
             WHERE aeat_identification_type = %s
               AND NULLIF(BTRIM(aeat_identification), '') IS NOT NULL
               AND NULLIF(BTRIM(additional_identifiers ->> %s), '') IS NULL
            """,
            (native_key, legacy_type, native_key),
        )

    _log_unresolved_identifiers(env.cr)
