# Copyright 2021 Tecnativa - João Marques
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade
from psycopg2 import sql


def migrate_l10n_es_aeat_sii(env):
    """Migrate l10n.es.aeat.sii to l10n.es.aeat.certificate"""
    openupgrade.logged_query(
        env.cr,
        "ALTER TABLE l10n_es_aeat_certificate ADD COLUMN IF NOT EXISTS %s INT"
        % openupgrade.get_legacy_name("l10n_es_aeat_sii_id"),
    )
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """
        INSERT INTO l10n_es_aeat_certificate
        (name, state, date_start, date_end, folder,
         public_key, private_key, company_id, %s)
        SELECT
        name, state, date_start, date_end, 'OU',
        public_key, private_key, company_id, id
        FROM l10n_es_aeat_sii
        """
            % openupgrade.get_legacy_name("l10n_es_aeat_sii_id")
        ),
    )
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE ir_attachment ia
            SET res_model = 'l10n.es.aeat.certificate',
                res_id = leac.{field_name}
            FROM l10n_es_aeat_certificate leac
            WHERE ia.res_model = 'l10n.es.aeat.sii' AND leac.{field_name} = ia.res_id
        """.format(
            field_name=openupgrade.get_legacy_name("l10n_es_aeat_sii_id")
        ),
    )


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.table_exists(env.cr, "l10n_es_aeat_sii"):
        migrate_l10n_es_aeat_sii(env)
